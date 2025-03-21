# Copyright (c) 2022, 2023 Humanitarian OpenStreetMap Team
#
# This file is part of FMTM.
#
#     FMTM is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     FMTM is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with FMTM.  If not, see <https:#www.gnu.org/licenses/>.
#

import os
import zipfile
import concurrent.futures
import logging
import threading
import csv
import io
import os
import zipfile
import json
from datetime import datetime
import logging
from fastapi import HTTPException, Response
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from ..central.central_crud import get_odk_form, get_odk_project
from ..tasks import tasks_crud
from ..projects import project_crud, project_schemas
from osm_fieldwork.json2osm import JsonDump
from pathlib import Path
from fastapi.logger import logger as logger


def get_submission_of_project(db: Session, project_id: int, task_id: int = None):
    """
    Gets the submission of project.

    Args:
        db (Session): A database session.
        project_id (int): The ID of the project.
        task_id (int, optional): The ID of the task. If provided, only submissions for this task are returned. Defaults to None.

    Returns:
        list: A list of submissions for the specified project and task (if provided).
    """
    project_info = project_crud.get_project(db, project_id)

    # Return empty list if project is not found
    if not project_info:
        return []

    odkid = project_info.odkid
    project_name = project_info.project_name_prefix
    form_category = project_info.xform_title
    project_tasks = project_info.tasks

    if not (
        project_info.odk_central_url
        or project_info.odk_central_user
        or project_info.odk_central_password
    ):
        raise HTTPException(
            status_code=404, detail="ODK Central Credentials not found in project"
        )

    # ODK Credentials
    odk_credentials = project_schemas.ODKCentral(
        odk_central_url=project_info.odk_central_url,
        odk_central_user=project_info.odk_central_user,
        odk_central_password=project_info.odk_central_password,
    )

    xform = get_odk_form(odk_credentials)

    # If task id is not provided, submission for all the task are listed
    if task_id is None:
        task_list = []

        task_list = [x.id for x in project_tasks]

        data = []

        for id in task_list:

            # XML Form Id is a combination or project_name, category and task_id
            xml_form_id = f"{project_name}_{form_category}_{id}".split("_")[2]
            submission_list = xform.listSubmissions(odkid, xml_form_id)

            # data.append(submission_list)
            if isinstance(submission_list, list):
                for submission in submission_list:
                    data.append(submission)
        return data

    else:
        # If task_id is provided, submission made to this particular task is returned.
        xml_form_id = f"{project_name}_{form_category}_{task_id}".split("_")[2]
        submission_list = xform.listSubmissionBasicInfo(odkid, xml_form_id)
        for x in submission_list:
            x["submitted_by"] = f"{project_name}_{form_category}_{task_id}"
        return submission_list


def get_forms_of_project(db: Session, project_id: int):
    """
    Gets the forms of a project.

    Args:
        db (Session): A database session.
        project_id (int): The ID of the project.

    Returns:
        list: A list of forms for the specified project.
    """
    project_info = project_crud.get_project_by_id(db, project_id)

    # Return empty list if project is not found
    if not project_info:
        return []

    odkid = project_info.odkid
    project = get_odk_project()

    result = project.listForms(odkid)
    return result


def list_app_users_or_project(db: Session, project_id: int):
    """
    Lists the app users of a project.

    Args:
        db (Session): A database session.
        project_id (int): The ID of the project.

    Returns:
        list: A list of app users for the specified project.
    """
    project_info = project_crud.get_project_by_id(db, project_id)

    # Return empty list if project is not found
    if not project_info:
        return []

    odkid = project_info.odkid
    project = get_odk_project()
    result = project.listAppUsers(odkid)
    return result


def create_zip_file(files, output_file_path):
    """
    Creates a zip file containing the specified files.

    Args:
        files (list): A list of file paths to include in the zip file.
        output_file_path (str): The path to save the zip file to.

    Returns:
        str: The path to the created zip file.
    """
    with zipfile.ZipFile(output_file_path, mode="w") as zip_file:
        for file_path in files:
            zip_file.write(file_path)
    return output_file_path


