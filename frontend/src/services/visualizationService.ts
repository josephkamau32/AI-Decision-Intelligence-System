import api from './api';

export const getCorrelation = async (datasetId: string): Promise<any> => {
    const response = await api.get(`/api/v1/visualizations/correlation/${datasetId}`);
    return response.data;
};

export const getFeatureImportanceForModel = async (modelId: string): Promise<any> => {
    const response = await api.get(`/api/v1/visualizations/feature_importance/${modelId}`);
    return response.data;
};

export const getTrend = async (datasetId: string): Promise<any> => {
    const response = await api.get(`/api/v1/visualizations/trend/${datasetId}`);
    return response.data;
};

export const getShapGlobal = async (modelId: string): Promise<any> => {
    const response = await api.get(`/api/v1/visualizations/shap_global/${modelId}`);
    return response.data;
};

export const getFilters = async (datasetId: string): Promise<any> => {
    const response = await api.get(`/api/v1/visualizations/filters/${datasetId}`);
    return response.data;
};

// Legacy aliases
export const getFeatureImportance = async (): Promise<any> => {
    return { features: [] };
};

export const getVisualInsights = async (): Promise<any> => {
    return { insights: [] };
};