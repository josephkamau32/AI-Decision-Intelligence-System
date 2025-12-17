import api from './api';

export const askCopilot = async (question: string): Promise<string> => {
  const response = await api.post(`/api/v1/copilot/ask`, { question });
  return response.data.answer || 'No response received';
};