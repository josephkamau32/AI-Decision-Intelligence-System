import React, { useEffect, useState } from 'react';
import Plot from 'react-plotly.js';
import { getFeatureImportance } from '../services/visualizationService';

const FeatureImportance: React.FC = () => {
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const result = await getFeatureImportance();
        setData(result);
      } catch (error) {
        console.error('Failed to fetch feature importance', error);
      }
    };
    fetchData();
  }, []);

  return (
    <div>
      <h1>Feature Importance</h1>
      {data ? (
        <Plot
          data={data}
          layout={{ title: 'Feature Importance' }}
        />
      ) : (
        <p>Loading...</p>
      )}
    </div>
  );
};

export default FeatureImportance;