import React, { useEffect, useState } from 'react';
import { getDatasets } from '../services/datasetService';

const DatasetOverview: React.FC = () => {
  const [datasets, setDatasets] = useState<any[]>([]);

  useEffect(() => {
    const fetchDatasets = async () => {
      try {
        const data = await getDatasets();
        setDatasets(data);
      } catch (error) {
        console.error('Failed to fetch datasets', error);
      }
    };
    fetchDatasets();
  }, []);

  return (
    <div>
      <h1>Dataset Overview</h1>
      <ul>
        {datasets.map((dataset, index) => (
          <li key={index}>{dataset.name} - {dataset.rows} rows</li>
        ))}
      </ul>
    </div>
  );
};

export default DatasetOverview;