import React, { useEffect } from "react";
import { Vector as VectorLayer } from "ol/layer.js";
import GeoJSON from "ol/format/GeoJSON";
import { Vector as VectorSource } from "ol/source.js";
import { geojsonObjectModel } from "../models/geojsonObjectModel";
import MapStyles from "../hooks/MapStyles";
import environment from "fmtm/environment";
import CoreModules from "fmtm/CoreModules";
import { get } from "ol/proj";
let geojsonObject;
const TasksLayer = (map, view, feature) => {
  const params = CoreModules.useParams();
  const state = CoreModules.useAppSelector((state) => state.project);
  const geojsonStyles = MapStyles(feature);

  useEffect(() => {
    if (state.projectTaskBoundries.length != 0 && map != undefined) {
      if (
        state.projectTaskBoundries.findIndex(
          (project) => project.id == environment.decode(params.id)
        ) != -1
      ) {
        geojsonObject = null;
        const index = state.projectTaskBoundries.findIndex(
          (project) => project.id == environment.decode(params.id)
        );

        const styleFunction = function (feature) {
          let id = feature.getId().toString().replace("_", ",");
          geojsonStyles[id.split(",")[1]];
          return geojsonStyles[id.split(",")[1]];
        };

        geojsonObject = { ...geojsonObjectModel };
        geojsonObject["features"] = [];
        state.projectTaskBoundries[index].taskBoundries.forEach((task) => {
          geojsonObject["features"].push({
            id: `${task.id}_${task.task_status_str}`,
            type: task.outline_geojson.type,
            geometry: task.outline_geojson.geometry,
            // properties: task.properties
          });
        });
        console.log(geojsonObject, "geojsonObject");
        console.log(state.projectTaskBoundries, "projectTaskBoundries");
        const vectorSource = new VectorSource({
          features: new GeoJSON().readFeatures(geojsonObject, {
            featureProjection: get("EPSG:3857"),
          }),
        });

        const vectorLayer = new VectorLayer({
          source: vectorSource,
          style: styleFunction,
          zIndex: 10,
        });
        // Initialize variables to store the extent
        var minX = Infinity;
        var minY = Infinity;
        var maxX = -Infinity;
        var maxY = -Infinity;

        // Iterate through the features and calculate the extent
        vectorSource.getFeatures().forEach(function (feature) {
          var geometry = feature.getGeometry();
          var extent = geometry.getExtent();

          minX = Math.min(minX, extent[0]);
          minY = Math.min(minY, extent[1]);
          maxX = Math.max(maxX, extent[2]);
          maxY = Math.max(maxY, extent[3]);
        });

        // The extent of the vector layer
        var extent = [minX, minY, maxX, maxY];

        map.getView().fit(extent, {
          duration: 2000, // Animation duration in milliseconds
          padding: [50, 50, 50, 200], // Optional padding around the extent
        });
        map.addLayer(vectorLayer);
        map.on("loadend", function () {
          map.getTargetElement().classList.remove("spinner");
        });
      }
    }
  }, [state.newProjectTrigger, map]);

  // useEffect(() => {

  //     if (state.projectTaskBoundries.length != 0 && map != undefined) {
  //         if (state.projectTaskBoundries.findIndex(project => project.id == environment.decode(params.id)) != -1) {
  //         }
  //     }
  // }, [map])
};

export default TasksLayer;
