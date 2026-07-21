import type { MetaFunction } from "react-router";

export const meta: MetaFunction = () => [
  { title: "Privacy Policy - Finitum" },
  { name: "description", content: "Finitum privacy policy. Learn how Finitum handles the bank emails you forward and protects your privacy." },
];

export default function Privacy() {
  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <div className="max-w-4xl mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold mb-6">Privacy Policy</h1>
        <article className="space-y-4 text-gray-300 leading-relaxed">
          <p>Finitum respects your privacy.</p>

          <p>
            Finitum does not access your email account or your bank. It only
            processes the emails you explicitly forward to your personal
            Finitum address, for the sole purpose of extracting financial
            transaction information from bank notification emails. You control
            what is forwarded and can stop at any time by removing the
            forwarding rule.
          </p>

          <p>
            No raw email content is permanently stored.
            Only extracted transaction data (amount, merchant, date, category)
            is saved to provide financial analytics.
          </p>

          <p>
            Google sign-in is optional and used for authentication only.
            Finitum does not request access to Gmail or to any email content.
          </p>

          <h2 className="text-xl font-semibold text-white pt-4">Data Retention and Deletion</h2>

          <p>
            Forwarded emails are processed in real time and are not stored
            beyond the immediate processing session. Only the derived
            transaction data (amount, merchant, date, category) is retained in
            your account for as long as your account remains active.
          </p>

          <p>
            You may request deletion of all your data at any time by contacting{" "}
            <a href="mailto:finitumapp@gmail.com" className="text-blue-400 hover:underline">
              finitumapp@gmail.com
            </a>
            . Upon receiving a deletion request, all stored transaction data and
            associated account information will be permanently deleted within 30
            days. You may also delete your account directly within the
            application, which will immediately remove all stored data.
          </p>

          <p>
            Tokens granted by Google for sign-in are stored securely and are
            revoked and deleted when you disconnect your Google account or
            delete your Finitum account.
          </p>

          <p>Finitum does not sell, share, or use user data for advertising purposes.</p>

          <p>
            Authentication is handled securely using JWT tokens, with optional
            Google OAuth2 sign-in. Sensitive credentials and tokens are stored
            securely.
          </p>

          <p>
            Finitum is open-source software (MIT license); you can inspect
            exactly how your data is handled, or self-host your own instance,
            at{" "}
            <a
              href="https://github.com/richardhapb/finitum"
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-400 hover:underline"
            >
              github.com/richardhapb/finitum
            </a>
            .
          </p>

          <p>
            If you have questions about this policy, contact:{" "}
            <a href="mailto:finitumapp@gmail.com" className="text-blue-400 hover:underline">
              finitumapp@gmail.com
            </a>
          </p>
        </article>
      </div>
    </div>
  );
}