async def convert_json_to_osm_xml(file_path):
    """
    Converts a JSON file to an OSM XML file.

    Args:
        file_path (str): The path to the JSON file to be converted.

    Returns:
        str: The path to the created OSM XML file.
    """

    jsonin = JsonDump()
    infile = Path(file_path)

    base = os.path.splitext(infile.name)[0]

    osmoutfile = f"/tmp/{base}.osm"
    jsonin.createOSM(osmoutfile)

    data = jsonin.parse(infile.as_posix())

    for entry in data:
        feature = jsonin.createEntry(entry)
        # Sometimes bad entries, usually from debugging XForm design, sneak in
        if len(feature) == 0:
            continue
        if len(feature) > 0:
            if "lat" not in feature["attrs"]:
                if 'geometry' in feature['tags']:
                    if type(feature['tags']['geometry']) == str:
                        coords = list(feature['tags']['geometry'])
                    else:
                        coords = feature['tags']['geometry']['coordinates']
                    feature['attrs'] = {'lat': coords[1], 'lon': coords[0]}
                else:
                    logger.warning("Bad record! %r" % feature)
                    continue
            jsonin.writeOSM(feature)

    jsonin.finishOSM()
    logger.info("Wrote OSM XML file: %r" % osmoutfile)
    return osmoutfile


async def convert_json_to_osm(file_path):
    """
    Converts a JSON file to an OSM XML file and a GeoJSON file.

    Args:
        file_path (str): The path to the JSON file to be converted.

    Returns:
        Tuple[str, str]: A tuple containing the paths to the created OSM XML and GeoJSON files.
    """

    jsonin = JsonDump()
    infile = Path(file_path)

    base = os.path.splitext(infile.name)[0]

    osmoutfile = f"/tmp/{base}.osm"
    jsonin.createOSM(osmoutfile)

    jsonoutfile = f"/tmp/{base}.geojson"
    jsonin.createGeoJson(jsonoutfile)

    data = jsonin.parse(infile.as_posix())

    for entry in data:
        feature = jsonin.createEntry(entry)
        # Sometimes bad entries, usually from debugging XForm design, sneak in
        if len(feature) == 0:
            continue
        if len(feature) > 0:
            if "lat" not in feature["attrs"]:
                if 'geometry' in feature['tags']:
                    if type(feature['tags']['geometry']) == str:
                        coords = list(feature['tags']['geometry'])
                        # del feature['tags']['geometry']
                    else:
                        coords = feature['tags']['geometry']['coordinates']
                        # del feature['tags']['geometry']
                    feature['attrs'] = {'lat': coords[1], 'lon': coords[0]}
                else:
                    logger.warning("Bad record! %r" % feature)
                    continue
            jsonin.writeOSM(feature)
            jsonin.writeGeoJson(feature)

    jsonin.finishOSM()
    jsonin.finishGeoJson()
    logger.info("Wrote OSM XML file: %r" % osmoutfile)
    logger.info("Wrote GeoJson file: %r" % jsonoutfile)
    return osmoutfile, jsonoutfile


async def convert_to_osm_for_task(odk_id: int, form_id: int, xform: any):
    """
    Converts submission data from ODK Central to OSM XML and GeoJSON files.

    Args:
        odk_id (int): The ID of the ODK project.
        form_id (int): The ID of the ODK form.
        xform (any): An instance of an ODK form object.

    Returns:
        Tuple[str, str]: A tuple containing the paths to the created OSM XML and GeoJSON files.
    """

    # This file stores the submission data.
    file_path = f"/tmp/{odk_id}_{form_id}.json"

    # Get the submission data from ODK Central
    file = xform.getSubmissions(odk_id, form_id, None, False, True)

    if file is None:
        return None, None

    with open(file_path, "wb") as f:
        f.write(file)

    osmoutfile, jsonoutfile = await convert_json_to_osm(file_path)
    return osmoutfile, jsonoutfile


