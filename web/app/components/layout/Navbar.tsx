import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useNavigate, Link } from 'react-router';
import { authApi } from '../../lib/api';

export function Navbar() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const { data: user } = useQuery({
    queryKey: ['me'],
    queryFn: authApi.getMe,
    retry: false,
  });

  const handleLogout = async () => {
    await authApi.logout();
    queryClient.clear();
    navigate('/login');
  };

  return (
    <nav className="bg-gray-900 text-white p-4 border-b border-gray-800">
      <div className="max-w-7xl mx-auto flex justify-between items-center">
        <div className="flex items-center gap-6">
          <Link to="/dashboard" className="text-xl font-bold hover:text-gray-300 transition-colors">
            Finitum
          </Link>
          <div className="flex gap-4">
            <Link
              to="/dashboard"
              className="text-sm text-gray-300 hover:text-white transition-colors"
            >
              Dashboard
            </Link>
            <Link
              to="/profile"
              className="text-sm text-gray-300 hover:text-white transition-colors"
            >
              Profile
            </Link>
            <Link
              to="/categories"
              className="text-sm text-gray-300 hover:text-white transition-colors"
            >
              Categories
            </Link>
          </div>
        </div>
        <div className="flex items-center gap-4">
          {user && <span className="text-sm text-gray-300">{user.username}</span>}
          <button
            onClick={handleLogout}
            className="px-4 py-2 bg-red-600 hover:bg-red-700 rounded text-sm"
          >
            Logout
          </button>
        </div>
      </div>
    </nav>
  );
}
