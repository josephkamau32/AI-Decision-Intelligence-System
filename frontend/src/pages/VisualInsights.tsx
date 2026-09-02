import React, { useEffect, useState, useCallback } from 'react';
import { getDatasets } from '../services/datasetService';
import { getCorrelation, getTrend } from '../services/visualizationService';
import { useToast } from '../context/ToastProvider';
import { LineChart, Database } from 'lucide-react';
import Card from '../components/ui/Card';
import SkeletonLoader from '../components/ui/SkeletonLoader';
import styles from './VisualInsights.module.css';

// Dynamic import for Plotly to avoid SSR issues
let Plot: any = null;
try {
    Plot = require('react-plotly.js').default;
} catch {
    // Plotly not available
}

type TabKey = 'overview' | 'trends' | 'correlation';

const VisualInsights: React.FC = () => {
    const [datasets, setDatasets] = useState<any[]>([]);
    const [selectedDatasetId, setSelectedDatasetId] = useState('');
    const [activeTab, setActiveTab] = useState<TabKey>('overview');
    const [loading, setLoading] = useState(true);
    const [chartLoading, setChartLoading] = useState(false);
    const [correlationData, setCorrelationData] = useState<any>(null);
    const [trendData, setTrendData] = useState<any>(null);
    const { addToast } = useToast();

    useEffect(() => {
        const fetchDatasets = async () => {
            try {
                const data = await getDatasets();
                const list = Array.isArray(data) ? data : (data as any)?.data || [];
                setDatasets(list);
                if (list.length > 0) setSelectedDatasetId(list[0].id);
            } catch {
                addToast('Failed to load datasets', 'error');
            } finally {
                setLoading(false);
            }
        };
        fetchDatasets();
    }, []);

    const fetchChartData = useCallback(async () => {
        if (!selectedDatasetId) return;
        setChartLoading(true);
        try {
            if (activeTab === 'correlation') {
                const data = await getCorrelation(selectedDatasetId);
                setCorrelationData(data);
            } else if (activeTab === 'trends') {
                const data = await getTrend(selectedDatasetId);
                setTrendData(data);
            }
        } catch {
            // Silently handle — show empty state
        } finally {
            setChartLoading(false);
        }
    }, [selectedDatasetId, activeTab]);

    useEffect(() => {
        fetchChartData();
    }, [fetchChartData]);

    const selectedDs = Array.isArray(datasets) ? datasets.find((d) => d.id === selectedDatasetId) : undefined;

    const tabs: { key: TabKey; label: string }[] = [
        { key: 'overview', label: 'Overview' },
        { key: 'trends', label: 'Trends' },
        { key: 'correlation', label: 'Correlation' },
    ];

    const chartColors = [
        'var(--chart-1)', 'var(--chart-2)', 'var(--chart-3)',
        'var(--chart-4)', 'var(--chart-5)', 'var(--chart-6)'
    ];

    const plotLayout: any = {
        autosize: true,
        margin: { l: 50, r: 20, t: 30, b: 40 },
        paper_bgcolor: 'transparent',
        plot_bgcolor: 'transparent',
        font: { family: 'Inter, sans-serif', size: 12, color: '#94a3b8' },
        xaxis: { gridcolor: 'rgba(148, 163, 184, 0.1)', zerolinecolor: 'rgba(148, 163, 184, 0.15)' },
        yaxis: { gridcolor: 'rgba(148, 163, 184, 0.1)', zerolinecolor: 'rgba(148, 163, 184, 0.15)' },
    };

    const renderOverview = () => {
        if (!selectedDs) return null;
        const stats = [
            { label: 'Rows', value: selectedDs.rows?.toLocaleString() || '0' },
            { label: 'Columns', value: selectedDs.columns || '0' },
            { label: 'Name', value: selectedDs.name || 'Unnamed' },
        ];

        return (
            <div className={styles.overviewGrid}>
                {stats.map((s, i) => (
                    <div key={i} className={styles.overviewStat}>
                        <div className={styles.overviewValue}>{s.value}</div>
                        <div className={styles.overviewLabel}>{s.label}</div>
                    </div>
                ))}
            </div>
        );
    };

    const renderTrends = () => {
        if (!trendData || !Plot) {
            return (
                <div className={styles.chartEmpty}>
                    <p>No trend data available for this dataset</p>
                </div>
            );
        }

        const traces = trendData.trends
            ? trendData.trends.map((t: any, i: number) => ({
                x: t.x || t.index,
                y: t.y || t.values,
                type: 'scatter',
                mode: 'lines',
                name: t.name || `Series ${i + 1}`,
                line: { color: chartColors[i % chartColors.length], width: 2 },
            }))
            : [{
                y: trendData.values || trendData.y || [],
                type: 'scatter',
                mode: 'lines',
                line: { color: chartColors[0], width: 2 },
            }];

        return (
            <Plot
                data={traces}
                layout={{ ...plotLayout, title: '' }}
                config={{ displayModeBar: false, responsive: true }}
                style={{ width: '100%', height: '360px' }}
                useResizeHandler
            />
        );
    };

    const renderCorrelation = () => {
        if (!correlationData || !Plot) {
            return (
                <div className={styles.chartEmpty}>
                    <p>No correlation data available for this dataset</p>
                </div>
            );
        }

        const matrix = correlationData.matrix || correlationData;
        const labels = correlationData.columns || correlationData.labels || [];

        return (
            <Plot
                data={[{
                    z: matrix,
                    x: labels,
                    y: labels,
                    type: 'heatmap',
                    colorscale: [
                        [0, '#312e81'], [0.25, '#4338ca'], [0.5, '#f8fafc'],
                        [0.75, '#0e7490'], [1, '#164e63']
                    ],
                    zmin: -1,
                    zmax: 1,
                }]}
                layout={{ ...plotLayout, title: '' }}
                config={{ displayModeBar: false, responsive: true }}
                style={{ width: '100%', height: '400px' }}
                useResizeHandler
            />
        );
    };

    return (
        <div className={styles.container}>
            <div className={styles.pageHeader}>
                <div>
                    <h1 className={styles.pageTitle}>Visual Insights</h1>
                    <p className={styles.pageSubtitle}>Explore your data through interactive visualizations</p>
                </div>
            </div>

            {/* Dataset Selector */}
            <div className={styles.controls}>
                <div className={styles.selectField}>
                    <label className={styles.selectLabel}>Dataset</label>
                    <select
                        className={styles.selectInput}
                        value={selectedDatasetId}
                        onChange={(e) => setSelectedDatasetId(e.target.value)}
                        disabled={loading}
                    >
                        <option value="">Select a dataset...</option>
                        {Array.isArray(datasets) && datasets.map((ds) => (
                            <option key={ds.id} value={ds.id}>
                                {ds.name} ({ds.rows?.toLocaleString()} rows)
                            </option>
                        ))}
                    </select>
                </div>
            </div>

            {loading ? (
                <Card><SkeletonLoader variant="rect" height={400} /></Card>
            ) : !selectedDatasetId ? (
                <Card className={styles.emptyCard}>
                    <div className={styles.empty}>
                        <LineChart size={40} className={styles.emptyIcon} />
                        <h3 className={styles.emptyTitle}>Select a dataset</h3>
                        <p className={styles.emptyDesc}>Choose a dataset to explore visualizations</p>
                    </div>
                </Card>
            ) : (
                <>
                    {/* Tab Controls */}
                    <div className={styles.tabBar}>
                        {tabs.map((tab) => (
                            <button
                                key={tab.key}
                                className={`${styles.tab} ${activeTab === tab.key ? styles.tabActive : ''}`}
                                onClick={() => setActiveTab(tab.key)}
                            >
                                {tab.label}
                            </button>
                        ))}
                    </div>

                    {/* Chart Area */}
                    <Card className={styles.chartCard}>
                        {chartLoading ? (
                            <SkeletonLoader variant="rect" height={360} />
                        ) : (
                            <>
                                {activeTab === 'overview' && renderOverview()}
                                {activeTab === 'trends' && renderTrends()}
                                {activeTab === 'correlation' && renderCorrelation()}
                            </>
                        )}
                    </Card>
                </>
            )}
        </div>
    );
};

export default VisualInsights;