import api from './api';

export const uploadDataset = async (file: File): Promise<void> => {
    const nameWithoutExtension = file.name.replace(/\.[^/.]+$/, '');
    const formData = new FormData();
    formData.append('file', file);
    formData.append('name', nameWithoutExtension);
    formData.append('description', '');
    await api.post('/api/v1/datasets/upload', formData);
};

export const getDatasets = async (): Promise<any[]> => {
    const response = await api.get('/api/v1/datasets/');
    if (Array.isArray(response.data)) return response.data;
    if (response.data && Array.isArray(response.data.data)) return response.data.data;
    if (response.data && Array.isArray(response.data.datasets)) return response.data.datasets;
    return [];
};

export const getDatasetById = async (id: string): Promise<any> => {
    const response = await api.get(`/api/v1/datasets/${id}`);
    return response.data;
};

export const deleteDataset = async (id: string): Promise<void> => {
    await api.delete(`/api/v1/datasets/${id}`);
};