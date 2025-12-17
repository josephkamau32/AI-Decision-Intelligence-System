import React, { useState, useRef } from 'react';
import { uploadDataset } from '../services/datasetService';
import { useToast } from '../context/ToastProvider';
import Button from './ui/Button';
import styles from './UploadDataset.module.css';

const UploadDataset: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [progress, setProgress] = useState(0);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { addToast } = useToast();

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    setUploading(true);
    setProgress(0);

    // Simulate upload progress
    const progressInterval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 90) {
          clearInterval(progressInterval);
          return 90;
        }
        return prev + 10;
      });
    }, 200);

    try {
      await uploadDataset(file);
      setProgress(100);
      addToast('Dataset uploaded successfully!', 'success');
      setFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    } catch (error) {
      addToast('Upload failed. Please try again.', 'error');
    } finally {
      clearInterval(progressInterval);
      setUploading(false);
      setTimeout(() => setProgress(0), 1000);
    }
  };

  const handleButtonClick = () => {
    fileInputRef.current?.click();
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  return (
    <div className={styles.container}>
      <div
        className={`${styles.dropzone} ${dragActive ? styles.active : ''}`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={handleButtonClick}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv,.xlsx,.json"
          onChange={handleFileChange}
          className={styles.fileInput}
        />

        <div className={styles.dropzoneContent}>
          <svg className={styles.icon} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
          </svg>
          <p className={styles.mainText}>
            {file ? file.name : 'Drop your dataset here or click to browse'}
          </p>
          <p className={styles.subText}>
            {file
              ? `Size: ${formatFileSize(file.size)}`
              : 'Supports CSV, XLSX, JSON files'
            }
          </p>
        </div>
      </div>

      {progress > 0 && (
        <div className={styles.progressBar}>
          <div className={styles.progressFill} style={{ width: `${progress}%` }} />
        </div>
      )}

      <div className={styles.actions}>
        {file && !uploading && (
          <Button
            variant="outline"
            onClick={() => {
              setFile(null);
              if (fileInputRef.current) {
                fileInputRef.current.value = '';
              }
            }}
          >
            Cancel
          </Button>
        )}
        <Button
          variant="primary"
          onClick={handleUpload}
          disabled={!file || uploading}
          loading={uploading}
          fullWidth={!file}
        >
          {uploading ? 'Uploading...' : 'Upload Dataset'}
        </Button>
      </div>
    </div>
  );
};

export default UploadDataset;