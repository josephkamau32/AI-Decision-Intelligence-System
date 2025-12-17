import React, { useState } from 'react';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import styles from './VisualInsights.module.css';

type ChartType = 'overview' | 'trends' | 'distribution' | 'correlation';

const VisualInsights: React.FC = () => {
  const [activeChart, setActiveChart] = useState<ChartType>('overview');

  const charts: { type: ChartType; label: string; icon: React.ReactNode }[] = [
    {
      type: 'overview',
      label: 'Overview',
      icon: (
        <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
      )
    },
    {
      type: 'trends',
      label: 'Trends',
      icon: (
        <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
        </svg>
      )
    },
    {
      type: 'distribution',
      label: 'Distribution',
      icon: (
        <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 8v8m-4-5v5m-4-2v2m-2 4h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
      )
    },
    {
      type: 'correlation',
      label: 'Correlation',
      icon: (
        <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
        </svg>
      )
    }
  ];

  const renderChartPlaceholder = () => {
    return (
      <div className={styles.chartPlaceholder}>
        <div className={styles.placeholderIcon}>
          <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
          </svg>
        </div>
        <h3 className={styles.placeholderTitle}>{activeChart.charAt(0).toUpperCase() + activeChart.slice(1)} Chart</h3>
        <p className={styles.placeholderText}>
          Interactive {activeChart} visualization would appear here. This could include:
        </p>
        <ul className={styles.placeholderList}>
          {activeChart === 'overview' && (
            <>
              <li>Key metrics dashboard</li>
              <li>Summary statistics</li>
              <li>Quick insights</li>
            </>
          )}
          {activeChart === 'trends' && (
            <>
              <li>Time series analysis</li>
              <li>Trend lines and forecasts</li>
              <li>Seasonal patterns</li>
            </>
          )}
          {activeChart === 'distribution' && (
            <>
              <li>Histograms and density plots</li>
              <li>Box plots</li>
              <li>Statistical summaries</li>
            </>
          )}
          {activeChart === 'correlation' && (
            <>
              <li>Correlation heatmaps</li>
              <li>Scatter plot matrices</li>
              <li>Relationship insights</li>
            </>
          )}
        </ul>
      </div>
    );
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div>
          <h1 className={styles.title}>Visual Insights</h1>
          <p className={styles.subtitle}>Explore your data through interactive visualizations</p>
        </div>
      </div>

      <div className={styles.controls}>
        {charts.map((chart) => (
          <Button
            key={chart.type}
            variant={activeChart === chart.type ? 'primary' : 'outline'}
            onClick={() => setActiveChart(chart.type)}
            leftIcon={chart.icon}
          >
            {chart.label}
          </Button>
        ))}
      </div>

      <Card variant="glass" className={styles.chartCard}>
        {renderChartPlaceholder()}
      </Card>

      <div className={styles.grid}>
        <Card variant="glass" className={styles.statCard}>
          <div className={styles.statIcon}>
            <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
            </svg>
          </div>
          <div className={styles.statContent}>
            <span className={styles.statLabel}>Total Records</span>
            <span className={styles.statValue}>124,567</span>
          </div>
        </Card>

        <Card variant="glass" className={styles.statCard}>
          <div className={styles.statIcon}>
            <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
          <div className={styles.statContent}>
            <span className={styles.statLabel}>Features</span>
            <span className={styles.statValue}>43</span>
          </div>
        </Card>

        <Card variant="glass" className={styles.statCard}>
          <div className={styles.statIcon}>
            <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div className={styles.statContent}>
            <span className={styles.statLabel}>Last Updated</span>
            <span className={styles.statValue}>2h ago</span>
          </div>
        </Card>

        <Card variant="glass" className={styles.statCard}>
          <div className={styles.statIcon}>
            <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div className={styles.statContent}>
            <span className={styles.statLabel}>Data Quality</span>
            <span className={styles.statValue}>97%</span>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default VisualInsights;