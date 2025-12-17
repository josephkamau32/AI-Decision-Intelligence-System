import React, { useEffect, useState } from 'react';
import { getModelPerformance } from '../services/modelService';

const ModelPerformance: React.FC = () => {
  const [performance, setPerformance] = useState<any>(null);

  useEffect(() => {
    const fetchPerformance = async () => {
      try {
        const data = await getModelPerformance();
        setPerformance(data);
      } catch (error) {
        console.error('Failed to fetch performance', error);
      }
    };
    fetchPerformance();
  }, []);

  return (
    <div>
      <h1>Model Performance Metrics</h1>
      {performance ? (
        <div>
          <p>Accuracy: {performance.accuracy}</p>
          <p>Precision: {performance.precision}</p>
          <p>Recall: {performance.recall}</p>
        </div>
      ) : (
        <p>Loading...</p>
      )}
    </div>
  );
};

export default ModelPerformance;