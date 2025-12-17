import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000'; // Adjust as needed

axios.defaults.baseURL = API_BASE_URL;

export const uploadDataset = async (file: File): Promise<void> => {
  const formData = new FormData();
  formData.append('file', file);
  await axios.post(`/api/v1/datasets`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
};

export const getDatasets = async (): Promise<any[]> => {
  const response = await axios.get(`/api/v1/datasets`);
  return response.data;
};