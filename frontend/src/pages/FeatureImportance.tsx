import React, { useEffect, useState } from 'react';
import Card from '../components/ui/Card';
import SkeletonLoader from '../components/ui/SkeletonLoader';
import styles from './FeatureImportance.module.css';

interface Feature {
  name: string;
  importance: number;
  category: string;
}

const FeatureImportance: React.FC = () => {
  const [features, setFeatures] = useState<Feature[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Simulate loading feature importance data
    setTimeout(() => {
      setFeatures([
        { name: 'Customer Lifetime Value', importance: 95, category: 'Financial' },
        { name: 'Purchase Frequency', importance: 88, category: 'Behavioral' },
        { name: 'Average Order Value', importance: 82, category: 'Financial' },
        { name: 'Days Since Last Purchase', importance: 76, category: 'Temporal' },
        { name: 'Customer Age', importance: 71, category: 'Demographic' },
        { name: 'Product Category Preference', importance: 68, category: 'Behavioral' },
        { name: 'Account Age', importance: 62, category: 'Temporal' },
        { name: 'Support Tickets', importance: 58, category: 'Service' },
        { name: 'Email Engagement Rate', importance: 54, category: 'Marketing' },
        { name: 'Geographic Region', importance: 49, category: 'Demographic' },
      ]);
      setLoading(false);
    }, 1000);
  }, []);

  const getBarColor = (importance: number) => {
    if (importance >= 80) return styles.barHigh;
    if (importance >= 60) return styles.barMedium;
    return styles.barLow;
  };

  const getCategoryColor = (category: string) => {
    const colors: Record<string, string> = {
      Financial: styles.categoryFinancial,
      Behavioral: styles.categoryBehavioral,
      Temporal: styles.categoryTemporal,
      Demographic: styles.categoryDemographic,
      Service: styles.categoryService,
      Marketing: styles.categoryMarketing,
    };
    return colors[category] || styles.categoryDefault;
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div>
          <h1 className={styles.title}>Feature Importance</h1>
          <p className={styles.subtitle}>Understand which features drive your model predictions</p>
        </div>
      </div>

      <Card variant="glass" className={styles.chartCard}>
        {loading ? (
          <SkeletonLoader variant="rect" height={600} />
        ) : (
          <div className={styles.chart}>
            <div className={styles.features}>
              {features.map((feature, index) => (
                <div key={index} className={styles.featureRow}>
                  <div className={styles.featureInfo}>
                    <span className={styles.featureName}>{feature.name}</span>
                    <span className={`${styles.featureCategory} ${getCategoryColor(feature.category)}`}>
                      {feature.category}
                    </span>
                  </div>
                  <div className={styles.barContainer}>
                    <div
                      className={`${styles.bar} ${getBarColor(feature.importance)}`}
                      style={{ width: `${feature.importance}%` }}
                    >
                      <span className={styles.barLabel}>{feature.importance}%</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </Card>

      <div className={styles.infoGrid}>
        <Card variant="glass" className={styles.infoCard}>
          <h3 className={styles.infoTitle}>What is Feature Importance?</h3>
          <p className={styles.infoText}>
            Feature importance measures how much each input feature contributes to the model's predictions.
            Higher values indicate features that have more influence on the model's decisions.
          </p>
        </Card>

        <Card variant="glass" className={styles.infoCard}>
          <h3 className={styles.infoTitle}>How to Interpret</h3>
          <p className={styles.infoText}>
            Focus on the top features for model optimization. Features with low importance might be
            candidates for removal to simplify the model and reduce overfitting.
          </p>
        </Card>
      </div>
    </div>
  );
};

export default FeatureImportance;