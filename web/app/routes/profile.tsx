import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Navbar } from "../components/layout/Navbar";
import { authApi, banksApi, ingestApi } from "../lib/api";

export default function ProfilePage() {
  const queryClient = useQueryClient();
  const [isEditing, setIsEditing] = useState(false);
  const [username, setUsername] = useState("");
  const [bank, setBank] = useState("");
  const [copied, setCopied] = useState<string | null>(null);

  const { data: user, isLoading } = useQuery({
    queryKey: ["me"],
    queryFn: authApi.getMe,
    // Poll so the "waiting for first email" status flips live once mail arrives.
    refetchInterval: (query) =>
      query.state.data?.forwarding_active ? false : 15000,
  });

  const { data: banks = [] } = useQuery({
    queryKey: ["banks"],
    queryFn: banksApi.getAll,
  });

  const { data: ingest } = useQuery({
    queryKey: ["ingest-address"],
    queryFn: ingestApi.getAddress,
  });

  const { data: confirmationData } = useQuery({
    queryKey: ["ingest-confirmation"],
    queryFn: ingestApi.getConfirmation,
    // The Gmail confirmation mail lands shortly after the user adds the filter.
    refetchInterval: user?.forwarding_active ? false : 10000,
  });

  const ingestAddress = ingest?.address ?? user?.ingest_address ?? null;
  const confirmation = confirmationData?.confirmation ?? null;
  const senders = banks.find((b) => b.id === user?.bank)?.senders ?? [];
  // Gmail search-bar query: paste into the search box, then "Create filter".
  const gmailFilter = senders.length ? `from:(${senders.join(" OR ")})` : "";

  const copy = (label: string, value: string) => {
    navigator.clipboard.writeText(value);
    setCopied(label);
    setTimeout(() => setCopied(null), 1500);
  };

  const updateMutation = useMutation({
    mutationFn: authApi.updateMe,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["me"] });
      setIsEditing(false);
    },
    onError: (error: any) => {
      alert(error.response?.data?.detail || "Update failed");
    },
  });

  const handleEdit = () => {
    if (user) {
      setUsername(user.username);
      setBank(user.bank);
      setIsEditing(true);
    }
  };

  const handleSave = () => {
    updateMutation.mutate({ username, bank });
  };

  const handleCancel = () => {
    setIsEditing(false);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-900">
        <Navbar />
        <div className="max-w-4xl mx-auto px-4 py-8">
          <p className="text-gray-400">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900">
      <Navbar />
      <div className="max-w-4xl mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold text-white mb-8">Profile Settings</h1>

        {/* Email Forwarding Setup */}
        <div className="bg-gray-800 rounded-lg p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-white">Email Forwarding</h2>
            <div className="flex items-center gap-2">
              {user?.forwarding_active ? (
                <>
                  <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                  <span className="text-sm text-gray-300">Receiving emails</span>
                </>
              ) : (
                <>
                  <div className="w-3 h-3 bg-yellow-500 rounded-full animate-pulse"></div>
                  <span className="text-sm text-gray-300">Waiting for first email…</span>
                </>
              )}
            </div>
          </div>

          <p className="text-gray-400 text-sm mb-4">
            Forward your bank notification emails to your personal Finitum address.
            No Gmail access required — set up one filter and you're done.
          </p>

          {/* Step 1: ingest address */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-400 mb-1">
              1. Your forwarding address
            </label>
            <div className="flex gap-2">
              <code className="flex-1 px-3 py-2 bg-gray-900 border border-gray-700 rounded text-green-300 text-sm overflow-x-auto">
                {ingestAddress ?? "Loading…"}
              </code>
              <button
                onClick={() => ingestAddress && copy("address", ingestAddress)}
                disabled={!ingestAddress}
                className="px-3 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded text-sm transition-colors disabled:opacity-50"
              >
                {copied === "address" ? "Copied!" : "Copy"}
              </button>
            </div>
          </div>

          {/* Step 2: add the forwarding address */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-400 mb-1">
              2. Add it as a forwarding address
            </label>
            <p className="text-gray-500 text-xs">
              In Gmail → Settings → “Forwarding and POP/IMAP” → “Add a forwarding
              address”, paste the address from step 1. Gmail sends it a confirmation
              request, which is captured automatically below.
            </p>
          </div>

          {/* Step 3: confirmation */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-400 mb-1">
              3. Confirm the forwarding request
            </label>
            {confirmation ? (
              <div className="px-3 py-2 bg-gray-900 border border-green-700 rounded text-sm">
                {confirmation.url ? (
                  <a
                    href={confirmation.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-green-300 underline break-all"
                  >
                    Click here to confirm forwarding
                  </a>
                ) : (
                  <span className="text-green-300">
                    Confirmation code: <span className="font-mono">{confirmation.code}</span>
                  </span>
                )}
              </div>
            ) : (
              <p className="text-gray-500 text-sm">
                Gmail will send a confirmation request — it'll appear here automatically.
              </p>
            )}
          </div>

          {/* Step 4: forwarding filter via Gmail search */}
          {gmailFilter && (
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-1">
                4. Forward your bank emails
              </label>
              <p className="text-gray-500 text-xs mb-1">
                Paste this into the Gmail search bar, click the filter icon (the
                sliders ⚙ on the right of the search bar) to open search options,
                then “Create filter” → check “Forward it to” → your address.
              </p>
              <div className="flex gap-2">
                <code className="flex-1 px-3 py-2 bg-gray-900 border border-gray-700 rounded text-blue-300 text-sm overflow-x-auto">
                  {gmailFilter}
                </code>
                <button
                  onClick={() => copy("filter", gmailFilter)}
                  className="px-3 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded text-sm transition-colors"
                >
                  {copied === "filter" ? "Copied!" : "Copy"}
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Google Sign-in Status */}
        <div className="bg-gray-800 rounded-lg p-6 mb-6">
          <h2 className="text-xl font-semibold text-white mb-4">Google Sign-in</h2>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              {user?.has_google_credentials ? (
                user?.is_google_credentials_valid ? (
                  <>
                    <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                    <span className="text-gray-300">Connected and active</span>
                  </>
                ) : (
                  <>
                    <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
                    <span className="text-gray-300">Connection expired - please reconnect</span>
                  </>
                )
              ) : (
                <>
                  <div className="w-3 h-3 bg-red-500 rounded-full"></div>
                  <span className="text-gray-300">Not connected</span>
                </>
              )}
            </div>
            <a
              href={authApi.getGoogleAuthUrl()}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors flex items-center gap-2"
            >
              <svg className="w-5 h-5" viewBox="0 0 24 24">
                <path
                  fill="#fff"
                  d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                />
                <path
                  fill="#fff"
                  d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                />
                <path
                  fill="#fff"
                  d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                />
                <path
                  fill="#fff"
                  d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                />
              </svg>
              {user?.has_google_credentials ? "Reconnect Google" : "Sign in with Google"}
            </a>
          </div>
        </div>

        {/* Account Settings */}
        <div className="bg-gray-800 rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-white">Account Settings</h2>
            {!isEditing && (
              <button
                onClick={handleEdit}
                className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded transition-colors"
              >
                Edit
              </button>
            )}
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-1">Email</label>
              <p className="text-white">{user?.email}</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-400 mb-1">Username</label>
              {isEditing ? (
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              ) : (
                <p className="text-white">{user?.username}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-400 mb-1">Bank</label>
              {isEditing ? (
                <select
                  value={bank}
                  onChange={(e) => setBank(e.target.value)}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {banks.map((b) => (
                    <option key={b.id} value={b.id}>
                      {b.name}
                    </option>
                  ))}
                </select>
              ) : (
                <p className="text-white">
                  {banks.find((b) => b.id === user?.bank)?.name || user?.bank}
                </p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-400 mb-1">Last Sync</label>
              <p className="text-white">
                {user?.last_update ? new Date(user.last_update).toLocaleString() : "Never"}
              </p>
            </div>

            {isEditing && (
              <div className="flex gap-3 pt-4">
                <button
                  onClick={handleSave}
                  disabled={updateMutation.isPending}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors disabled:bg-gray-600"
                >
                  {updateMutation.isPending ? "Saving..." : "Save Changes"}
                </button>
                <button
                  onClick={handleCancel}
                  className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded transition-colors"
                >
                  Cancel
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
