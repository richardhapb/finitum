import type { MetaFunction } from "react-router";

export const meta: MetaFunction = () => [
  { title: "Privacy Policy - Finitum" },
  { name: "description", content: "Finitum privacy policy. Learn how Finitum handles your Gmail data and protects your privacy." },
];

export default function Privacy() {
  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <div className="max-w-4xl mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold mb-6">Privacy Policy</h1>
        <article className="space-y-4 text-gray-300 leading-relaxed">
          <p>Finitum respects your privacy.</p>

          <p>
            Finitum only accesses Gmail data with the user's explicit consent, and
            only for the purpose of extracting financial transaction information
            from bank notification emails.
          </p>

          <p>
            No raw email content is permanently stored.
            Only extracted transaction data (amount, merchant, date, category)
            is saved to provide financial analytics.
          </p>

          <p>Finitum does not sell, share, or use user data for advertising purposes.</p>

          <p>
            Authentication is handled securely using Google OAuth2 and JWT tokens.
            Sensitive credentials and tokens are stored securely.
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
