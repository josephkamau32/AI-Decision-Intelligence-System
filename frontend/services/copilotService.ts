import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

export const askCopilot = async (question: string): Promise<string> => {
  const response = await axios.post(`${API_BASE_URL}/copilot/ask`, { question });
  return response.data.answer;
};