import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000'; // Adjust as needed

export const uploadDataset = async (file: File): Promise<void> => {
  const formData = new FormData();
  formData.append('file', file);
  await axios.post(`${API_BASE_URL}/datasets`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
};

export const getDatasets = async (): Promise<any[]> => {
  const response = await axios.get(`${API_BASE_URL}/datasets`);
  return response.data;
};