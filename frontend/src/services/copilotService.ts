import api from './api';

export interface CopilotRequest {
  question: string;
  dataset_id?: string;
  model_id?: string;
  context?: Record<string, any>;
}

export interface CopilotResponse {
  answer: string;
  sources: string[];
  confidence: number;
  metadata?: Record<string, any>;
}

export interface CopilotError {
  error: string;
  details?: string;
}

/**
 * Ask the AI Copilot a question
 * @param question - The user's question
 * @param datasetId - Optional dataset context
 * @param modelId - Optional model context
 * @param retries - Number of retry attempts (default: 2)
 * @param signal - AbortSignal for canceling the request
 * @returns Promise<CopilotResponse>
 */
export const askCopilot = async (
  question: string,
  datasetId?: string,
  modelId?: string,
  retries: number = 2,
  signal?: AbortSignal
): Promise<CopilotResponse> => {
  const request: CopilotRequest = {
    question,
    dataset_id: datasetId,
    model_id: modelId,
  };

  let lastError: Error | null = null;

  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const response = await api.post<CopilotResponse>(
        `/api/v1/copilot/ask`,
        request,
        { signal }
      );

      // Validate response structure
      if (!response.data || typeof response.data.answer !== 'string') {
        throw new Error('Invalid response format from copilot API');
      }

      return {
        answer: response.data.answer,
        sources: response.data.sources || [],
        confidence: response.data.confidence || 0,
        metadata: response.data.metadata || {},
      };
    } catch (error: any) {
      lastError = error;

      // Don't retry if request was cancelled
      if (signal?.aborted) {
        throw new Error('Request cancelled');
      }

      // Don't retry on 4xx errors (client errors)
      if (error.response?.status >= 400 && error.response?.status < 500) {
        throw error;
      }

      // If this is not the last attempt, wait before retrying
      if (attempt < retries) {
        // Exponential backoff: 1s, 2s, 4s...
        const delay = Math.pow(2, attempt) * 1000;
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
  }

  // If all retries failed, throw the last error
  throw lastError || new Error('Failed to get response from AI Copilot');
};

/**
 * Quick query using GET parameters (simpler API)
 */
export const queryCopilot = async (
  query: string,
  datasetId?: string,
  modelId?: string
): Promise<CopilotResponse> => {
  const params = new URLSearchParams({ query });
  if (datasetId) params.append('dataset_id', datasetId);
  if (modelId) params.append('model_id', modelId);

  const response = await api.post<CopilotResponse>(
    `/api/v1/copilot/query?${params.toString()}`
  );

  return {
    answer: response.data.answer,
    sources: response.data.sources || [],
    confidence: response.data.confidence || 0,
    metadata: response.data.metadata || {},
  };
};