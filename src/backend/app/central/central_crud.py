# Copyright (c) 2023 Humanitarian OpenStreetMap Team
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
import base64
import json
import os
import pathlib
import zlib

# import osm_fieldwork

# Qr code imports
import segno
import xmltodict
from fastapi import HTTPException
from fastapi.logger import logger as logger
from osm_fieldwork.CSVDump import CSVDump
from osm_fieldwork.OdkCentral import OdkAppUser, OdkForm, OdkProject
from pyxform.xls2xform import xls2xform_convert
from sqlalchemy.orm import Session

from ..config import settings
from ..db import db_models
from ..projects import project_schemas


def get_odk_project(odk_central: project_schemas.ODKCentral = None):
    """
    Get an instance of the OdkProject class with the provided credentials.

    Args:
        odk_central (project_schemas.ODKCentral, optional): The ODK Central credentials. Defaults to None.

    Returns:
        An instance of the OdkProject class.

    Raises:
        HTTPException: If there is an error creating a project on ODK Central.
    """
    if odk_central:
        url = odk_central.odk_central_url
        user = odk_central.odk_central_user
        pw = odk_central.odk_central_password
    else:
        logger.debug("ODKCentral connection variables not set in function")
        logger.debug("Attempting extraction from environment variables")
        url = settings.ODK_CENTRAL_URL
        user = settings.ODK_CENTRAL_USER
        pw = settings.ODK_CENTRAL_PASSWD

    try:
        logger.debug(f"Connecting to ODKCentral: url={url} user={user}")
        project = OdkProject(url, user, pw)
    except Exception as e:
        logger.error(e)
        raise HTTPException(
            status_code=500, detail=f"Error creating project on ODK Central: {e}"
        ) from e

    return project


def get_odk_form(odk_central: project_schemas.ODKCentral = None):
    """
    Get an instance of the OdkForm class with the provided credentials.

    Args:
        odk_central (project_schemas.ODKCentral, optional): The ODK Central credentials. Defaults to None.

    Returns:
        An instance of the OdkForm class.

    Raises:
        HTTPException: If there is an error creating a project on ODK Central.
    """
    if odk_central:
        url = odk_central.odk_central_url
        user = odk_central.odk_central_user
        pw = odk_central.odk_central_password

    else:
        logger.debug("ODKCentral connection variables not set in function")
        logger.debug("Attempting extraction from environment variables")
        url = settings.ODK_CENTRAL_URL
        user = settings.ODK_CENTRAL_USER
        pw = settings.ODK_CENTRAL_PASSWD

    try:
        logger.debug(f"Connecting to ODKCentral: url={url} user={user}")
        form = OdkForm(url, user, pw)
    except Exception as e:
        logger.error(e)
        raise HTTPException(
            status_code=500, detail=f"Error creating project on ODK Central: {e}"
        ) from e

    return form


def get_odk_app_user(odk_central: project_schemas.ODKCentral = None):
    """
    Get an instance of the OdkAppUser class with the provided credentials.

    Args:
        odk_central (project_schemas.ODKCentral, optional): The ODK Central credentials. Defaults to None.

    Returns:
        An instance of the OdkAppUser class.

    Raises:
        HTTPException: If there is an error creating a project on ODK Central.
    """
    if odk_central:
        url = odk_central.odk_central_url
        user = odk_central.odk_central_user
        pw = odk_central.odk_central_password
    else:
        logger.debug("ODKCentral connection variables not set in function")
        logger.debug("Attempting extraction from environment variables")
        url = settings.ODK_CENTRAL_URL
        user = settings.ODK_CENTRAL_USER
        pw = settings.ODK_CENTRAL_PASSWD

    try:
        logger.debug(f"Connecting to ODKCentral: url={url} user={user}")
        form = OdkAppUser(url, user, pw)
    except Exception as e:
        logger.error(e)
        raise HTTPException(
            status_code=500, detail=f"Error creating project on ODK Central: {e}"
        ) from e

    return form


