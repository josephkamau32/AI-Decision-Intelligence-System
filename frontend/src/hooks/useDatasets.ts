import { useState, useEffect } from 'react';
import { getDatasets } from '../services/datasetService';

export const useDatasets = () => {
  const [datasets, setDatasets] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const data = await getDatasets();
        setDatasets(data);
      } catch (err) {
        setError('Failed to fetch datasets');
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  return { datasets, loading, error };
};