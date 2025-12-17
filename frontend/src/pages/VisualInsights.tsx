import React, { useEffect, useState } from 'react';
import Plot from 'react-plotly.js';
import { getVisualInsights } from '../services/visualizationService';

const VisualInsights: React.FC = () => {
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const result = await getVisualInsights();
        setData(result);
      } catch (error) {
        console.error('Failed to fetch visual insights', error);
      }
    };
    fetchData();
  }, []);

  return (
    <div>
      <h1>Visual Insights</h1>
      {data ? (
        <Plot
          data={data}
          layout={{ title: 'Visual Insights' }}
        />
      ) : (
        <p>Loading...</p>
      )}
    </div>
  );
};

export default VisualInsights;