def list_odk_projects(odk_central: project_schemas.ODKCentral = None):
    """
    List all projects on a remote ODK Server.

    Args:
        odk_central (project_schemas.ODKCentral, optional): The ODK Central credentials. Defaults to None.

    Returns:
        A list of projects on the remote ODK Server.
    """
    project = get_odk_project(odk_central)
    return project.listProjects()


def create_odk_project(name: str, odk_central: project_schemas.ODKCentral = None):
    """
    Create a project on a remote ODK Server.

    Args:
        name (str): The name of the project to create.
        odk_central (project_schemas.ODKCentral, optional): The ODK Central credentials. Defaults to None.

    Returns:
        The result of creating the project on the remote ODK Server.

    Raises:
        HTTPException: If there is an error creating a project on ODK Central or if authentication fails.
    """
    project = get_odk_project(odk_central)

    try:
        result = project.createProject(name)
        if result.get("code") == 401.2:
            raise HTTPException(
                status_code=500,
                detail=f"Could not authenticate to odk central.",
            )

        logger.debug(f"ODKCentral response: {result}")
        logger.info(f"Project {name} has been created on the ODK Central server.")
        return result
    except Exception as e:
        logger.error(e)
        raise HTTPException(
            status_code=500, detail=f"Error creating project on ODK Central: {e}"
        ) from e


def delete_odk_project(project_id: int, odk_central: project_schemas.ODKCentral = None):
    """
    Delete a project from a remote ODK Server.

    Args:
        project_id (int): The ID of the project to delete.
        odk_central (project_schemas.ODKCentral, optional): The ODK Central credentials. Defaults to None.

    Returns:
        The result of deleting the project from the remote ODK Server.
    """
    # FIXME: when a project is deleted from Central, we have to update the
    # odkid in the projects table
    try:
        project = get_odk_project(odk_central)
        result = project.deleteProject(project_id)
        logger.info(f"Project {project_id} has been deleted from the ODK Central server.")
        return result
    except Exception as e:
        return 'Could not delete project from central odk'


def create_appuser(project_id: int, name: str, odk_credentials: project_schemas.ODKCentral = None):
    """
    Create an app-user on a remote ODK Server.

    Args:
        project_id (int): The ID of the project to create an app-user for.
        name (str): The name of the app-user to create.
        odk_credentials (project_schemas.ODKCentral, optional): The ODK Central credentials. Defaults to None.

    Returns:
        The result of creating an app-user on the remote ODK Server.
    """
    if odk_credentials:
        url = odk_credentials.odk_central_url
        user = odk_credentials.odk_central_user
        pw = odk_credentials.odk_central_password

    else:
        logger.debug("ODKCentral connection variables not set in function")
        logger.debug("Attempting extraction from environment variables")
        url = settings.ODK_CENTRAL_URL
        user = settings.ODK_CENTRAL_USER
        pw = settings.ODK_CENTRAL_PASSWD

    app_user = OdkAppUser(url, user, pw)
    result = app_user.create(project_id, name)
    logger.info(f"Created app user: {result.json()}")
    return result


def delete_app_user(
    project_id: int, name: str, odk_central: project_schemas.ODKCentral = None
):
    """
    Delete an app-user from a remote ODK Server.

    Args:
        project_id (int): The ID of the project to delete an app-user from.
        name (str): The name of the app-user to delete.
        odk_central (project_schemas.ODKCentral, optional): The ODK Central credentials. Defaults to None.

    Returns:
        The result of deleting an app-user from the remote ODK Server.
    """
    appuser = get_odk_app_user(odk_central)
    result = appuser.delete(project_id, name)
    return result


