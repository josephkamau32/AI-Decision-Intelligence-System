import api from './api';

export interface ModelSummary {
    model_id: string;
    model_type: string;
    dataset_id: string;
    target_column: string;
    task_type: string;
    metrics?: Record<string, number>;
    created_at?: string;
}

export interface TrainModelRequest {
    dataset_id: string;
    target_column: string;
    task_type?: string;
}

export const getModels = async (): Promise<ModelSummary[]> => {
    const response = await api.get('/api/v1/models/list');
    if (Array.isArray(response.data)) {
        return response.data;
    }
    if (response.data && Array.isArray(response.data.models)) {
        return response.data.models;
    }
    return [];
};

export const trainModel = async (req: TrainModelRequest): Promise<any> => {
    const response = await api.post('/api/v1/models/train', req);
    return response.data;
};

export const getModelMetrics = async (modelId: string): Promise<any> => {
    const response = await api.get(`/api/v1/models/${modelId}/metrics`);
    return response.data;
};

export const getGlobalExplanations = async (modelId: string): Promise<any> => {
    const response = await api.get(`/api/v1/models/${modelId}/explain/global`);
    return response.data;
};

export const getTaskStatus = async (taskId: string): Promise<any> => {
    const response = await api.get(`/api/v1/models/tasks/${taskId}/status`);
    return response.data;
};

export const deleteModel = async (modelId: string): Promise<void> => {
    await api.delete(`/api/v1/models/${modelId}`);
};

// Legacy alias
export const getModelPerformance = getModels;