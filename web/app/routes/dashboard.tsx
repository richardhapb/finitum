import { Navbar } from "../components/layout/Navbar";
import { ExpenseForm } from "../components/expenses/ExpenseForm";
import { ExpenseList } from "../components/expenses/ExpenseList";
import { ExpenseChart } from "../components/expenses/ExpenseChart";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useSearchParams } from "react-router";
import { authApi, emailApi } from "../lib/api";

export default function DashboardPage() {
  const [searchParams] = useSearchParams();
  const gmailScanStatus = searchParams.get("gmail_scan");

  const { data: user } = useQuery({
    queryKey: ["me"],
    queryFn: authApi.getMe,
  });

  const manualScan = useMutation({
    mutationFn: emailApi.triggerScan,
  });

  const showAuthWarning = user && (!user.has_google_credentials || !user.is_google_credentials_valid);
  const showGmailScopeWarning = user && user.has_google_credentials && user.is_google_credentials_valid && !user.has_gmail_scope;
  const canTriggerVerificationScan = Boolean(user?.verification_scan_enabled);

  const oauthScanFeedback = (() => {
    if (gmailScanStatus === "queued") {
      return {
        title: "Initial Gmail scan queued",
        body: "We started scanning your Gmail for supported bank transaction emails. Imported expenses will appear shortly.",
        tone: "bg-emerald-500/10 border-emerald-500 text-emerald-300",
      };
    }
    if (gmailScanStatus === "skipped_scope") {
      return {
        title: "Gmail scan not started",
        body: "You signed in without Gmail read-only permission, so automatic import is disabled.",
        tone: "bg-yellow-500/10 border-yellow-500 text-yellow-300",
      };
    }
    if (gmailScanStatus === "queue_error") {
      return {
        title: "Gmail scan could not start",
        body: "Google login succeeded, but queueing the initial scan failed. Please try again from the dashboard.",
        tone: "bg-red-500/10 border-red-500 text-red-300",
      };
    }
    return null;
  })();

  return (
    <div className="min-h-screen bg-gray-900">
      <Navbar />
      <div className="max-w-7xl mx-auto px-4 py-8">
        {oauthScanFeedback && (
          <div className={`mb-6 border rounded-lg p-4 ${oauthScanFeedback.tone}`}>
            <h3 className="font-semibold">{oauthScanFeedback.title}</h3>
            <p className="text-sm text-gray-200 mt-1">{oauthScanFeedback.body}</p>
          </div>
        )}

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

        {canTriggerVerificationScan && (
          <div className="mb-6 bg-indigo-500/10 border border-indigo-500 rounded-lg p-4 flex items-center justify-between gap-4">
            <div>
              <h3 className="font-semibold text-indigo-300">Google verification mode</h3>
              <p className="text-sm text-gray-300">
                Use this manual trigger only for OAuth app verification testing.
              </p>
              {manualScan.isSuccess && (
                <p className="text-xs text-emerald-300 mt-2">
                  {manualScan.data.msg}. Task id: {manualScan.data.task_id}
                </p>
              )}
              {manualScan.isError && (
                <p className="text-xs text-red-300 mt-2">
                  {(manualScan.error as Error).message}
                </p>
              )}
            </div>
            <button
              type="button"
              onClick={() => manualScan.mutate()}
              disabled={
                manualScan.isPending ||
                !user?.has_google_credentials ||
                !user?.is_google_credentials_valid ||
                !user?.has_gmail_scope
              }
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-700 disabled:cursor-not-allowed text-white font-medium rounded transition-colors whitespace-nowrap"
            >
              {manualScan.isPending ? "Queueing..." : "Scan Gmail now"}
            </button>
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