def upload_xform_media(project_id: int, xform_id:str, filespec: str,    odk_credentials: dict = None):
    """
    Upload media for an XForm on a remote ODK Central server.

    Args:
        project_id (int): The ID of the project to upload media for.
        xform_id (str): The ID of the XForm to upload media for.
        filespec (str): The path to the media file to upload.
        odk_credentials (dict, optional): A dictionary containing the ODK Central credentials. Defaults to None.

    Returns:
        The result of uploading media for an XForm on the remote ODK Central server.
    """

    title = os.path.basename(os.path.splitext(filespec)[0])

    if odk_credentials:
        url = odk_credentials["odk_central_url"]
        user = odk_credentials["odk_central_user"]
        pw = odk_credentials["odk_central_password"]

    else:
        logger.debug("ODKCentral connection variables not set in function")
        logger.debug("Attempting extraction from environment variables")
        url = settings.ODK_CENTRAL_URL
        user = settings.ODK_CENTRAL_USER
        pw = settings.ODK_CENTRAL_PASSWD

    try:
        xform = OdkForm(url, user, pw)
    except Exception as e:
        logger.error(e)
        raise HTTPException(
            status_code=500, detail={"message": "Connection failed to odk central"}
        ) from e

    result = xform.uploadMedia(project_id, title, filespec)
    result = xform.publishForm(project_id, title)
    return result



def create_odk_xform(
    project_id: int, 
    xform_id: str, 
    filespec: str, 
    odk_credentials: project_schemas.ODKCentral = None,
    create_draft: bool = False,
    upload_media = True,
    convert_to_draft_when_publishing = True

):
    """
    Create an XForm on a remote ODK Central server.

    Args:
        project_id (int): The ID of the project to create an XForm for.
        xform_id (str): The ID of the XForm to create.
        filespec (str): The path to the XLSForm file to use for creating the XForm.
        odk_credentials (project_schemas.ODKCentral, optional): The ODK Central credentials. Defaults to None.
        create_draft (bool, optional): Whether to create a draft version of the XForm. Defaults to False.
        upload_media (bool, optional): Whether to upload media for the XForm. Defaults to True.
        convert_to_draft_when_publishing (bool, optional): Whether to convert an existing published XForm to draft mode when publishing. Defaults to True.

    Returns:
        The result of creating an XForm on the remote ODK Central server.
    """
    title = os.path.basename(os.path.splitext(filespec)[0])
    # result = xform.createForm(project_id, title, filespec, True)
    # Pass odk credentials of project in xform

    if not odk_credentials:
        odk_credentials = project_schemas.ODKCentral(
            odk_central_url=settings.ODK_CENTRAL_URL,
            odk_central_user=settings.ODK_CENTRAL_USER,
            odk_central_password=settings.ODK_CENTRAL_PASSWD,
        )
    try:
        xform = get_odk_form(odk_credentials)
    except Exception as e:
        logger.error(e)
        raise HTTPException(
            status_code=500, detail={"message": "Connection failed to odk central"}
        ) from e

    result = xform.createForm(project_id, xform_id, filespec, create_draft)

    if result != 200 and result != 409:
        return result
    data = f"/tmp/{title}.geojson"

    # This modifies an existing published XForm to be in draft mode.
    # An XForm must be in draft mode to upload an attachment.
    if upload_media:
        result = xform.uploadMedia(project_id, 
                                   title, 
                                   data, 
                                   convert_to_draft_when_publishing
                                   )

    result = xform.publishForm(project_id, title)
    return result


def delete_odk_xform(
    project_id: int,
    xform_id: str,
    filespec: str,
    odk_central: project_schemas.ODKCentral = None,
):
    """
    Delete an XForm from a remote ODK Central server.

    Args:
        project_id (int): The ID of the project to delete an XForm from.
        xform_id (str): The ID of the XForm to delete.
        filespec (str): The path to the XLSForm file used to create the XForm.
        odk_central (project_schemas.ODKCentral, optional): The ODK Central credentials. Defaults to None.

    Returns:
        The result of deleting an XForm from the remote ODK Central server.
    """
    xform = get_odk_form(odk_central)
    result = xform.deleteForm(project_id, xform_id, filespec, True)
    # FIXME: make sure it's a valid project id
    return result


