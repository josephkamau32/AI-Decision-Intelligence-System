import React, { useEffect, useState } from 'react';
import { getModels, ModelSummary, getGlobalExplanations } from '../services/modelService';
import { getFeatureImportanceForModel } from '../services/visualizationService';
import { useToast } from '../context/ToastProvider';
import { BarChart3, HelpCircle } from 'lucide-react';
import Card from '../components/ui/Card';
import SkeletonLoader from '../components/ui/SkeletonLoader';
import styles from './FeatureImportance.module.css';

interface Feature {
    name: string;
    importance: number;
}

const FeatureImportance: React.FC = () => {
    const [models, setModels] = useState<ModelSummary[]>([]);
    const [selectedModelId, setSelectedModelId] = useState('');
    const [features, setFeatures] = useState<Feature[]>([]);
    const [loading, setLoading] = useState(true);
    const [featuresLoading, setFeaturesLoading] = useState(false);
    const [showTooltip, setShowTooltip] = useState(false);
    const { addToast } = useToast();

    useEffect(() => {
        const fetchModels = async () => {
            try {
                const data = await getModels();
                const list = Array.isArray(data) ? data : (data as any)?.models || [];
                setModels(list);
                if (list.length > 0) {
                    setSelectedModelId(list[0].model_id);
                }
            } catch {
                addToast('Failed to load models', 'error');
            } finally {
                setLoading(false);
            }
        };
        fetchModels();
    }, []);

    useEffect(() => {
        if (!selectedModelId) return;
        const fetchFeatures = async () => {
            setFeaturesLoading(true);
            try {
                // Try feature importance endpoint first, fallback to SHAP
                let data: any;
                try {
                    data = await getFeatureImportanceForModel(selectedModelId);
                } catch {
                    data = await getGlobalExplanations(selectedModelId);
                }

                // Normalize response format
                let featureList: Feature[] = [];
                if (Array.isArray(data)) {
                    featureList = data.map((f: any) => ({
                        name: f.feature || f.name || 'unknown',
                        importance: f.importance || f.value || 0
                    }));
                } else if (data?.feature_importance) {
                    featureList = Object.entries(data.feature_importance).map(([name, val]) => ({
                        name,
                        importance: val as number
                    }));
                } else if (data?.features) {
                    featureList = data.features;
                }

                featureList.sort((a, b) => b.importance - a.importance);
                setFeatures(featureList);
            } catch {
                setFeatures([]);
                addToast('Failed to load feature importance', 'error');
            } finally {
                setFeaturesLoading(false);
            }
        };
        fetchFeatures();
    }, [selectedModelId]);

    const safeFeatures = Array.isArray(features) ? features : [];
    const maxImportance = Math.max(...safeFeatures.map((f) => f.importance), 0.001);

    return (
        <div className={styles.container}>
            <div className={styles.pageHeader}>
                <div className={styles.titleRow}>
                    <h1 className={styles.pageTitle}>Feature Importance</h1>
                    <button
                        className={styles.helpBtn}
                        onMouseEnter={() => setShowTooltip(true)}
                        onMouseLeave={() => setShowTooltip(false)}
                        aria-label="What is feature importance?"
                    >
                        <HelpCircle size={16} />
                        {showTooltip && (
                            <div className={styles.tooltip}>
                                Feature importance shows which input variables have the most influence
                                on model predictions. Higher values mean the feature has more impact on
                                the model's output. This is calculated using SHAP values or model-native
                                importance scores.
                            </div>
                        )}
                    </button>
                </div>
                <p className={styles.pageSubtitle}>
                    {safeFeatures.length > 0
                        ? `${safeFeatures.length} features ranked by importance`
                        : 'Select a model to view feature importance'
                    }
                </p>
            </div>

            {/* Model Selector */}
            <div className={styles.controls}>
                <div className={styles.selectField}>
                    <label className={styles.selectLabel}>Model</label>
                    <select
                        className={styles.selectInput}
                        value={selectedModelId}
                        onChange={(e) => setSelectedModelId(e.target.value)}
                        disabled={loading}
                    >
                        <option value="">Select a model...</option>
                        {Array.isArray(models) && models.map((m) => (
                            <option key={m.model_id} value={m.model_id}>
                                {m.model_type} — {m.target_column}
                            </option>
                        ))}
                    </select>
                </div>
            </div>

            {/* Chart */}
            {loading || featuresLoading ? (
                <Card><SkeletonLoader variant="rect" height={300} /></Card>
            ) : !selectedModelId ? (
                <Card className={styles.emptyCard}>
                    <div className={styles.empty}>
                        <BarChart3 size={40} className={styles.emptyIcon} />
                        <h3 className={styles.emptyTitle}>Select a model</h3>
                        <p className={styles.emptyDesc}>Choose a trained model to view its feature importance scores</p>
                    </div>
                </Card>
            ) : safeFeatures.length === 0 ? (
                <Card className={styles.emptyCard}>
                    <div className={styles.empty}>
                        <BarChart3 size={40} className={styles.emptyIcon} />
                        <h3 className={styles.emptyTitle}>No feature data available</h3>
                        <p className={styles.emptyDesc}>This model may not have computed importance scores yet</p>
                    </div>
                </Card>
            ) : (
                <Card className={styles.chartCard}>
                    <div className={styles.barChart}>
                        {safeFeatures.slice(0, 15).map((feat, i) => {
                            const pct = (feat.importance / maxImportance) * 100;
                            return (
                                <div key={i} className={styles.barRow}>
                                    <div className={styles.barLabel} title={feat.name}>
                                        {feat.name}
                                    </div>
                                    <div className={styles.barTrack}>
                                        <div
                                            className={styles.barFill}
                                            style={{ width: `${pct}%` }}
                                        />
                                    </div>
                                    <div className={styles.barValue}>
                                        {feat.importance.toFixed(4)}
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </Card>
            )}
        </div>
    );
};

export default FeatureImportance;