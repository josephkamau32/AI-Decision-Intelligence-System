import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

export const getModelPerformance = async (): Promise<any> => {
  const response = await axios.get(`${API_BASE_URL}/models/performance`);
  return response.data;
};