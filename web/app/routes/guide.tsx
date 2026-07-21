import { Link } from "react-router";

const GITHUB_URL = "https://github.com/richardhapb/finitum";

export default function GuidePage() {
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
        <h1 className="text-4xl font-bold mb-4">How Finitum Works</h1>
        <p className="text-xl text-gray-400">
          Your bank already emails you every transaction. Set up a one-time
          forwarding rule and Finitum does the rest -- no bank credentials, no
          inbox access.
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
                  Sign up with your email and password, or use Google sign-in.
                  Either way, Finitum never accesses your email account --
                  Google is used for login only.
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
                <h2 className="text-xl font-semibold mb-2">
                  Get Your Forwarding Address
                </h2>
                <p className="text-gray-400 mb-4">
                  In your profile, select your bank and copy your personal
                  Finitum address (it looks like{" "}
                  <code className="text-green-300">u-a1b2c3@finitum.app</code>).
                  This address is unique to you -- emails sent to it land in
                  your account and nowhere else.
                </p>
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
                <h2 className="text-xl font-semibold mb-2">
                  Set Up the Forwarding Rule
                </h2>
                <p className="text-gray-400 mb-4">
                  In Gmail, add your Finitum address as a forwarding address and
                  create a filter that forwards only your bank's notification
                  emails. Your profile page walks you through it: Gmail's
                  confirmation request is captured automatically, and the filter
                  for your bank's senders is generated for you -- just copy and
                  paste.
                </p>
                <div className="bg-gray-700/50 rounded p-4 text-sm text-gray-300">
                  <strong className="text-white">You stay in control:</strong>
                  <ul className="mt-2 space-y-1 list-disc list-inside">
                    <li>Only emails matching your filter are forwarded</li>
                    <li>Finitum never connects to your inbox or your bank</li>
                    <li>Remove the rule at any time to stop instantly</li>
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
                <h2 className="text-xl font-semibold mb-2">
                  Transactions Appear Automatically
                </h2>
                <p className="text-gray-400 mb-4">
                  From then on, every bank notification is parsed the moment it
                  arrives. The raw email is processed in real time and never
                  stored -- only the extracted transaction data.
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

          {/* Step 5 */}
          <div className="bg-gray-800 rounded-lg p-6">
            <div className="flex items-start gap-4">
              <div className="flex-shrink-0 w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center font-bold text-lg">
                5
              </div>
              <div>
                <h2 className="text-xl font-semibold mb-2">
                  Explore Your Dashboard
                </h2>
                <p className="text-gray-400 mb-4">
                  See all your expenses in one place, and add manual entries for
                  cash or anything not covered by email.
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

          {/* Bank not supported */}
          <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-2">
              Bank not supported yet?
            </h2>
            <p className="text-gray-400">
              Finitum is open source and bank parsers are community-built --
              adding a bank takes a JSON definition and a few sample emails, no
              core code.{" "}
              <a
                href={`${GITHUB_URL}/blob/main/docs/adding-a-bank.md`}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-400 hover:underline"
              >
                Read the guide
              </a>{" "}
              or{" "}
              <a
                href={`${GITHUB_URL}/issues/new?template=add-a-bank.yml`}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-400 hover:underline"
              >
                request your bank on GitHub
              </a>
              .
            </p>
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
            <a
              href={GITHUB_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-white transition-colors"
            >
              GitHub
            </a>
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