async def convert_to_osm(db: Session, project_id: int, task_id: int):
    """
    Converts submission data from a project to OSM XML and GeoJSON files and returns a ZIP file containing the converted files.

    Args:
        db (Session): A database session.
        project_id (int): The ID of the project.
        task_id (int): The ID of the task.

    Returns:
        FileResponse: A FileResponse object containing the ZIP file with the converted OSM XML and GeoJSON files.
    """

    project_info = project_crud.get_project(db, project_id)

    # Return exception if project is not found
    if not project_info:
        raise HTTPException(status_code=404, detail="Project not found")

    odkid = project_info.odkid
    project_name = project_info.project_name_prefix
    form_category = project_info.xform_title

    # ODK Credentials
    odk_credentials = project_schemas.ODKCentral(
        odk_central_url=project_info.odk_central_url,
        odk_central_user=project_info.odk_central_user,
        odk_central_password=project_info.odk_central_password,
    )

    # Get ODK Form with odk credentials from the project.
    xform = get_odk_form(odk_credentials)

    # Create a new ZIP file for the extracted files
    final_zip_file_path = f"/tmp/{project_name}_{form_category}_osm.zip"

    # Remove the ZIP file if it already exists
    if os.path.exists(final_zip_file_path):
        os.remove(final_zip_file_path)

    # Submission JSON
    if task_id:
        submission = xform.getSubmissions(odkid, task_id, None, False, True)
        submission = (json.loads(submission))['value']
    else:
        submission = await get_all_submissions(db, project_id)

    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    # JSON FILE PATH
    jsoninfile = "/tmp/json_infile.json"

    # Write the submission to a file
    with open(jsoninfile, 'w') as f:
        f.write(json.dumps(submission))

    # Convert the submission to osm xml format
    osmoutfile, jsonoutfile = await convert_json_to_osm(jsoninfile)

    if osmoutfile and jsonoutfile:

        #FIXME: Need to fix this when generating osm file

        # Remove the extra closing </osm> tag from the end of the file
        with open(osmoutfile, 'r') as f:
            osmoutfile_data = f.read()
            # Find the last index of the closing </osm> tag
            last_osm_index = osmoutfile_data.rfind('</osm>')
            # Remove the extra closing </osm> tag from the end
            processed_xml_string = osmoutfile_data[:last_osm_index] + osmoutfile_data[last_osm_index + len('</osm>'):]

        # Write the modified XML data back to the file
        with open(osmoutfile, 'w') as f:
            f.write(processed_xml_string)


        # Add the files to the ZIP file
        with zipfile.ZipFile(final_zip_file_path, mode="a") as final_zip_file:
            final_zip_file.write(osmoutfile)
            final_zip_file.write(jsonoutfile)

    return FileResponse(final_zip_file_path)



