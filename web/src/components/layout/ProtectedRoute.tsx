import { Navigate, Outlet } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { authApi } from '../../lib/api';

export function ProtectedRoute() {
  const { isLoading, isError } = useQuery({
    queryKey: ['session'],
    queryFn: authApi.validateSession,
    retry: false,
  });

  if (isLoading) {
    return <div>Loading...</div>;
  }

  if (isError) {
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
}