def list_odk_xforms(project_id: int, odk_central: project_schemas.ODKCentral = None):
    """
    List all XForms in an ODK Central project.

    Args:
        project_id (int): The ID of the project to list XForms for.
        odk_central (project_schemas.ODKCentral, optional): The ODK Central credentials. Defaults to None.

    Returns:
        A list of XForms in the specified ODK Central project.
    """
    project = get_odk_project(odk_central)
    xforms = project.listForms(project_id)
    # FIXME: make sure it's a valid project id
    return xforms


def get_form_full_details(
        odk_project_id: int,
        form_id: str,
        odk_central: project_schemas.ODKCentral
    ):
    """
    Get the full details of an XForm in an ODK Central project.

    Args:
        odk_project_id (int): The ID of the ODK Central project to get the full details of an XForm for.
        form_id (str): The ID of the XForm to get the full details for.
        odk_central (project_schemas.ODKCentral): The ODK Central credentials.

    Returns:
        A dictionary containing the full details of the specified XForm in the specified ODK Central project.
    """
    form = get_odk_form(odk_central)
    form_details = form.getFullDetails(odk_project_id, form_id)
    return form_details.json()


def list_task_submissions(odk_project_id:int, form_id: str, odk_central: project_schemas.ODKCentral = None):
    """
    List submissions for a specific task in an ODK Central project.

    Args:
        odk_project_id (int): The ID of the ODK Central project to list submissions for.
        form_id (str): The ID of the form to list submissions for.
        odk_central (project_schemas.ODKCentral, optional): The ODK Central credentials. Defaults to None.

    Returns:
        A list of submissions for the specified task in the specified ODK Central project.
    """
    project = get_odk_form(odk_central)
    submissions = project.listSubmissions(odk_project_id, form_id)
    return submissions


def list_submissions(project_id: int, odk_central: project_schemas.ODKCentral = None):
    """
    List all submissions from a remote ODK server.

    Args:
        project_id (int): The ID of the project to list submissions for.
        odk_central (project_schemas.ODKCentral, optional): The ODK Central credentials. Defaults to None.

    Returns:
        A list of all submissions from the remote ODK server for the specified project.
    """
    project = get_odk_project(odk_central)
    xform = get_odk_form(odk_central)
    submissions = list()
    for user in project.listAppUsers(project_id):
        for subm in xform.listSubmissions(project_id, user["displayName"]):
            submissions.append(subm)

    return submissions


def get_form_list(db: Session, skip: int, limit: int):
    """
    Get a list of IDs and titles of XForms from the database.

    Args:
        db (Session): The database session.
        skip (int): The number of records to skip before returning results.
        limit (int): The maximum number of records to return.

    Returns:
        A list of tuples containing the IDs and titles of XForms from the database.

    Raises:
        HTTPException: If there is an error querying the database.
    """
    try:
        return (
            db.query(db_models.DbXForm.id, db_models.DbXForm.title)
            .offset(skip)
            .limit(limit)
            .all()
        )
    except Exception as e:
        logger.error(e)
        raise HTTPException(e) from e


def download_submissions(
    project_id: int,
    xform_id: str,
    submission_id: str = None,
    get_json: bool = True,
    odk_central: project_schemas.ODKCentral = None,
):
    """
    Download submissions from a remote ODK server.

    Args:
        project_id (int): The ID of the project to download submissions for.
        xform_id (str): The ID of the XForm to download submissions for.
        submission_id (str, optional): The ID of a specific submission to download. Defaults to None.
        get_json (bool, optional): Whether to return submissions in JSON format. Defaults to True.
        odk_central (project_schemas.ODKCentral, optional): The ODK Central credentials. Defaults to None.

    Returns:
        A list of downloaded submissions from the remote ODK server for the specified parameters.
    """    
    xform = get_odk_form(odk_central)
    # FIXME: should probably filter by timestamps or status value
    data = xform.getSubmissions(project_id, xform_id, submission_id, True, get_json)
    fixed = str(data, "utf-8")
    return fixed.splitlines()


