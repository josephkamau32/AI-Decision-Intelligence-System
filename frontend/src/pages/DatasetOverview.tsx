import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getDatasets, deleteDataset } from '../services/datasetService';
import { useToast } from '../context/ToastProvider';
import { Database, Upload, Trash2, ChevronDown, ChevronUp, DatabaseZap } from 'lucide-react';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import SkeletonLoader from '../components/ui/SkeletonLoader';
import styles from './DatasetOverview.module.css';

interface Dataset {
    id: string;
    name: string;
    rows: number;
    columns: number;
    created: string;
    description?: string;
}

const DatasetOverview: React.FC = () => {
    const [datasets, setDatasets] = useState<Dataset[]>([]);
    const [loading, setLoading] = useState(true);
    const [expandedId, setExpandedId] = useState<string | null>(null);
    const [deletingId, setDeletingId] = useState<string | null>(null);
    const { addToast } = useToast();
    const navigate = useNavigate();

    const fetchDatasets = async () => {
        try {
            const data = await getDatasets();
            const list = Array.isArray(data) ? data : (data as any)?.data || [];
            setDatasets(list);
        } catch (error) {
            addToast('Failed to load datasets', 'error');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchDatasets();
    }, []);

    const handleDelete = async (id: string, name: string) => {
        if (!window.confirm(`Delete dataset "${name}"? This cannot be undone.`)) return;
        setDeletingId(id);
        try {
            await deleteDataset(id);
            setDatasets((prev) => prev.filter((d) => d.id !== id));
            addToast(`Dataset "${name}" deleted`, 'success');
        } catch (error) {
            addToast('Failed to delete dataset', 'error');
        } finally {
            setDeletingId(null);
        }
    };

    const formatDate = (dateStr: string) => {
        try {
            return new Date(dateStr).toLocaleDateString('en-US', {
                month: 'short', day: 'numeric', year: 'numeric'
            });
        } catch {
            return '—';
        }
    };

    return (
        <div className={styles.container}>
            <div className={styles.pageHeader}>
                <div>
                    <h1 className={styles.pageTitle}>Datasets</h1>
                    <p className={styles.pageSubtitle}>
                        {datasets.length > 0
                            ? `${datasets.length} dataset${datasets.length !== 1 ? 's' : ''} available`
                            : 'Manage and explore your datasets'
                        }
                    </p>
                </div>
                <Button
                    variant="primary"
                    size="sm"
                    leftIcon={<Upload size={14} />}
                    onClick={() => navigate('/dashboard')}
                >
                    Upload Dataset
                </Button>
            </div>

            {loading ? (
                <Card>
                    <SkeletonLoader variant="rect" height={200} />
                </Card>
            ) : !datasets || datasets.length === 0 ? (
                <Card className={styles.emptyCard}>
                    <div className={styles.empty}>
                        <DatabaseZap size={40} className={styles.emptyIcon} />
                        <h3 className={styles.emptyTitle}>No datasets yet</h3>
                        <p className={styles.emptyDesc}>Upload your first dataset to start exploring</p>
                        <Button
                            variant="primary"
                            leftIcon={<Upload size={14} />}
                            onClick={() => navigate('/dashboard')}
                        >
                            Upload Dataset
                        </Button>
                    </div>
                </Card>
            ) : (
                <Card className={styles.tableCard}>
                    <div className={styles.tableWrapper}>
                        <table className={styles.table}>
                            <thead>
                                <tr>
                                    <th style={{ width: '40%' }}>Name</th>
                                    <th>Rows</th>
                                    <th>Columns</th>
                                    <th>Created</th>
                                    <th style={{ width: '60px' }}>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {Array.isArray(datasets) && datasets.map((ds) => (
                                    <React.Fragment key={ds.id}>
                                        <tr
                                            className={`${styles.tableRow} ${expandedId === ds.id ? styles.tableRowExpanded : ''}`}
                                            onClick={() => setExpandedId(expandedId === ds.id ? null : ds.id)}
                                        >
                                            <td className={styles.tdName}>
                                                <Database size={14} className={styles.rowIcon} />
                                                {ds.name || 'Unnamed Dataset'}
                                                <span className={styles.expandToggle}>
                                                    {expandedId === ds.id ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                                                </span>
                                            </td>
                                            <td className={styles.tdNum}>{ds.rows?.toLocaleString() || '—'}</td>
                                            <td className={styles.tdNum}>{ds.columns || '—'}</td>
                                            <td>{formatDate(ds.created)}</td>
                                            <td>
                                                <button
                                                    className={styles.deleteBtn}
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        handleDelete(ds.id, ds.name);
                                                    }}
                                                    disabled={deletingId === ds.id}
                                                    title="Delete dataset"
                                                    aria-label={`Delete ${ds.name}`}
                                                >
                                                    <Trash2 size={14} />
                                                </button>
                                            </td>
                                        </tr>
                                        {expandedId === ds.id && (
                                            <tr className={styles.expandedRow}>
                                                <td colSpan={5}>
                                                    <div className={styles.expandedContent}>
                                                        <div className={styles.detailGrid}>
                                                            <div className={styles.detailItem}>
                                                                <span className={styles.detailLabel}>Dataset ID</span>
                                                                <span className={styles.detailValue}>{ds.id}</span>
                                                            </div>
                                                            <div className={styles.detailItem}>
                                                                <span className={styles.detailLabel}>Total Rows</span>
                                                                <span className={styles.detailValue}>{ds.rows?.toLocaleString() || '0'}</span>
                                                            </div>
                                                            <div className={styles.detailItem}>
                                                                <span className={styles.detailLabel}>Columns</span>
                                                                <span className={styles.detailValue}>{ds.columns || '0'}</span>
                                                            </div>
                                                            <div className={styles.detailItem}>
                                                                <span className={styles.detailLabel}>Created</span>
                                                                <span className={styles.detailValue}>{formatDate(ds.created)}</span>
                                                            </div>
                                                        </div>
                                                        <div className={styles.detailActions}>
                                                            <Button
                                                                variant="outline"
                                                                size="sm"
                                                                onClick={(e) => {
                                                                    e.stopPropagation();
                                                                    navigate('/model-performance');
                                                                }}
                                                            >
                                                                Train Model
                                                            </Button>
                                                            <Button
                                                                variant="outline"
                                                                size="sm"
                                                                onClick={(e) => {
                                                                    e.stopPropagation();
                                                                    navigate('/visual-insights');
                                                                }}
                                                            >
                                                                Visualize
                                                            </Button>
                                                        </div>
                                                    </div>
                                                </td>
                                            </tr>
                                        )}
                                    </React.Fragment>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </Card>
            )}
        </div>
    );
};

export default DatasetOverview;