import { Navbar } from "../components/layout/Navbar";
import { ExpenseForm } from "../components/expenses/ExpenseForm";
import { ExpenseList } from "../components/expenses/ExpenseList";
import { ExpenseChart } from "../components/expenses/ExpenseChart";
import { useQuery } from "@tanstack/react-query";
import { authApi } from "../lib/api";

export default function DashboardPage() {
  const { data: user } = useQuery({
    queryKey: ["me"],
    queryFn: authApi.getMe,
  });

  const showAuthWarning = user && (!user.has_google_credentials || !user.is_google_credentials_valid);
  const showGmailScopeWarning = user && user.has_google_credentials && user.is_google_credentials_valid && !user.has_gmail_scope;

  return (
    <div className="min-h-screen bg-gray-900">
      <Navbar />
      <div className="max-w-7xl mx-auto px-4 py-8">
        {showGmailScopeWarning && (
          <div className="mb-6 bg-blue-500/10 border border-blue-500 rounded-lg p-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="text-2xl">📧</span>
              <div>
                <h3 className="font-semibold text-blue-400">Gmail access not granted</h3>
                <p className="text-sm text-gray-300">
                  You connected Google but didn't grant Gmail access. Expenses won't be imported automatically from your bank emails.
                </p>
              </div>
            </div>
            <a
              href={authApi.getGoogleAuthUrl()}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded transition-colors whitespace-nowrap"
            >
              Grant Gmail access
            </a>
          </div>
        )}
        {showAuthWarning && (
          <div className="mb-6 bg-yellow-500/10 border border-yellow-500 rounded-lg p-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="text-2xl">⚠️</span>
              <div>
                <h3 className="font-semibold text-yellow-500">Google Account Connection Required</h3>
                <p className="text-sm text-gray-300">
                  {!user.has_google_credentials
                    ? "Connect your Google account to automatically import expenses."
                    : "Your Google session has expired. Please reconnect to continue importing expenses."}
                </p>
              </div>
            </div>
            <a
              href={authApi.getGoogleAuthUrl()}
              className="px-4 py-2 bg-yellow-500 hover:bg-yellow-600 text-black font-medium rounded transition-colors"
            >
              {!user.has_google_credentials ? "Connect Google" : "Reconnect Google"}
            </a>
          </div>
        )}

        {/* Charts section - full width */}
        <div className="mb-6">
          <ExpenseChart />
        </div>

        {/* Form + List section */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Add expense form - takes 1 column */}
          <div className="lg:col-span-1">
            <ExpenseForm />
          </div>

          {/* Expense list - takes 2 columns */}
          <div className="lg:col-span-2">
            <ExpenseList />
          </div>
        </div>
      </div>
    </div>
  );
}