def download_submission_for_project(db, project_id):
    """
    Downloads submission data for a project.

    Args:
        db (Session): A database session.
        project_id (int): The ID of the project.

    Returns:
        None
    """
    print('Download submission for a project')

    project_info = project_crud.get_project(db, project_id)

    # Return empty list if project is not found
    if not project_info:
        raise HTTPException(status_code=404, detail="Project not found")

    odkid = project_info.odkid
    project_name = project_info.project_name_prefix
    form_category = project_info.xform_title
    project_tasks = project_info.tasks

    # ODK Credentials
    odk_credentials = project_schemas.ODKCentral(
        odk_central_url=project_info.odk_central_url,
        odk_central_user=project_info.odk_central_user,
        odk_central_password=project_info.odk_central_password,
    )

    # Get ODK Form with odk credentials from the project.
    xform = get_odk_form(odk_credentials)

    def download_submission_for_task(task_id):
        """
        Downloads submission data for a task.

        Args:
            task_id (int): The ID of the task.

        Returns:
            str: The path to the downloaded ZIP file containing the submission data.
        """

        logging.info(f"Thread {threading.current_thread().name} - Downloading submission for Task ID {task_id}")
        xml_form_id = f"{project_name}_{form_category}_{task_id}".split("_")[2]
        file = xform.getSubmissionMedia(odkid, xml_form_id)
        file_path = f"{project_name}_{form_category}_submission_{task_id}.zip"
        with open(file_path, "wb") as f:
            f.write(file.content)
        return file_path

    def extract_files(zip_file_path):
        """
        Extracts files from a ZIP file.

        Args:
            zip_file_path (str): The path to the ZIP file to extract files from.

        Returns:
            List[str]: A list of paths to the extracted files.
        """
        logging.info(f"Thread {threading.current_thread().name} - Extracting files from {zip_file_path}")
        with zipfile.ZipFile(zip_file_path, "r") as zip_file:
            extract_dir = os.path.splitext(zip_file_path)[0]
            zip_file.extractall(extract_dir)
            return [os.path.join(extract_dir, f) for f in zip_file.namelist()]

    # Set up logging configuration
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(threadName)s] %(message)s")

    with concurrent.futures.ThreadPoolExecutor() as executor:
        task_list = [x.id for x in project_tasks]

        # Download submissions using thread pool
        futures = {executor.submit(download_submission_for_task, task_id): task_id for task_id in task_list}

        files = []
        for future in concurrent.futures.as_completed(futures):
            task_id = futures[future]
            try:
                file_path = future.result()
                files.append(file_path)
                logging.info(f"Thread {threading.current_thread().name} - Task {task_id} - Download completed.")
            except Exception as e:
                logging.error(f"Thread {threading.current_thread().name} - Error occurred while downloading submission for task {task_id}: {e}")

        # Extract files using thread pool
        extracted_files = []
        futures = {executor.submit(extract_files, file_path): file_path for file_path in files}
        for future in concurrent.futures.as_completed(futures):
            file_path = futures[future]
            try:
                extracted_files.extend(future.result())
                logging.info(f"Thread {threading.current_thread().name} - Extracted files from {file_path}")
            except Exception as e:
                logging.error(f"Thread {threading.current_thread().name} - Error occurred while extracting files from {file_path}: {e}")

    # Create a new ZIP file for the extracted files
    final_zip_file_path = f"{project_name}_{form_category}_submissions_final.zip"
    with zipfile.ZipFile(final_zip_file_path, mode="w") as final_zip_file:
        for file_path in extracted_files:
            final_zip_file.write(file_path)

    return final_zip_file_path


def get_all_submissions(db: Session, project_id):
    """
    Gets all submissions for a project.

    Args:
        db (Session): A database session.
        project_id (int): The ID of the project.

    Returns:
        Any: The submission data for the specified project.
    """
    project_info = project_crud.get_project(db, project_id)

    # ODK Credentials
    odk_credentials = project_schemas.ODKCentral(
        odk_central_url=project_info.odk_central_url,
        odk_central_user=project_info.odk_central_user,
        odk_central_password=project_info.odk_central_password,
    )

    project = get_odk_project(odk_credentials)

    task_lists = tasks_crud.get_task_lists(db, project_id)
    submissions = project.getAllSubmissions(project_info.odkid, task_lists)
    return submissions


def get_project_submission(db: Session, project_id: int):
    """
    Gets submission data for a project.

    Args:
        db (Session): A database session.
        project_id (int): The ID of the project.

    Returns:
        Any: The submission data for the specified project.
    """
    project_info = project_crud.get_project(db, project_id)

    # Return empty list if project is not found
    if not project_info:
        raise HTTPException(status_code=404, detail="Project not found")

    odkid = project_info.odkid
    project_name = project_info.project_name_prefix
    form_category = project_info.xform_title
    project_tasks = project_info.tasks

    # ODK Credentials
    odk_credentials = project_schemas.ODKCentral(
        odk_central_url=project_info.odk_central_url,
        odk_central_user=project_info.odk_central_user,
        odk_central_password=project_info.odk_central_password,
    )

    # Get ODK Form with odk credentials from the project.
    xform = get_odk_form(odk_credentials)

    submissions = []

    task_list = [x.id for x in project_tasks]
    for id in task_list:
        xml_form_id = f"{project_name}_{form_category}_{id}".split("_")[
            2]
        file = xform.getSubmissions(
            odkid, xml_form_id, None, False, True)
        if not file:
            json_data = None
        else:
            json_data = json.loads(file)
            json_data_value = json_data.get('value')
            if json_data_value:
                submissions.extend(json_data_value)

    return submissions


