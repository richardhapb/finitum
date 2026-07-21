import { Link } from "react-router";
import { useQuery } from "@tanstack/react-query";
import { authApi, banksApi } from "../lib/api";

const GITHUB_URL = "https://github.com/richardhapb/finitum";

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

const GitHubIcon = () => (
  <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
    <path d="M12 .5C5.65.5.5 5.65.5 12c0 5.08 3.29 9.39 7.86 10.91.58.11.79-.25.79-.55 0-.27-.01-1.17-.02-2.12-3.2.7-3.88-1.36-3.88-1.36-.52-1.33-1.28-1.68-1.28-1.68-1.04-.71.08-.7.08-.7 1.15.08 1.76 1.19 1.76 1.19 1.03 1.76 2.69 1.25 3.35.96.1-.75.4-1.25.72-1.54-2.56-.29-5.25-1.28-5.25-5.68 0-1.26.45-2.28 1.19-3.09-.12-.29-.52-1.46.11-3.05 0 0 .97-.31 3.17 1.18a11 11 0 0 1 5.78 0c2.2-1.49 3.17-1.18 3.17-1.18.63 1.59.23 2.76.11 3.05.74.81 1.19 1.83 1.19 3.09 0 4.41-2.69 5.38-5.26 5.67.41.35.77 1.05.77 2.12 0 1.53-.01 2.76-.01 3.14 0 .3.2.66.8.55A11.51 11.51 0 0 0 23.5 12C23.5 5.65 18.35.5 12 .5z" />
  </svg>
);

export default function LandingPage() {
  const handleGoogleLogin = () => {
    window.location.href = authApi.getGoogleAuthUrl();
  };

  const { data: banks = [] } = useQuery({
    queryKey: ["banks"],
    queryFn: banksApi.getAll,
  });

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Navigation */}
      <nav className="max-w-7xl mx-auto px-4 py-6 flex justify-between items-center">
        <div>
          <span className="text-2xl font-bold">Finitum</span>
          <span className="block text-sm text-gray-400">
            Open-Source Finance Tracker
          </span>
        </div>
        <div className="flex gap-4 items-center">
          <a
            href={GITHUB_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 px-4 py-2 text-gray-300 hover:text-white transition-colors"
          >
            <GitHubIcon />
            <span className="hidden sm:inline">GitHub</span>
          </a>
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
        <h1 className="text-6xl font-bold mb-4 text-blue-400">Finitum</h1>
        <p className="text-2xl text-gray-300 mb-6">
          Your bank already emails you every transaction. Finitum turns those
          emails into your finance dashboard.
        </p>

        <p className="text-xl text-gray-400 max-w-2xl mx-auto mb-10">
          Forward your bank's notification emails to your personal Finitum
          address and every purchase, withdrawal, and transfer is parsed
          automatically -- amount, merchant, date, and category. No bank
          credentials, no inbox access, no manual entry.
        </p>

        <div className="flex flex-col items-center gap-4">
          <div className="flex gap-4">
            <Link
              to="/guide"
              className="px-8 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg text-lg font-medium transition-colors"
            >
              How It Works
            </Link>
            <Link
              to="/signup"
              className="px-8 py-3 bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded-lg text-lg font-medium transition-colors"
            >
              Get Started
            </Link>
          </div>

          <button
            onClick={handleGoogleLogin}
            className="flex items-center gap-2 px-6 py-2 bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded-lg transition-colors"
          >
            <GoogleIcon />
            <span>Continue with Google</span>
          </button>
          <p className="text-xs text-gray-500">
            Google sign-in is optional and used for login only. Finitum never
            accesses your inbox.
          </p>
        </div>
      </section>

      {/* How it works, in one line */}
      <section className="max-w-4xl mx-auto px-4 pb-8">
        <div className="bg-gray-800/40 border border-gray-700 rounded-lg p-4 overflow-x-auto">
          <code className="text-sm text-gray-300 whitespace-nowrap">
            Bank email → your forwarding rule → u-…@finitum.app → parser →
            dashboard 📊
          </code>
        </div>
      </section>

      {/* Features Section */}
      <section className="max-w-7xl mx-auto px-4 py-16">
        <div className="grid md:grid-cols-3 gap-8">
          <div className="bg-gray-800 p-6 rounded-lg">
            <div className="text-3xl mb-4">📧</div>
            <h3 className="text-xl font-semibold mb-2">Email Forwarding</h3>
            <p className="text-gray-400">
              A one-time forwarding rule sends your bank notifications to your
              personal Finitum address. You choose exactly what gets forwarded
              -- Finitum never reads your inbox.
            </p>
          </div>

          <div className="bg-gray-800 p-6 rounded-lg">
            <div className="text-3xl mb-4">🌍</div>
            <h3 className="text-xl font-semibold mb-2">Open Source</h3>
            <p className="text-gray-400">
              MIT-licensed and self-hostable. Bank parsers are community-built:
              adding your bank is a JSON file and a couple of tests -- no core
              code required.
            </p>
          </div>

          <div className="bg-gray-800 p-6 rounded-lg">
            <div className="text-3xl mb-4">📊</div>
            <h3 className="text-xl font-semibold mb-2">Visual Analytics</h3>
            <p className="text-gray-400">
              Automatic categories, spending trends, and a full transaction
              history -- built from data extracted the moment each email
              arrives.
            </p>
          </div>
        </div>
      </section>

      {/* Supported banks */}
      <section className="max-w-4xl mx-auto px-4 pb-12">
        <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-6">
          <h3 className="text-2xl font-bold mb-4 text-white">Supported Banks</h3>
          {banks.length > 0 ? (
            <div className="flex flex-wrap gap-3 mb-4">
              {banks.map((b) => (
                <span
                  key={b.id}
                  className="px-3 py-1.5 bg-gray-700/70 border border-gray-600 rounded-full text-sm text-gray-200"
                >
                  {b.name}
                </span>
              ))}
            </div>
          ) : (
            <p className="text-gray-400 text-sm mb-4">Loading bank list…</p>
          )}
          <p className="text-gray-400 text-sm">
            Missing yours? Parsers are data-driven and community-contributed --{" "}
            <a
              href={`${GITHUB_URL}/blob/main/docs/adding-a-bank.md`}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-400 hover:underline"
            >
              add your bank
            </a>{" "}
            with a JSON block and a few sample emails, or{" "}
            <a
              href={`${GITHUB_URL}/issues/new?template=add-a-bank.yml`}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-400 hover:underline"
            >
              request it on GitHub
            </a>
            .
          </p>
        </div>
      </section>

      {/* About Section */}
      <section className="max-w-4xl mx-auto px-4 py-4 pb-12">
        <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-6">
          <h3 className="text-2xl font-bold mb-4 text-white">
            Privacy by Design
          </h3>
          <div className="text-gray-300 leading-relaxed space-y-3 text-sm">
            <p>
              Finitum works only with the emails you explicitly forward to it.
              There is no connection to your bank and no access to your email
              account.
            </p>
            <p>
              Forwarded emails are processed in real time: transaction data
              (amount, merchant, date, category) is extracted and stored; the
              raw email content is not.
            </p>
            <p>
              Don't want to trust a hosted service? Run it yourself -- the{" "}
              <a
                href={GITHUB_URL}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-400 hover:underline"
              >
                entire stack is open source
              </a>{" "}
              and ships with a Docker Compose setup.
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
            <span>Open-Source Finance Tracker</span>
          </div>
          <div className="flex gap-6">
            <a
              href={GITHUB_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-white transition-colors"
            >
              GitHub
            </a>
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
