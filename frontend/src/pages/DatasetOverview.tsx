import React, { useEffect, useState } from 'react';
import { getDatasets } from '../services/datasetService';
import { useToast } from '../context/ToastProvider';
import Card from '../components/ui/Card';
import SkeletonLoader from '../components/ui/SkeletonLoader';
import styles from './DatasetOverview.module.css';

interface Dataset {
  id: string;
  name: string;
  rows: number;
  columns: number;
  created: string;
}

const DatasetOverview: React.FC = () => {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [loading, setLoading] = useState(true);
  const { addToast } = useToast();

  useEffect(() => {
    const fetchDatasets = async () => {
      try {
        const data = await getDatasets();
        setDatasets(data);
      } catch (error) {
        console.error('Failed to fetch datasets', error);
        addToast('Failed to load datasets', 'error');
      } finally {
        setLoading(false);
      }
    };
    fetchDatasets();
  }, [addToast]);

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1 className={styles.title}>Dataset Overview</h1>
        <p className={styles.subtitle}>Manage and explore your datasets</p>
      </div>

      <div className={styles.grid}>
        {loading ? (
          <>
            {[1, 2, 3, 4].map((i) => (
              <Card key={i} variant="glass">
                <SkeletonLoader variant="rect" height={150} />
              </Card>
            ))}
          </>
        ) : datasets.length === 0 ? (
          <div className={styles.empty}>
            <svg className={styles.emptyIcon} fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
            </svg>
            <p className={styles.emptyText}>No datasets found</p>
            <p className={styles.emptySubtext}>Upload your first dataset to get started</p>
          </div>
        ) : (
          datasets.map((dataset) => (
            <Card key={dataset.id} variant="glass" hoverable className={styles.datasetCard}>
              <div className={styles.cardHeader}>
                <h3 className={styles.datasetName}>{dataset.name || 'Unnamed Dataset'}</h3>
              </div>
              <div className={styles.cardStats}>
                <div className={styles.stat}>
                  <span className={styles.statLabel}>Rows</span>
                  <span className={styles.statValue}>{dataset.rows?.toLocaleString() || '0'}</span>
                </div>
                <div className={styles.stat}>
                  <span className={styles.statLabel}>Columns</span>
                  <span className={styles.statValue}>{dataset.columns || '0'}</span>
                </div>
              </div>
            </Card>
          ))
        )}
      </div>
    </div>
  );
};

export default DatasetOverview;