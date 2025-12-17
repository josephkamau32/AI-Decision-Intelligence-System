import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import DatasetOverview from './pages/DatasetOverview';
import ModelPerformance from './pages/ModelPerformance';
import FeatureImportance from './pages/FeatureImportance';
import VisualInsights from './pages/VisualInsights';
import CopilotChat from './pages/CopilotChat';
import './App.css';

function App() {
  return (
    <Router>
      <div className="App">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/dataset-overview" element={<DatasetOverview />} />
          <Route path="/model-performance" element={<ModelPerformance />} />
          <Route path="/feature-importance" element={<FeatureImportance />} />
          <Route path="/visual-insights" element={<VisualInsights />} />
          <Route path="/copilot" element={<CopilotChat />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;