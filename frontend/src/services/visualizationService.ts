import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

export const getFeatureImportance = async (): Promise<any> => {
  const response = await axios.get(`${API_BASE_URL}/visualizations/feature-importance`);
  return response.data;
};

export const getVisualInsights = async (): Promise<any> => {
  const response = await axios.get(`${API_BASE_URL}/visualizations/insights`);
  return response.data;
};