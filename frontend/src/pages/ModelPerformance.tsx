import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useToast } from '../context/ToastProvider';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import Input from '../components/ui/Input';
import SkeletonLoader from '../components/ui/SkeletonLoader';
import styles from './ModelPerformance.module.css';

interface Model {
  id: string;
  name: string;
  type: string;
  accuracy: number;
  precision: number;
  recall: number;
  f1Score: number;
  trainedAt: string;
}

const ModelPerformance: React.FC = () => {
  const [models, setModels] = useState<Model[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedModel, setSelectedModel] = useState<Model | null>(null);
  const [showTrainModal, setShowTrainModal] = useState(false);
  const [datasetId, setDatasetId] = useState('');
  const [targetColumn, setTargetColumn] = useState('');
  const [training, setTraining] = useState(false);

  const navigate = useNavigate();
  const { addToast } = useToast();

  useEffect(() => {
    fetchModels();
  }, []);

  const fetchModels = () => {
    // Simulate loading models
    setTimeout(() => {
      setModels([
        {
          id: '1',
          name: 'Customer Churn Predictor',
          type: 'Random Forest',
          accuracy: 94.5,
          precision: 92.3,
          recall: 89.7,
          f1Score: 90.9,
          trainedAt: '2025-01-15'
        },
        {
          id: '2',
          name: 'Sales Forecaster',
          type: 'XGBoost',
          accuracy: 91.2,
          precision: 88.9,
          recall: 92.1,
          f1Score: 90.5,
          trainedAt: '2025-01-14'
        },
        {
          id: '3',
          name: 'Sentiment Classifier',
          type: 'Neural Network',
          accuracy: 87.8,
          precision: 85.6,
          recall: 88.3,
          f1Score: 86.9,
          trainedAt: '2025-01-13'
        }
      ]);
      setLoading(false);
    }, 1000);
  };

  const handleTrainModel = async () => {
    if (!datasetId || !targetColumn) {
      addToast('Please fill in all fields', 'error');
      return;
    }

    setTraining(true);

    try {
      // TODO: Call actual API endpoint
      // const response = await fetch('http://localhost:8000/api/v1/models/train', {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify({
      //     dataset_id: datasetId,
      //     target_column: targetColumn,
      //     task_type: 'auto'
      //   })
      // });

      // Simulate training
      await new Promise(resolve => setTimeout(resolve, 2000));

      addToast('Model training started! Check back soon for results.', 'success');
      setShowTrainModal(false);
      setDatasetId('');
      setTargetColumn('');
    } catch (error) {
      addToast('Failed to start training', 'error');
    } finally {
      setTraining(false);
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 90) return styles.scoreHigh;
    if (score >= 75) return styles.scoreMedium;
    return styles.scoreLow;
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div>
          <h1 className={styles.title}>Model Performance</h1>
          <p className={styles.subtitle}>Monitor and compare your ML models</p>
        </div>
        <Button variant="primary" onClick={() => setShowTrainModal(true)}>
          <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" style={{ width: '20px', height: '20px' }}>
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Train New Model
        </Button>
      </div>

      {/* Training Modal */}
      {showTrainModal && (
        <div className={styles.modalOverlay} onClick={() => !training && setShowTrainModal(false)}>
          <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
            <h2 className={styles.modalTitle}>Train New Model</h2>
            <div className={styles.modalContent}>
              <Input
                label="Dataset ID"
                value={datasetId}
                onChange={(e) => setDatasetId(e.target.value)}
                placeholder="Enter dataset ID"
                disabled={training}
              />
              <Input
                label="Target Column"
                value={targetColumn}
                onChange={(e) => setTargetColumn(e.target.value)}
                placeholder="e.g., target, label, outcome"
                disabled={training}
              />
              <p className={styles.modalHint}>
                Tip: After uploading a dataset, you can find its ID in the Dataset Overview page.
              </p>
            </div>
            <div className={styles.modalActions}>
              <Button
                variant="outline"
                onClick={() => setShowTrainModal(false)}
                disabled={training}
              >
                Cancel
              </Button>
              <Button
                variant="primary"
                onClick={handleTrainModel}
                loading={training}
              >
                {training ? 'Starting...' : 'Start Training'}
              </Button>
            </div>
          </div>
        </div>
      )}

      <div className={styles.grid}>
        {loading ? (
          <>
            {[1, 2, 3].map((i) => (
              <Card key={i} variant="glass">
                <SkeletonLoader variant="rect" height={200} />
              </Card>
            ))}
          </>
        ) : models.length === 0 ? (
          <div className={styles.empty}>
            <svg className={styles.emptyIcon} fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
            <p className={styles.emptyText}>No models found</p>
            <p className={styles.emptySubtext}>Train your first model to see performance metrics</p>
          </div>
        ) : (
          models.map((model) => (
            <Card
              key={model.id}
              variant="glass"
              hoverable
              className={`${styles.modelCard} ${selectedModel?.id === model.id ? styles.selected : ''}`}
              onClick={() => setSelectedModel(model)}
            >
              <div className={styles.cardHeader}>
                <h3 className={styles.modelName}>{model.name}</h3>
                <span className={styles.modelType}>{model.type}</span>
              </div>

              <div className={styles.metricsGrid}>
                <div className={styles.metric}>
                  <span className={styles.metricLabel}>Accuracy</span>
                  <div className={styles.metricValueContainer}>
                    <span className={`${styles.metricValue} ${getScoreColor(model.accuracy)}`}>
                      {model.accuracy}%
                    </span>
                  </div>
                </div>

                <div className={styles.metric}>
                  <span className={styles.metricLabel}>Precision</span>
                  <div className={styles.metricValueContainer}>
                    <span className={`${styles.metricValue} ${getScoreColor(model.precision)}`}>
                      {model.precision}%
                    </span>
                  </div>
                </div>

                <div className={styles.metric}>
                  <span className={styles.metricLabel}>Recall</span>
                  <div className={styles.metricValueContainer}>
                    <span className={`${styles.metricValue} ${getScoreColor(model.recall)}`}>
                      {model.recall}%
                    </span>
                  </div>
                </div>

                <div className={styles.metric}>
                  <span className={styles.metricLabel}>F1 Score</span>
                  <div className={styles.metricValueContainer}>
                    <span className={`${styles.metricValue} ${getScoreColor(model.f1Score)}`}>
                      {model.f1Score}%
                    </span>
                  </div>
                </div>
              </div>

              <div className={styles.cardFooter}>
                <span className={styles.trainedDate}>
                  Trained: {new Date(model.trainedAt).toLocaleDateString()}
                </span>
              </div>
            </Card>
          ))
        )}
      </div>

      {selectedModel && (
        <Card variant="glass" className={styles.detailsCard}>
          <h2 className={styles.detailsTitle}>Model Details: {selectedModel.name}</h2>
          <div className={styles.detailsContent}>
            <p className={styles.detailsText}>
              Detailed performance metrics and visualizations would appear here.
              This could include confusion matrices, ROC curves, and feature importance charts.
            </p>
          </div>
        </Card>
      )}
    </div>
  );
};

export default ModelPerformance;