def download_submission(db: Session, project_id: int, task_id: int, export_json: bool):
    """
    Downloads submission data for a project.

    Args:
        db (Session): A database session.
        project_id (int): The ID of the project.
        task_id (int): The ID of the task. If not provided, submission data for all tasks in the project are downloaded.
        export_json (bool): If True, the submission data is exported as a JSON file. If False, the submission data is exported as a ZIP file.

    Returns:
        Union[FileResponse, Response]: A FileResponse object containing the downloaded submission data as a ZIP or JSON file.
    """

    project_info = project_crud.get_project(db, project_id)

    # Return empty list if project is not found
    if not project_info:
        raise HTTPException(status_code=404, detail="Project not found")

    odkid = project_info.odkid
    project_name = project_info.project_name_prefix
    form_category = project_info.xform_title
    project_tasks = project_info.tasks

    # ODK Credentials
    odk_credentials = project_schemas.ODKCentral(
        odk_central_url=project_info.odk_central_url,
        odk_central_user=project_info.odk_central_user,
        odk_central_password=project_info.odk_central_password,
    )

    # Get ODK Form with odk credentials from the project.
    xform = get_odk_form(odk_credentials)
    if not export_json:
        file_path = f"{project_id}_submissions.zip"

        # If task id is not provided, submission for all the task are listed
        if task_id is None:
            task_list = []

            task_list = [x.id for x in project_tasks]

            # zip_file_path = f"{project_name}_{form_category}_submissions.zip"  # Create a new ZIP file for all submissions
            files = []

            for id in task_list:

                # XML Form Id is a combination or project_name, category and task_id
                # FIXME: fix xml_form_id
                xml_form_id = f"{project_name}_{form_category}_{id}".split("_")[
                    2]
                file = xform.getSubmissionMedia(odkid, xml_form_id)

                # Create a new output file for each submission
                file_path = f"{project_name}_{form_category}_submission_{id}.zip"
                with open(file_path, "wb") as f:
                    f.write(file.content)

                files.append(
                    file_path
                )  # Add the output file path to the list of files for the final ZIP file

            extracted_files = []
            for file_path in files:
                with zipfile.ZipFile(file_path, "r") as zip_file:
                    zip_file.extractall(
                        os.path.splitext(file_path)[0]
                    )  # Extract the contents of the nested ZIP files to a directory with the same name as the ZIP file
                    extracted_files += [
                        os.path.join(os.path.splitext(file_path)[0], f)
                        for f in zip_file.namelist()
                    ]  # Add the extracted file paths to the list of extracted files

            # Create a new ZIP file for the extracted files
            final_zip_file_path = f"{project_name}_{form_category}_submissions_final.zip"
            with zipfile.ZipFile(final_zip_file_path, mode="w") as final_zip_file:
                for file_path in extracted_files:
                    final_zip_file.write(file_path)

            return FileResponse(final_zip_file_path)
        else:
            xml_form_id = f"{project_name}_{form_category}_{task_id}".split("_")[
                2]
            file = xform.getSubmissionMedia(odkid, xml_form_id)
            with open(file_path, "wb") as f:
                f.write(file.content)
            return FileResponse(file_path)
    else:
        headers = {
            "Content-Disposition": "attachment; filename=submission_data.json",
            "Content-Type": "application/json",
        }

        files = []

        if task_id is None:
            task_list = [x.id for x in project_tasks]
            for id in task_list:
                xml_form_id = f"{project_name}_{form_category}_{id}".split("_")[
                    2]
                file = xform.getSubmissions(
                    odkid, xml_form_id, None, False, True)
                if not file:
                    json_data = None
                else:
                    json_data = json.loads(file)
                    json_data_value = json_data.get('value')
                    if json_data_value:
                        files.extend(json_data_value)
        else:
            xml_form_id = f"{project_name}_{form_category}_{task_id}".split("_")[
                2]
            file = xform.getSubmissions(odkid, xml_form_id, None, False, True)
            json_data = json.loads(file)

        response_content = json.dumps(
            files if task_id is None else json_data, indent=4).encode()

        return Response(content=response_content, headers=headers)