async def test_form_validity(
    xform_content: str,
    form_type: str
    ):
    """
    Validate an XForm.

    Args:
        xform_content (str): The content of the XForm to validate.
        form_type (str): The type of the XForm (xls or xlsx).

    Returns:
        A dictionary containing a message indicating whether the XForm is valid.

    Raises:
        HTTPException: If the XForm is invalid.
    """
    try:
        xlsform_path = f"/tmp/validate_form.{form_type}"
        outfile = f"/tmp/outfile.xml"

        with open(xlsform_path, "wb") as f:
            f.write(xform_content)

        xls2xform_convert(xlsform_path=xlsform_path, xform_path=outfile, validate=False)
        return {"message": "Your form is valid"}
    except Exception as e:
        raise HTTPException(status_code=400, detail={
            "message": "Your form is invalid",
            "possible_reason":str(e)
        })


def generate_updated_xform(
    xlsform: str,
    xform: str,
    form_type : str,
):
    """
    Update the version in an XForm so it's unique.

    Args:
        xlsform (str): The path to the XLSForm file used to create the XForm.
        xform (str): The path to the XForm file to update.
        form_type (str): The type of the XForm (xls, xlsx, or xml).

    Returns:
        The path to the updated XForm file.

    Raises:
        HTTPException: If there is an error converting the XLSForm to an XForm or if the generated XForm file is empty.
    """
    name = os.path.basename(xform).replace(".xml", "")
    outfile = xform
    if form_type != 'xml':
        try:
            xls2xform_convert(xlsform_path=xlsform, xform_path=outfile, validate=False)
        except Exception as e:
            logger.error(f"Couldn't convert {xlsform} to an XForm!", str(e))
            raise HTTPException(status_code=400, detail=str(e)) from e

        if os.path.getsize(outfile) <= 0:
            logger.warning(f"{outfile} is empty!")
            raise HTTPException(status=400, detail=f"{outfile} is empty!") from None

        xls = open(outfile, "r")
        data = xls.read()
        xls.close()
    else:
        xls = open(xlsform, "r")
        data = xls.read()
        xls.close()

    tmp = name.split("_")
    tmp[0]
    tmp[1]
    id = tmp[2].split(".")[0]
    extract = f"jr://file/{name}.geojson"
    xml = xmltodict.parse(str(data))
    # First change the osm data extract file
    index = 0
    for inst in xml["h:html"]["h:head"]["model"]["instance"]:
        try:
            if "@src" in inst:
                if (
                    xml["h:html"]["h:head"]["model"]["instance"][index]["@src"].split(
                        "."
                    )[1]
                    == "geojson"
                ):
                    xml["h:html"]["h:head"]["model"]["instance"][index][
                        "@src"
                    ] = extract
            if "data" in inst:
                if "data" == inst:
                    xml["h:html"]["h:head"]["model"]["instance"]["data"]["@id"] = id
                    # xml["h:html"]["h:head"]["model"]["instance"]["data"]["@id"] = xform

                else:
                    xml["h:html"]["h:head"]["model"]["instance"][0]["data"]["@id"] = id
        except Exception:
            continue
        index += 1
    xml["h:html"]["h:head"]["h:title"] = name

    # write the updated XML file
    outxml = open(outfile, "w")
    newxml = xmltodict.unparse(xml)
    outxml.write(newxml)
    outxml.close()

    # insert the new version
    # forms = table(
    #     "xlsforms", column("title"), column("xls"), column("xml"), column("id")
    # )
    # ins = insert(forms).values(title=name, xml=data)
    # sql = ins.on_conflict_do_update(
    #     constraint="xlsforms_title_key", set_=dict(title=name, xml=newxml)
    # )
    # db.execute(sql)
    # db.commit()

    return outfile


