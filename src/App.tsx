import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './context/AuthContext';
import RoleGuard from './components/ui/RoleGuard';

// Lazy-load pages for code-splitting
const Login = React.lazy(() => import('./pages/Login'));
const Register = React.lazy(() => import('./pages/Register'));
const AdminDashboard = React.lazy(() => import('./pages/admin/AdminDashboard'));
const HRDashboard = React.lazy(() => import('./pages/hr/HRDashboard'));
const EmployeeDashboard = React.lazy(() => import('./pages/employee/EmployeeDashboard'));
const ManagerDashboard = React.lazy(() => import('./pages/manager/ManagerDashboard'));
const CandidatePortal = React.lazy(() => import('./pages/candidate/CandidatePortal'));
const VoiceInterview = React.lazy(() => import('./pages/candidate/VoiceInterview'));

const LoadingFallback = () => (
  <div className="min-h-screen bg-black flex items-center justify-center">
    <div className="flex flex-col items-center gap-4">
      <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-amber-400 to-amber-600 flex items-center justify-center text-black font-extrabold text-2xl shadow-amber-glow animate-pulse">
        H
      </div>
      <p className="text-zinc-500 text-xs font-semibold uppercase tracking-widest">Loading…</p>
    </div>
  </div>
);

const App: React.FC = () => {
  const { user, loading } = useAuth();

  if (loading) return <LoadingFallback />;

  return (
    <BrowserRouter>
      <React.Suspense fallback={<LoadingFallback />}>
        <Routes>
          {/* Public routes */}
          <Route path="/login" element={user ? <Navigate to={`/${user.role === 'manager' ? 'manager' : user.role}`} replace /> : <Login />} />
          <Route path="/register" element={user ? <Navigate to="/candidate" replace /> : <Register />} />

          {/* Protected dashboard routes */}
          <Route path="/admin" element={<RoleGuard allowedRoles={['admin']}><AdminDashboard /></RoleGuard>} />
          <Route path="/hr" element={<RoleGuard allowedRoles={['hr']}><HRDashboard /></RoleGuard>} />
          <Route path="/employee" element={<RoleGuard allowedRoles={['employee']}><EmployeeDashboard /></RoleGuard>} />
          <Route path="/manager" element={<RoleGuard allowedRoles={['manager']}><ManagerDashboard /></RoleGuard>} />
          <Route path="/candidate" element={<RoleGuard allowedRoles={['candidate']}><CandidatePortal /></RoleGuard>} />
          <Route path="/candidate/interview/:sessionId" element={<RoleGuard allowedRoles={['candidate']}><VoiceInterview /></RoleGuard>} />

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </React.Suspense>
    </BrowserRouter>
  );
};

export default App;
