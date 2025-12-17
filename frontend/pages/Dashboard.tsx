import React from 'react';
import { Link } from 'react-router-dom';
import UploadDataset from '../components/UploadDataset';

const Dashboard: React.FC = () => {
  return (
    <div>
      <h1>AI Decision Intelligence System</h1>
      <UploadDataset />
      <nav>
        <ul>
          <li><Link to="/dataset-overview">Dataset Overview</Link></li>
          <li><Link to="/model-performance">Model Performance</Link></li>
          <li><Link to="/feature-importance">Feature Importance</Link></li>
          <li><Link to="/visual-insights">Visual Insights</Link></li>
          <li><Link to="/copilot">AI Copilot</Link></li>
        </ul>
      </nav>
    </div>
  );
};

export default Dashboard;