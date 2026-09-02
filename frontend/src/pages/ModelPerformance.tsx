import React, { useEffect, useState } from 'react';
import { getModels, trainModel, getModelMetrics, ModelSummary } from '../services/modelService';
import { getDatasets } from '../services/datasetService';
import { useToast } from '../context/ToastProvider';
import { Cpu, Plus, Trash2, Eye, Loader2 } from 'lucide-react';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import SkeletonLoader from '../components/ui/SkeletonLoader';
import styles from './ModelPerformance.module.css';

const ModelPerformance: React.FC = () => {
    const [models, setModels] = useState<ModelSummary[]>([]);
    const [datasets, setDatasets] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [showTrainModal, setShowTrainModal] = useState(false);
    const [training, setTraining] = useState(false);
    const [selectedModel, setSelectedModel] = useState<string | null>(null);
    const [modelMetrics, setModelMetrics] = useState<any>(null);
    const [metricsLoading, setMetricsLoading] = useState(false);
    const [trainForm, setTrainForm] = useState({ dataset_id: '', target_column: '', task_type: 'auto' });
    const { addToast } = useToast();

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [modelData, dsData] = await Promise.allSettled([getModels(), getDatasets()]);
                if (modelData.status === 'fulfilled') {
                    const raw = modelData.value;
                    setModels(Array.isArray(raw) ? raw : (raw as any)?.models || []);
                }
                if (dsData.status === 'fulfilled') {
                    const rawDs = dsData.value;
                    setDatasets(Array.isArray(rawDs) ? rawDs : (rawDs as any)?.data || []);
                }
            } catch (error) {
                addToast('Failed to load data', 'error');
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, []);

    const handleTrain = async () => {
        if (!trainForm.dataset_id || !trainForm.target_column) {
            addToast('Please fill in all fields', 'warning');
            return;
        }
        setTraining(true);
        try {
            await trainModel(trainForm);
            addToast('Model training started!', 'success');
            setShowTrainModal(false);
            setTrainForm({ dataset_id: '', target_column: '', task_type: 'auto' });
            // Refresh models list
            const updated = await getModels();
            setModels(Array.isArray(updated) ? updated : (updated as any)?.models || []);
        } catch (error: any) {
            addToast(error?.response?.data?.detail || 'Training failed', 'error');
        } finally {
            setTraining(false);
        }
    };

    const handleViewMetrics = async (modelId: string) => {
        if (selectedModel === modelId) {
            setSelectedModel(null);
            setModelMetrics(null);
            return;
        }
        setSelectedModel(modelId);
        setMetricsLoading(true);
        try {
            const metrics = await getModelMetrics(modelId);
            setModelMetrics(metrics);
        } catch {
            setModelMetrics(null);
            addToast('Failed to load model metrics', 'error');
        } finally {
            setMetricsLoading(false);
        }
    };

    const formatMetricValue = (val: any): string => {
        if (typeof val === 'number') return val >= 0.01 ? val.toFixed(4) : val.toExponential(2);
        return String(val || '—');
    };

    return (
        <div className={styles.container}>
            <div className={styles.pageHeader}>
                <div>
                    <h1 className={styles.pageTitle}>Model Performance</h1>
                    <p className={styles.pageSubtitle}>
                        {models.length > 0
                            ? `${models.length} model${models.length !== 1 ? 's' : ''} trained`
                            : 'Train and monitor your ML models'
                        }
                    </p>
                </div>
                <Button
                    variant="primary"
                    size="sm"
                    leftIcon={<Plus size={14} />}
                    onClick={() => setShowTrainModal(true)}
                >
                    Train New Model
                </Button>
            </div>

            {loading ? (
                <div className={styles.grid}>
                    {[1, 2, 3].map((i) => (
                        <Card key={i}><SkeletonLoader variant="rect" height={160} /></Card>
                    ))}
                </div>
            ) : !models || models.length === 0 ? (
                <Card className={styles.emptyCard}>
                    <div className={styles.empty}>
                        <Cpu size={40} className={styles.emptyIcon} />
                        <h3 className={styles.emptyTitle}>No models trained yet</h3>
                        <p className={styles.emptyDesc}>
                            {datasets.length > 0
                                ? 'Click "Train New Model" to get started'
                                : 'Upload a dataset first, then train a model'
                            }
                        </p>
                        <Button
                            variant="primary"
                            leftIcon={<Plus size={14} />}
                            onClick={() => setShowTrainModal(true)}
                            disabled={datasets.length === 0}
                        >
                            Train New Model
                        </Button>
                    </div>
                </Card>
            ) : (
                <div className={styles.grid}>
                    {Array.isArray(models) && models.map((model) => (
                        <Card key={model.model_id} className={styles.modelCard} hoverable>
                            <div className={styles.modelHeader}>
                                <div className={styles.modelIcon}>
                                    <Cpu size={16} />
                                </div>
                                <div className={styles.modelInfo}>
                                    <div className={styles.modelType}>{model.model_type || 'AutoML'}</div>
                                    <div className={styles.modelTarget}>Target: {model.target_column}</div>
                                </div>
                                <span className={styles.taskBadge}>{model.task_type}</span>
                            </div>

                            {model.metrics && (
                                <div className={styles.metricsGrid}>
                                    {Object.entries(model.metrics).slice(0, 4).map(([key, val]) => (
                                        <div key={key} className={styles.metricItem}>
                                            <div className={styles.metricValue}>{formatMetricValue(val)}</div>
                                            <div className={styles.metricLabel}>{key.replace(/_/g, ' ')}</div>
                                        </div>
                                    ))}
                                </div>
                            )}

                            <div className={styles.modelActions}>
                                <Button
                                    variant="outline"
                                    size="sm"
                                    leftIcon={<Eye size={14} />}
                                    onClick={() => handleViewMetrics(model.model_id)}
                                >
                                    {selectedModel === model.model_id ? 'Hide Details' : 'View Details'}
                                </Button>
                            </div>

                            {selectedModel === model.model_id && (
                                <div className={styles.detailPanel}>
                                    {metricsLoading ? (
                                        <SkeletonLoader variant="rect" height={80} />
                                    ) : modelMetrics ? (
                                        <div className={styles.detailMetrics}>
                                            {Object.entries(modelMetrics.metrics || modelMetrics).map(([key, val]) => (
                                                <div key={key} className={styles.detailMetric}>
                                                    <span className={styles.detailMetricLabel}>{key.replace(/_/g, ' ')}</span>
                                                    <span className={styles.detailMetricValue}>{formatMetricValue(val)}</span>
                                                </div>
                                            ))}
                                        </div>
                                    ) : (
                                        <p className={styles.noMetrics}>No detailed metrics available</p>
                                    )}
                                </div>
                            )}
                        </Card>
                    ))}
                </div>
            )}

            {/* Train Modal */}
            {showTrainModal && (
                <div className={styles.modalOverlay} onClick={() => !training && setShowTrainModal(false)}>
                    <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
                        <h2 className={styles.modalTitle}>Train New Model</h2>
                        <p className={styles.modalDesc}>Select a dataset and configure training parameters</p>

                        <div className={styles.modalForm}>
                            <div className={styles.formField}>
                                <label className={styles.formLabel}>Dataset</label>
                                <select
                                    className={styles.formSelect}
                                    value={trainForm.dataset_id}
                                    onChange={(e) => setTrainForm({ ...trainForm, dataset_id: e.target.value })}
                                    disabled={training}
                                >
                                    <option value="">Select a dataset...</option>
                                    {Array.isArray(datasets) && datasets.map((ds) => (
                                        <option key={ds.id} value={ds.id}>
                                            {ds.name} ({ds.rows?.toLocaleString()} rows, {ds.columns} cols)
                                        </option>
                                    ))}
                                </select>
                            </div>

                            <div className={styles.formField}>
                                <label className={styles.formLabel}>Target Column</label>
                                <input
                                    type="text"
                                    className={styles.formInput}
                                    placeholder="e.g., price, churn, category"
                                    value={trainForm.target_column}
                                    onChange={(e) => setTrainForm({ ...trainForm, target_column: e.target.value })}
                                    disabled={training}
                                />
                            </div>

                            <div className={styles.formField}>
                                <label className={styles.formLabel}>Task Type</label>
                                <select
                                    className={styles.formSelect}
                                    value={trainForm.task_type}
                                    onChange={(e) => setTrainForm({ ...trainForm, task_type: e.target.value })}
                                    disabled={training}
                                >
                                    <option value="auto">Auto-detect</option>
                                    <option value="classification">Classification</option>
                                    <option value="regression">Regression</option>
                                </select>
                            </div>
                        </div>

                        <div className={styles.modalActions}>
                            <Button variant="outline" onClick={() => setShowTrainModal(false)} disabled={training}>
                                Cancel
                            </Button>
                            <Button variant="primary" onClick={handleTrain} loading={training}>
                                {training ? 'Training...' : 'Start Training'}
                            </Button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default ModelPerformance;