import React, { Suspense } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider } from './context/ThemeProvider';
import { ToastProvider } from './context/ToastProvider';
import { AuthProvider } from './context/AuthContext';
import Layout from './components/Layout/Layout';
import Toast from './components/ui/Toast';
import Spinner from './components/ui/Spinner';
import ErrorBoundary from './components/ErrorBoundary';
import ProtectedRoute from './components/ProtectedRoute';

// Lazy load pages for code splitting
const LandingPage = React.lazy(() => import('./pages/LandingPage'));
const Dashboard = React.lazy(() => import('./pages/Dashboard'));
const DatasetOverview = React.lazy(() => import('./pages/DatasetOverview'));
const ModelPerformance = React.lazy(() => import('./pages/ModelPerformance'));
const FeatureImportance = React.lazy(() => import('./pages/FeatureImportance'));
const VisualInsights = React.lazy(() => import('./pages/VisualInsights'));
const CopilotChat = React.lazy(() => import('./pages/CopilotChat'));
const Login = React.lazy(() => import('./pages/Login'));
const Register = React.lazy(() => import('./pages/Register'));

// Loading fallback
const PageLoader = () => (
  <div style={{
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    height: '100vh',
    background: 'var(--bg-secondary)'
  }}>
    <Spinner size="lg" />
  </div>
);

function App() {
  return (
    <ErrorBoundary>
      <ThemeProvider>
        <ToastProvider>
          <AuthProvider>
            <Router>
              <Suspense fallback={<PageLoader />}>
                <Routes>
                  {/* Public routes - Landing & Auth */}
                  <Route path="/" element={<LandingPage />} />
                  <Route path="/login" element={<Login />} />
                  <Route path="/register" element={<Register />} />

                  {/* Protected routes - Dashboard */}
                  <Route path="/dashboard" element={
                    <ProtectedRoute>
                      <Layout>
                        <Dashboard />
                      </Layout>
                    </ProtectedRoute>
                  } />
                  <Route path="/dataset-overview" element={
                    <ProtectedRoute>
                      <Layout>
                        <DatasetOverview />
                      </Layout>
                    </ProtectedRoute>
                  } />
                  <Route path="/model-performance" element={
                    <ProtectedRoute>
                      <Layout>
                        <ModelPerformance />
                      </Layout>
                    </ProtectedRoute>
                  } />
                  <Route path="/feature-importance" element={
                    <ProtectedRoute>
                      <Layout>
                        <FeatureImportance />
                      </Layout>
                    </ProtectedRoute>
                  } />
                  <Route path="/visual-insights" element={
                    <ProtectedRoute>
                      <Layout>
                        <VisualInsights />
                      </Layout>
                    </ProtectedRoute>
                  } />
                  <Route path="/copilot" element={
                    <ProtectedRoute>
                      <Layout>
                        <CopilotChat />
                      </Layout>
                    </ProtectedRoute>
                  } />
                </Routes>
              </Suspense>
              <Toast />
            </Router>
          </AuthProvider>
        </ToastProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}

export default App;