def create_qrcode(project_id: int,
                  token: str,
                  name: str,
                  odk_central_url: str = None
                  ):
    """
    Create a QR Code for an app-user.

    Args:
        project_id (int): The ID of the project to create a QR Code for.
        token (str): The token to use for creating the QR Code.
        name (str): The name of the app-user to create a QR Code for.
        odk_central_url (str, optional): The URL of the ODK Central server. Defaults to None.

    Returns:
        A dictionary containing the settings for generating a QR Code for an app-user.
    """
    if not odk_central_url:
        logger.debug("ODKCentral connection variables not set in function")
        logger.debug("Attempting extraction from environment variables")
        odk_central_url = settings.ODK_CENTRAL_URL

    # Qr code text json in the format acceptable by odk collect.
    qr_code_setting = {
        "general": {
            "server_url": f"{odk_central_url}/v1/key/{token}/projects/{project_id}",
            "form_update_mode": "match_exactly",
            "basemap_source": "osm",
            "autosend": "wifi_and_cellular",
        },
        "project": {"name": f"{name}"},
        "admin": {},
    }

    # Base64 encoded
    qr_data = base64.b64encode(
        zlib.compress(json.dumps(qr_code_setting).encode("utf-8"))
    )

    # Generate qr code using segno
    qrcode = segno.make(qr_data, micro=False)
    qrcode.save(f"/tmp/{name}_qr.png", scale=5)
    return qr_data


def upload_media(
    project_id: int,
    xform_id: str,
    filespec: str,
    odk_central: project_schemas.ODKCentral = None,
):
    """
    Upload a data file to ODK Central.

    Args:
        project_id (int): The ID of the project to upload a data file for.
        xform_id (str): The ID of the XForm to upload a data file for.
        filespec (str): The path to the data file to upload.
        odk_central (project_schemas.ODKCentral, optional): The ODK Central credentials. Defaults to None.
    """
    xform = get_odk_form(odk_central)
    xform.uploadMedia(project_id, xform_id, filespec)


def download_media(
    project_id: int,
    xform_id: str,
    filespec: str,
    odk_central: project_schemas.ODKCentral = None,
):
    """
    Download a data file from ODK Central.

    Args:
        project_id (int): The ID of the project to download a data file for.
        xform_id (str): The ID of the XForm to download a data file for.
        filespec (str): The path to save the downloaded data file to.
        odk_central (project_schemas.ODKCentral, optional): The ODK Central credentials. Defaults to None.
    """
    xform = get_odk_form(odk_central)
    filename = "test"
    xform.getMedia(project_id, xform_id, filename)


def convert_csv(
    filespec: str,
    data: bytes,
):
    """
    Convert an ODK CSV file to OSM XML and GeoJson.

    Args:
        filespec (str): The path to the CSV file to convert.
        data (bytes): The content of the CSV file.

    Returns:
        True if the conversion is successful.
    """
    pathlib.Path(osm_fieldwork.__file__).resolve().parent
    csvin = CSVDump("/xforms.yaml")

    osmoutfile = f"{filespec}.osm"
    csvin.createOSM(osmoutfile)

    jsonoutfile = f"{filespec}.geojson"
    csvin.createGeoJson(jsonoutfile)

    if len(data) == 0:
        logger.debug("Parsing csv file %r" % filespec)
        # The yaml file is in the package files for osm_fieldwork
        data = csvin.parse(filespec)
    else:
        csvdata = csvin.parse(filespec, data)
        for entry in csvdata:
            logger.debug(f"Parsing csv data {entry}")
            if len(data) <= 1:
                continue
            feature = csvin.createEntry(entry)
            # Sometimes bad entries, usually from debugging XForm design, sneak in
            if len(feature) > 0:
                if "tags" not in feature:
                    logger.warning("Bad record! %r" % feature)
                else:
                    if "lat" not in feature["attrs"]:
                        import epdb

                        epdb.st()
                    csvin.writeOSM(feature)
                    # This GeoJson file has all the data values
                    csvin.writeGeoJson(feature)
                    pass

    csvin.finishOSM()
    csvin.finishGeoJson()

    return True
