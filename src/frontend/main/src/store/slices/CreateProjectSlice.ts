import { CreateProjectStateTypes } from 'store/types/ICreateProject';
import CoreModules from '../../shared/CoreModules';
import { createSlice } from '@reduxjs/toolkit';

export const initialState: CreateProjectStateTypes = {
  editProjectDetails: { name: '', description: '', short_description: '' },
  editProjectResponse: null,
  projectDetails: { dimension: 10, no_of_buildings: 5 },
  projectDetailsResponse: null,
  projectDetailsLoading: false,
  editProjectDetailsLoading: false,
  projectArea: null,
  projectAreaLoading: false,
  formCategoryList: [],
  formCategoryLoading: false,
  generateQrLoading: false,
  organizationList: [],
  organizationListLoading: false,
  generateQrSuccess: null,
  generateProjectLogLoading: false,
  generateProjectLog: null,
  createProjectStep: 1,
  dividedTaskLoading: false,
  dividedTaskGeojson: null,
  formUpdateLoading: false,
  taskSplittingGeojsonLoading: false,
  taskSplittingGeojson: null,
  updateBoundaryLoading: false,
  drawnGeojson: null,
  drawToggle: false,
};

const CreateProject = createSlice({
  name: 'createproject',
  initialState: initialState,
  reducers: {
    SetProjectDetails(state, action) {
      state.projectDetails = { ...state.projectDetails, [action.payload.key]: action.payload.value };
    },
    CreateProjectLoading(state, action) {
      state.projectDetailsLoading = action.payload;
    },
    PostProjectDetails(state, action) {
      state.projectDetailsResponse = action.payload;
    },
    ClearCreateProjectFormData(state) {
      // state.projectDetailsResponse = null
      state.projectDetails = { dimension: 10, no_of_buildings: 5 };
      state.projectArea = null;
    },
    UploadAreaLoading(state, action) {
      state.projectAreaLoading = action.payload;
    },
    PostUploadAreaSuccess(state, action) {
      state.projectArea = action.payload;
    },
    GetFormCategoryLoading(state, action) {
      state.formCategoryLoading = action.payload;
    },
    GetFormCategoryList(state, action) {
      state.formCategoryList = action.payload;
    },
    SetFormCategory(state, action) {
      state.formCategoryList = action.payload;
    },
    SetIndividualProjectDetailsData(state, action) {
      state.projectDetails = action.payload;
    },
    GenerateProjectQRLoading(state, action) {
      state.generateQrLoading = action.payload;
    },
    GetOrganisationList(state, action) {
      state.organizationList = action.payload;
    },
    GetOrganisationListLoading(state, action) {
      state.organizationListLoading = action.payload;
    },
    GenerateProjectQRSuccess(state, action) {
      if (action.payload.status === 'SUCCESS') {
        state.generateQrSuccess = null;
      } else {
        state.generateQrSuccess = action.payload;
      }
    },
    SetGenerateProjectQRSuccess(state, action) {
      state.generateQrSuccess = action.payload;
    },
    GenerateProjectLogLoading(state, action) {
      state.generateProjectLogLoading = action.payload;
    },
    SetGenerateProjectLog(state, action) {
      state.generateProjectLog = action.payload;
    },
    SetCreateProjectFormStep(state, action) {
      state.createProjectStep = action.payload;
    },
    GetDividedTaskFromGeojsonLoading(state, action) {
      state.dividedTaskLoading = action.payload;
    },
    SetDividedTaskGeojson(state, action) {
      state.dividedTaskGeojson = action.payload;
    },
    SetDrawnGeojson(state, action) {
      state.drawnGeojson = action.payload;
    },
    SetDividedTaskFromGeojsonLoading(state, action) {
      state.dividedTaskLoading = action.payload;
    },
    //EDIT Project

    SetIndividualProjectDetails(state, action) {
      state.editProjectDetails = action.payload;
    },
    SetIndividualProjectDetailsLoading(state, action) {
      state.projectDetailsLoading = action.payload;
    },
    SetPatchProjectDetails(state, action) {
      state.editProjectResponse = action.payload;
    },
    SetPatchProjectDetailsLoading(state, action) {
      state.editProjectDetailsLoading = action.payload;
    },
    SetPostFormUpdateLoading(state, action) {
      state.formUpdateLoading = action.payload;
    },
    GetTaskSplittingPreviewLoading(state, action) {
      state.taskSplittingGeojsonLoading = action.payload;
    },
    GetTaskSplittingPreview(state, action) {
      state.dividedTaskGeojson = action.payload;
      state.taskSplittingGeojson = action.payload;
    },
    SetEditProjectBoundaryServiceLoading(state, action) {
      state.updateBoundaryLoading = action.payload;
    },
    SetDrawToggle(state, action) {
      state.drawToggle = action.payload;
    },
  },
});

export const CreateProjectActions = CreateProject.actions;
export default CreateProject.reducer;
