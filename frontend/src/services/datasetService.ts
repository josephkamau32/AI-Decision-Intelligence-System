import api from './api';

export const uploadDataset = async (file: File): Promise<void> => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('name', file.name);
  formData.append('description', '');

  // Don't manually set Content-Type - let axios set it with the correct boundary
  await api.post(`/api/v1/datasets/upload`, formData);
};

export const getDatasets = async (): Promise<any[]> => {
  const response = await api.get(`/api/v1/datasets/`);
  return response.data.datasets || [];
};