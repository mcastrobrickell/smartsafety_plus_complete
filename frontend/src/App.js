import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { Toaster } from "./components/ui/sonner";

// Pages
import LandingPage from "./pages/LandingPage";
import LoginPage from "./pages/LoginPage";
import DashboardPage from "./pages/DashboardPage";
import Scan360Page from "./pages/Scan360Page";
import EPPPage from "./pages/EPPPage";
import IncidentsPage from "./pages/IncidentsPage";
import FindingsPage from "./pages/FindingsPage";
import UsersPage from "./pages/UsersPage";
import ProfilesPage from "./pages/ProfilesPage";
import SuperAdminPage from "./pages/SuperAdminPage";
import ProceduresPage from "./pages/ProceduresPage";
import RiskMatrixPage from "./pages/RiskMatrixPage";
import ConfigPage from "./pages/ConfigPage";
import FormsPage from "./pages/FormsPage";
import InvestigationPage from "./pages/InvestigationPage";
import EPPDeliveriesPage from "./pages/EPPDeliveriesPage";

// Protected Route Component
const ProtectedRoute = ({ children, adminOnly = false, superadminOnly = false }) => {
  const { isAuthenticated, loading, user } = useAuth();
  
  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="spinner"></div>
      </div>
    );
  }
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (superadminOnly && user?.role !== 'superadmin') {
    return <Navigate to="/dashboard" replace />;
  }

  if (adminOnly && user?.role !== 'admin' && user?.role !== 'superadmin') {
    return <Navigate to="/dashboard" replace />;
  }
  
  return children;
};

// Public Route (redirect if authenticated)
const PublicRoute = ({ children }) => {
  const { isAuthenticated, loading, user } = useAuth();
  
  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="spinner"></div>
      </div>
    );
  }
  
  if (isAuthenticated) {
    if (user?.role === 'superadmin') {
      return <Navigate to="/superadmin" replace />;
    }
    return <Navigate to="/dashboard" replace />;
  }
  
  return children;
};

function AppRoutes() {
  return (
    <Routes>
      {/* Public Routes */}
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={
        <PublicRoute>
          <LoginPage />
        </PublicRoute>
      } />
      
      {/* Super Admin Route */}
      <Route path="/superadmin" element={
        <ProtectedRoute superadminOnly>
          <SuperAdminPage />
        </ProtectedRoute>
      } />
      
      {/* Protected Routes */}
      <Route path="/dashboard" element={
        <ProtectedRoute>
          <DashboardPage />
        </ProtectedRoute>
      } />
      <Route path="/scan360" element={
        <ProtectedRoute>
          <Scan360Page />
        </ProtectedRoute>
      } />
      <Route path="/epp" element={
        <ProtectedRoute>
          <EPPPage />
        </ProtectedRoute>
      } />
      <Route path="/epp/entregas" element={
        <ProtectedRoute>
          <EPPDeliveriesPage />
        </ProtectedRoute>
      } />
      <Route path="/incidents" element={
        <ProtectedRoute>
          <IncidentsPage />
        </ProtectedRoute>
      } />
      <Route path="/findings" element={
        <ProtectedRoute>
          <FindingsPage />
        </ProtectedRoute>
      } />
      <Route path="/users" element={
        <ProtectedRoute adminOnly>
          <UsersPage />
        </ProtectedRoute>
      } />
      <Route path="/profiles" element={
        <ProtectedRoute adminOnly>
          <ProfilesPage />
        </ProtectedRoute>
      } />
      <Route path="/procedures" element={
        <ProtectedRoute>
          <ProceduresPage />
        </ProtectedRoute>
      } />
      <Route path="/risk-matrix" element={
        <ProtectedRoute>
          <RiskMatrixPage />
        </ProtectedRoute>
      } />
      <Route path="/config" element={
        <ProtectedRoute adminOnly>
          <ConfigPage />
        </ProtectedRoute>
      } />
      <Route path="/forms" element={
        <ProtectedRoute>
          <FormsPage />
        </ProtectedRoute>
      } />
      <Route path="/investigation/:investigationId" element={
        <ProtectedRoute>
          <InvestigationPage />
        </ProtectedRoute>
      } />
      
      {/* Catch all */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <AppRoutes />
        <Toaster position="top-right" richColors closeButton />
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
