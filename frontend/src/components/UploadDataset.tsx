import React, { useState } from 'react';
import { uploadDataset } from '../services/datasetService';

const UploadDataset: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFile(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    try {
      await uploadDataset(file);
      alert('Dataset uploaded successfully');
    } catch (error) {
      alert('Upload failed');
    }
    setUploading(false);
  };

  return (
    <div>
      <h2>Upload Dataset</h2>
      <input type="file" accept=".csv,.xlsx,.json" onChange={handleFileChange} />
      <button onClick={handleUpload} disabled={!file || uploading}>
        {uploading ? 'Uploading...' : 'Upload'}
      </button>
    </div>
  );
};

export default UploadDataset;