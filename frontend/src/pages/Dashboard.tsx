import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getDatasets } from '../services/datasetService';
import { getModels, ModelSummary } from '../services/modelService';
import { useToast } from '../context/ToastProvider';
import { Database, Cpu, Zap, Target, Upload, ArrowRight } from 'lucide-react';
import UploadDataset from '../components/UploadDataset';
import Card from '../components/ui/Card';
import SkeletonLoader from '../components/ui/SkeletonLoader';
import styles from './Dashboard.module.css';

interface DashboardStats {
    datasets: number;
    models: number;
    predictions: string;
    topAccuracy: string;
}

const Dashboard: React.FC = () => {
    const [stats, setStats] = useState<DashboardStats>({ datasets: 0, models: 0, predictions: '—', topAccuracy: '—' });
    const [datasets, setDatasets] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const { addToast } = useToast();
    const navigate = useNavigate();

    const fetchData = async () => {
        setLoading(true);
        try {
            const [dsData, modelData] = await Promise.allSettled([
                getDatasets(),
                getModels()
            ]);

            const rawDs = dsData.status === 'fulfilled' ? dsData.value : [];
            const dsList = Array.isArray(rawDs) ? rawDs : (rawDs as any)?.data || [];
            const rawModels = modelData.status === 'fulfilled' ? modelData.value : [];
            const modelList: ModelSummary[] = Array.isArray(rawModels) ? rawModels : (rawModels as any)?.models || [];

            setDatasets(dsList);

            // Calculate top accuracy from model metrics
            let topAcc = 0;
            modelList.forEach((m) => {
                if (m.metrics) {
                    const acc = m.metrics.accuracy || m.metrics.r2_score || 0;
                    if (acc > topAcc) topAcc = acc;
                }
            });

            setStats({
                datasets: dsList.length,
                models: modelList.length,
                predictions: modelList.length > 0 ? 'Available' : '—',
                topAccuracy: topAcc > 0 ? `${(topAcc * 100).toFixed(1)}%` : '—'
            });
        } catch (error) {
            addToast('Failed to load dashboard data', 'error');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, []);

    const statCards = [
        { icon: <Database size={18} />, label: 'Datasets', value: stats.datasets.toString(), color: 'indigo' },
        { icon: <Cpu size={18} />, label: 'Models', value: stats.models.toString(), color: 'cyan' },
        { icon: <Zap size={18} />, label: 'Predictions', value: stats.predictions, color: 'amber' },
        { icon: <Target size={18} />, label: 'Top Accuracy', value: stats.topAccuracy, color: 'emerald' },
    ];

    const pipelineSteps = [
        { num: 1, label: 'Upload Dataset', desc: 'CSV, Excel, or JSON', path: '/dataset-overview', done: stats.datasets > 0 },
        { num: 2, label: 'Train Model', desc: 'AutoML picks the best', path: '/model-performance', done: stats.models > 0 },
        { num: 3, label: 'View Insights', desc: 'Charts & explanations', path: '/visual-insights', done: stats.models > 0 },
    ];

    const formatDate = (dateStr: string) => {
        try {
            return new Date(dateStr).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        } catch {
            return '—';
        }
    };

    return (
        <div className={styles.container}>
            {/* Page Header */}
            <div className={styles.pageHeader}>
                <div>
                    <h1 className={styles.pageTitle}>Dashboard</h1>
                    <p className={styles.pageSubtitle}>
                        {stats.datasets > 0
                            ? `${stats.datasets} dataset${stats.datasets !== 1 ? 's' : ''} · ${stats.models} model${stats.models !== 1 ? 's' : ''} active`
                            : 'Upload your first dataset to get started'
                        }
                    </p>
                </div>
            </div>

            {/* Stat Cards */}
            <div className={styles.statsGrid}>
                {loading ? (
                    [1, 2, 3, 4].map((i) => (
                        <Card key={i}>
                            <SkeletonLoader variant="rect" height={70} />
                        </Card>
                    ))
                ) : (
                    statCards.map((stat, i) => (
                        <Card key={i} className={styles.statCard}>
                            <div className={`${styles.statIcon} ${styles[`statIcon_${stat.color}`]}`}>
                                {stat.icon}
                            </div>
                            <div className={styles.statContent}>
                                <div className={styles.statValue}>{stat.value}</div>
                                <div className={styles.statLabel}>{stat.label}</div>
                            </div>
                        </Card>
                    ))
                )}
            </div>

            {/* Main Content Grid */}
            <div className={styles.contentGrid}>
                {/* Upload Zone */}
                <Card className={styles.uploadCard}>
                    <div className={styles.cardHeader}>
                        <Upload size={16} className={styles.cardHeaderIcon} />
                        <h2 className={styles.cardTitle}>Upload Dataset</h2>
                    </div>
                    <UploadDataset />
                </Card>

                {/* Getting Started Pipeline */}
                <Card className={styles.pipelineCard}>
                    <div className={styles.cardHeader}>
                        <ArrowRight size={16} className={styles.cardHeaderIcon} />
                        <h2 className={styles.cardTitle}>Getting Started</h2>
                    </div>
                    <div className={styles.pipeline}>
                        {pipelineSteps.map((step, i) => (
                            <button
                                key={i}
                                className={`${styles.pipelineStep} ${step.done ? styles.pipelineStepDone : ''}`}
                                onClick={() => navigate(step.path)}
                            >
                                <div className={styles.pipelineNum}>{step.done ? '✓' : step.num}</div>
                                <div className={styles.pipelineInfo}>
                                    <div className={styles.pipelineLabel}>{step.label}</div>
                                    <div className={styles.pipelineDesc}>{step.desc}</div>
                                </div>
                                {i < pipelineSteps.length - 1 && <div className={styles.pipelineConnector} />}
                            </button>
                        ))}
                    </div>
                </Card>
            </div>

            {/* Recent Datasets Table */}
            {datasets.length > 0 && (
                <Card className={styles.tableCard}>
                    <div className={styles.cardHeader}>
                        <Database size={16} className={styles.cardHeaderIcon} />
                        <h2 className={styles.cardTitle}>Recent Datasets</h2>
                        <button className={styles.viewAllBtn} onClick={() => navigate('/dataset-overview')}>
                            View All
                        </button>
                    </div>
                    <div className={styles.tableWrapper}>
                        <table className={styles.table}>
                            <thead>
                                <tr>
                                    <th>Name</th>
                                    <th>Rows</th>
                                    <th>Columns</th>
                                    <th>Created</th>
                                </tr>
                            </thead>
                            <tbody>
                                {datasets.slice(0, 5).map((ds, i) => (
                                    <tr key={ds.id || i} onClick={() => navigate('/dataset-overview')} className={styles.tableRow}>
                                        <td className={styles.tdName}>{ds.name || 'Unnamed'}</td>
                                        <td>{ds.rows?.toLocaleString() || '—'}</td>
                                        <td>{ds.columns || '—'}</td>
                                        <td>{formatDate(ds.created)}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </Card>
            )}
        </div>
    );
};

export default Dashboard;