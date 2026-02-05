import { Link } from 'react-router-dom';
import { authApi } from '../lib/api';

const GoogleIcon = () => (
  <svg className="w-5 h-5" viewBox="0 0 24 24">
    <path
      fill="#4285F4"
      d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
    />
    <path
      fill="#34A853"
      d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
    />
    <path
      fill="#FBBC05"
      d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
    />
    <path
      fill="#EA4335"
      d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
    />
  </svg>
);

export function LandingPage() {
  const handleGoogleLogin = () => {
    window.location.href = authApi.getGoogleAuthUrl();
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Navigation */}
      <nav className="max-w-7xl mx-auto px-4 py-6 flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold">Finitum</h1>
          <span className="text-sm text-gray-400">Personal Finance Manager</span>
        </div>
        <div className="flex gap-4">
          <Link
            to="/login"
            className="px-4 py-2 text-gray-300 hover:text-white transition-colors"
          >
            Login
          </Link>
          <Link
            to="/signup"
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded transition-colors"
          >
            Sign Up
          </Link>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="max-w-7xl mx-auto px-4 py-12 text-center">
        <h2 className="text-5xl font-bold mb-6">
          Track Your Expenses
          <span className="block text-blue-400">Automatically</span>
        </h2>
        <p className="text-xl text-gray-400 max-w-2xl mx-auto mb-10">
          Finitum connects to your Gmail and automatically extracts transaction data
          from bank notifications. No more manual entry.
        </p>
        <div className="flex flex-col items-center gap-4">
          <div className="flex gap-4">
            <Link
              to="/guide"
              className="px-8 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg text-lg font-medium transition-colors"
            >
              Get Started
            </Link>
            <Link
              to="/login"
              className="px-8 py-3 bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded-lg text-lg font-medium transition-colors"
            >
              Login
            </Link>
          </div>
          <button
            onClick={handleGoogleLogin}
            className="flex items-center gap-2 px-6 py-2 bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded-lg transition-colors"
          >
            <GoogleIcon />
            <span>Continue with Google</span>
          </button>
        </div>
      </section>

      {/* Features Section */}
      <section className="max-w-7xl mx-auto px-4 py-16">
        <div className="grid md:grid-cols-3 gap-8">
          <div className="bg-gray-800 p-6 rounded-lg">
            <div className="text-3xl mb-4">📧</div>
            <h3 className="text-xl font-semibold mb-2">Gmail Integration</h3>
            <p className="text-gray-400">
              Securely connect your Gmail to automatically import transactions from bank emails.
            </p>
          </div>
          <div className="bg-gray-800 p-6 rounded-lg">
            <div className="text-3xl mb-4">📊</div>
            <h3 className="text-xl font-semibold mb-2">Visual Analytics</h3>
            <p className="text-gray-400">
              See where your money goes with intuitive charts and spending breakdowns.
            </p>
          </div>
          <div className="bg-gray-800 p-6 rounded-lg">
            <div className="text-3xl mb-4">🔒</div>
            <h3 className="text-xl font-semibold mb-2">Privacy First</h3>
            <p className="text-gray-400">
              No raw emails stored. Only extracted transaction data is saved securely.
            </p>
          </div>
        </div>
      </section>

      {/* About Section - Required for Google OAuth Verification */}
      <section className="max-w-4xl mx-auto px-4 py-12">
        <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-6">
          <h2 className="text-2xl font-bold mb-4 text-white">About Finitum</h2>
          <div className="text-gray-300 leading-relaxed space-y-3 text-sm">
            <p>
              <strong className="text-white">Finitum</strong> is a personal finance management application that helps you
              automatically track expenses without manual data entry.
            </p>
            <p>
              It connects securely to your Gmail using Google OAuth 2.0 to read bank notification emails,
              extracts transaction data (amounts, dates, merchants), and presents them in an organized dashboard
              with visual analytics.
            </p>
            <p>
              <strong className="text-white">Privacy:</strong> Finitum only reads emails from recognized bank senders.
              No raw email content is stored - only extracted financial data is saved to your account.
            </p>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="max-w-7xl mx-auto px-4 py-8 border-t border-gray-800">
        <div className="flex flex-col md:flex-row justify-between items-center gap-4 text-gray-400 text-sm">
          <div className="text-center md:text-left">
            <span className="font-semibold text-white">Finitum</span>
            <span className="mx-2">|</span>
            <span>Personal Finance Manager</span>
          </div>
          <div className="flex gap-6">
            <Link to="/guide" className="hover:text-white transition-colors">
              Guide
            </Link>
            <Link to="/privacy" className="hover:text-white transition-colors">
              Privacy Policy
            </Link>
            <Link to="/terms" className="hover:text-white transition-colors">
              Terms of Service
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
