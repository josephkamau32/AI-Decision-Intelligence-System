import api from './api';

export const uploadDataset = async (file: File): Promise<void> => {
  console.log('uploadDataset called with file:', file);
  console.log('File details:', { name: file.name, size: file.size, type: file.type });

  // Remove file extension from name for backend validation
  // Backend validator doesn't allow dots in dataset names
  const nameWithoutExtension = file.name.replace(/\.[^/.]+$/, '');

  const formData = new FormData();
  formData.append('file', file);
  formData.append('name', nameWithoutExtension);
  formData.append('description', '');

  // Debug: Log FormData entries
  console.log('FormData entries:');
  Array.from(formData.entries()).forEach(([key, value]) => {
    console.log(`  ${key}:`, value);
  });

  // Don't manually set Content-Type - let axios set it with the correct boundary
  await api.post(`/api/v1/datasets/upload`, formData);
};

export const getDatasets = async (): Promise<any[]> => {
  const response = await api.get(`/api/v1/datasets/`);
  // Backend returns PaginatedResponse with 'data' field
  return response.data.data || [];
};