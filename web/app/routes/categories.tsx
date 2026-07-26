import { Link } from 'react-router';
import { Navbar } from '../components/layout/Navbar';
import { CategoryManager } from '../components/categories/CategoryManager';

export default function CategoriesPage() {
  return (
    <div className="min-h-screen bg-gray-900">
      <Navbar />
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="mb-8">
          <Link to="/profile" className="text-sm text-blue-400 hover:text-blue-300 transition-colors">
            ← Back to settings
          </Link>
          <h1 className="text-3xl font-bold text-white mt-2">Manage Categories</h1>
        </div>
        <CategoryManager />
      </div>
    </div>
  );
}
