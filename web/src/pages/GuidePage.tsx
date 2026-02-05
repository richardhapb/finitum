import { Link } from 'react-router-dom';

export function GuidePage() {
  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Navigation */}
      <nav className="max-w-7xl mx-auto px-4 py-6 flex justify-between items-center">
        <Link to="/" className="text-2xl font-bold">Finitum</Link>
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

      {/* Header */}
      <section className="max-w-4xl mx-auto px-4 py-12">
        <h1 className="text-4xl font-bold mb-4">Getting Started</h1>
        <p className="text-xl text-gray-400">
          Follow these steps to start tracking your expenses automatically.
        </p>
      </section>

      {/* Steps */}
      <section className="max-w-4xl mx-auto px-4 pb-16">
        <div className="space-y-8">
          {/* Step 1 */}
          <div className="bg-gray-800 rounded-lg p-6">
            <div className="flex items-start gap-4">
              <div className="flex-shrink-0 w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center font-bold text-lg">
                1
              </div>
              <div>
                <h2 className="text-xl font-semibold mb-2">Create an Account</h2>
                <p className="text-gray-400 mb-4">
                  Sign up with your email and password, or use Google to create an account instantly.
                </p>
                <Link
                  to="/signup"
                  className="inline-block px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded transition-colors text-sm"
                >
                  Create Account
                </Link>
              </div>
            </div>
          </div>

          {/* Step 2 */}
          <div className="bg-gray-800 rounded-lg p-6">
            <div className="flex items-start gap-4">
              <div className="flex-shrink-0 w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center font-bold text-lg">
                2
              </div>
              <div>
                <h2 className="text-xl font-semibold mb-2">Connect Your Gmail</h2>
                <p className="text-gray-400 mb-4">
                  Link your Google account to allow Finitum to read your bank notification emails.
                  We only access emails from financial institutions to extract transaction data.
                </p>
                <div className="bg-gray-700/50 rounded p-4 text-sm text-gray-300">
                  <strong className="text-white">What we access:</strong>
                  <ul className="mt-2 space-y-1 list-disc list-inside">
                    <li>Bank transaction notification emails</li>
                    <li>Payment confirmations from supported banks</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>

          {/* Step 3 */}
          <div className="bg-gray-800 rounded-lg p-6">
            <div className="flex items-start gap-4">
              <div className="flex-shrink-0 w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center font-bold text-lg">
                3
              </div>
              <div>
                <h2 className="text-xl font-semibold mb-2">Automatic Import</h2>
                <p className="text-gray-400 mb-4">
                  Once connected, Finitum automatically scans your inbox for transaction emails
                  and extracts the relevant data: amount, merchant, date, and category.
                </p>
                <div className="bg-gray-700/50 rounded p-4 text-sm text-gray-300">
                  <strong className="text-white">Extracted data:</strong>
                  <ul className="mt-2 space-y-1 list-disc list-inside">
                    <li>Transaction amount</li>
                    <li>Merchant or vendor name</li>
                    <li>Date and time</li>
                    <li>Auto-detected category</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>

          {/* Step 4 */}
          <div className="bg-gray-800 rounded-lg p-6">
            <div className="flex items-start gap-4">
              <div className="flex-shrink-0 w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center font-bold text-lg">
                4
              </div>
              <div>
                <h2 className="text-xl font-semibold mb-2">View Your Dashboard</h2>
                <p className="text-gray-400 mb-4">
                  Head to your dashboard to see all your expenses in one place. View charts,
                  filter by category, and understand your spending patterns.
                </p>
                <ul className="text-gray-400 space-y-2">
                  <li className="flex items-center gap-2">
                    <span className="text-green-400">✓</span>
                    Spending breakdown by category
                  </li>
                  <li className="flex items-center gap-2">
                    <span className="text-green-400">✓</span>
                    Monthly and weekly trends
                  </li>
                  <li className="flex items-center gap-2">
                    <span className="text-green-400">✓</span>
                    Full transaction history
                  </li>
                </ul>
              </div>
            </div>
          </div>

          {/* Step 5 */}
          <div className="bg-gray-800 rounded-lg p-6">
            <div className="flex items-start gap-4">
              <div className="flex-shrink-0 w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center font-bold text-lg">
                5
              </div>
              <div>
                <h2 className="text-xl font-semibold mb-2">Add Manual Expenses</h2>
                <p className="text-gray-400 mb-4">
                  For cash transactions or expenses not captured by email, you can manually
                  add entries directly from your dashboard.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* CTA */}
        <div className="mt-12 text-center">
          <p className="text-gray-400 mb-4">Ready to take control of your finances?</p>
          <Link
            to="/signup"
            className="inline-block px-8 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg text-lg font-medium transition-colors"
          >
            Get Started Now
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="max-w-7xl mx-auto px-4 py-8 border-t border-gray-800">
        <div className="flex justify-between items-center text-gray-400 text-sm">
          <Link to="/" className="hover:text-white transition-colors">Finitum</Link>
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
