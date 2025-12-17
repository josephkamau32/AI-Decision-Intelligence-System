import React, { Suspense } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider } from './context/ThemeProvider';
import { ToastProvider } from './context/ToastProvider';
import Layout from './components/Layout/Layout';
import Toast from './components/ui/Toast';
import Spinner from './components/ui/Spinner';

// Lazy load pages for code splitting
const Dashboard = React.lazy(() => import('./pages/Dashboard'));
const DatasetOverview = React.lazy(() => import('./pages/DatasetOverview'));
const ModelPerformance = React.lazy(() => import('./pages/ModelPerformance'));
const FeatureImportance = React.lazy(() => import('./pages/FeatureImportance'));
const VisualInsights = React.lazy(() => import('./pages/VisualInsights'));
const CopilotChat = React.lazy(() => import('./pages/CopilotChat'));

// Loading fallback
const PageLoader = () => (
  <div style={{
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    height: '100vh'
  }}>
    <Spinner size="lg" />
  </div>
);

function App() {
  return (
    <ThemeProvider>
      <ToastProvider>
        <Router>
          <Layout>
            <Suspense fallback={<PageLoader />}>
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/dataset-overview" element={<DatasetOverview />} />
                <Route path="/model-performance" element={<ModelPerformance />} />
                <Route path="/feature-importance" element={<FeatureImportance />} />
                <Route path="/visual-insights" element={<VisualInsights />} />
                <Route path="/copilot" element={<CopilotChat />} />
              </Routes>
            </Suspense>
          </Layout>
          <Toast />
        </Router>
      </ToastProvider>
    </ThemeProvider>
  );
}

export default App;
