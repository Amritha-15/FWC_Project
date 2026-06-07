import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

interface RoleGuardProps {
  children: React.ReactNode;
  allowedRoles: ('admin' | 'hr' | 'employee' | 'manager' | 'candidate')[];
}

export const RoleGuard: React.FC<RoleGuardProps> = ({ children, allowedRoles }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-black">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-amber-500 border-t-transparent"></div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (!allowedRoles.includes(user.role)) {
    // If authenticated but role isn't allowed, send back to login
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};

export default RoleGuard;
