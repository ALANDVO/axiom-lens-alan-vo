/**
 * Axiom Lens - Main App component with routing.
 */
import { Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from './components/layout';
import { Dashboard } from './pages/Dashboard';
import { Analyses } from './pages/Analyses';
import { AnalysisDetail } from './pages/AnalysisDetail';
import { NewAnalysis } from './pages/NewAnalysis';
import { useAuth } from './auth/AuthProvider';

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();
  
  if (isLoading) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-64">
          <div className="spinner" role="status" aria-label="Loading..." />
        </div>
      </Layout>
    );
  }
  
  return isAuthenticated ? <>{children}</> : <Navigate to="/api/v1/auth/login" replace />;
}

function PublicRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();
  
  if (isLoading) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-64">
          <div className="spinner" role="status" aria-label="Loading..." />
        </div>
      </Layout>
    );
  }
  
  return !isAuthenticated ? <>{children}</> : <Navigate to="/" replace />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<PrivateRoute><Dashboard /></PrivateRoute>} />
      <Route path="/analyses" element={<PrivateRoute><Analyses /></PrivateRoute>} />
      <Route path="/analyses/new" element={<PrivateRoute><NewAnalysis /></PrivateRoute>} />
      <Route path="/analyses/:id" element={<PrivateRoute><AnalysisDetail /></PrivateRoute>} />
      <Route path="/analyses/:id/edit" element={<PrivateRoute><AnalysisDetail /></PrivateRoute>} />
      <Route path="/login" element={<PublicRoute><div>Redirecting...</div></PublicRoute>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}