def get_submission_points(db: Session, project_id: int, task_id: int = None):
    """
    Gets the submission points of a project.

    Args:
        db (Session): A database session.
        project_id (int): The ID of the project.
        task_id (int, optional): The ID of the task. If provided, only submission points for this task are returned. Defaults to None.

    Returns:
        Union[List[Dict[str, Any]], None]: A list of GeoJSON Feature objects representing the submission points for the specified project and task (if provided), or None if an error occurred.
    """
    project_info = project_crud.get_project_by_id(db, project_id)

    # Return empty list if project is not found
    if not project_info:
        raise HTTPException(status_code=404, detail="Project not found")

    odkid = project_info.odkid
    project_name = project_info.project_name_prefix
    form_category = project_info.xform_title

    # ODK Credentials
    odk_credentials = project_schemas.ODKCentral(
        odk_central_url=project_info.odk_central_url,
        odk_central_user=project_info.odk_central_user,
        odk_central_password=project_info.odk_central_password,
    )

    xform = get_odk_form(odk_credentials)

    if task_id:
        xml_form_id = f"{project_name}_{form_category}_{task_id}".split("_")[
            2
        ]  # FIXME: fix xml_form_id
        # file_path = f"{project_id}_submissions.zip"
        response_file = xform.getSubmissionMedia(odkid, xml_form_id)

        # Create a file-like object from the bytes object
        response_file_obj = io.BytesIO(response_file.content)
        try:
            # Open the zipfile
            with zipfile.ZipFile(response_file_obj, "r") as zip_ref:
                # Find the CSV file in the zipfile (assuming it has a .csv extension)
                csv_filename = [
                    f for f in zip_ref.namelist() if f.endswith(".csv")][0]
                # Open the CSV file
                with zip_ref.open(csv_filename) as csv_file:
                    # Read the CSV data
                    csv_reader = csv.DictReader(io.TextIOWrapper(csv_file))
                    geometry = []
                    for row in csv_reader:
                        # Check if the row contains the 'warmup-Latitude' and 'warmup-Longitude' columns
                        # FIXME: fix the column names (they might not be same warmup-Latitude and warmup-Longitude)
                        if "warmup-Latitude" in row and "warmup-Longitude" in row:
                            point = (row["warmup-Latitude"],
                                     row["warmup-Longitude"])

                            # Create a GeoJSON Feature object
                            geometry.append(
                                {
                                    "type": "Feature",
                                    "geometry": {"type": "Point", "coordinates": point},
                                }
                            )
                            # points.append(point)
                return geometry
        except zipfile.BadZipFile:
            print("The file is not a valid zip file.")
            return None
    else:
        return None


async def get_submission_count_of_a_project(db:Session, 
                                      project_id: int):
    """
    Gets the submission count for a project.

    Args:
        db (Session): A database session.
        project_id (int): The ID of the project.

    Returns:
        int: The submission count for the specified project.
    """

    project_info = project_crud.get_project(db, project_id)

    # Return empty list if project is not found
    if not project_info:
        raise HTTPException(status_code=404, detail="Project not found")

    odkid = project_info.odkid
    project_name = project_info.project_name_prefix
    form_category = project_info.xform_title
    project_tasks = project_info.tasks

    # ODK Credentials
    odk_credentials = project_schemas.ODKCentral(
        odk_central_url=project_info.odk_central_url,
        odk_central_user=project_info.odk_central_user,
        odk_central_password=project_info.odk_central_password,
    )

    # Get ODK Form with odk credentials from the project.
    xform = get_odk_form(odk_credentials)

    files = []

    task_list = [x.id for x in project_tasks]
    for id in task_list:
        xml_form_id = f"{project_name}_{form_category}_{id}".split("_")[
            2]
        file = xform.getSubmissions(
            odkid, xml_form_id, None, False, True)
        if not file:
            json_data = None
        else:
            json_data = json.loads(file)
            json_data_value = json_data.get('value')
            if json_data_value:
                files.extend(json_data_value)

    return len(files)
