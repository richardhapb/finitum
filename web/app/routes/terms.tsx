import type { MetaFunction } from "react-router";

export const meta: MetaFunction = () => [
  { title: "Terms of Service - Finitum" },
  { name: "description", content: "Finitum terms of service." },
];

export default function Terms() {
  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <div className="max-w-4xl mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold mb-6">Terms of Service</h1>
        <article className="space-y-4 text-gray-300 leading-relaxed">
          <p>By using Finitum, you agree to use the service responsibly.</p>

          <p>
            Finitum is provided on an "as is" basis without warranties of any kind.
            The service may be modified or discontinued at any time.
          </p>

          <p>
            Finitum is not responsible for financial decisions made based on
            the information provided by the application.
          </p>

          <p>
            By using the service, you agree to the collection and use of data
            as described in the Privacy Policy.
          </p>

          <p>
            Contact:{" "}
            <a href="mailto:finitumapp@gmail.com" className="text-blue-400 hover:underline">
              finitumapp@gmail.com
            </a>
          </p>
        </article>
      </div>
    </div>
  );
}
