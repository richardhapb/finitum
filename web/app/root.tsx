import {
  Links,
  Meta,
  Outlet,
  Scripts,
  ScrollRestoration,
  isRouteErrorResponse,
  Link,
} from "react-router";
import type { LinksFunction, MetaFunction, Route } from "react-router";
import { QueryClientProvider } from "@tanstack/react-query";
import { queryClient } from "./lib/queryClient";
import "./index.css";

export const links: LinksFunction = () => [
  { rel: "icon", type: "image/svg+xml", href: "/icon.svg" },
];

export const meta: MetaFunction = () => [
  { charSet: "utf-8" },
  { name: "viewport", content: "width=device-width, initial-scale=1.0" },
  { title: "Finitum - Personal Finance Manager | Automatic Expense Tracking" },
  {
    name: "description",
    content:
      "Finitum is a personal finance manager that automatically tracks your expenses by parsing bank notification emails from your Gmail. View spending analytics, categorize transactions, and take control of your finances with privacy-first design.",
  },
  { name: "author", content: "Finitum" },
  { name: "application-name", content: "Finitum" },
  { property: "og:type", content: "website" },
  { property: "og:url", content: "https://finitum.richardhapb.com/" },
  {
    property: "og:title",
    content: "Finitum - Personal Finance Manager | Automatic Expense Tracking",
  },
  {
    property: "og:description",
    content:
      "Finitum is a personal finance manager that automatically tracks your expenses by parsing bank notification emails from your Gmail. View spending analytics and take control of your finances.",
  },
  { property: "og:site_name", content: "Finitum" },
  { property: "twitter:card", content: "summary_large_image" },
  { property: "twitter:url", content: "https://finitum.richardhapb.com/" },
  {
    property: "twitter:title",
    content: "Finitum - Personal Finance Manager | Automatic Expense Tracking",
  },
  {
    property: "twitter:description",
    content:
      "Finitum is a personal finance manager that automatically tracks your expenses by parsing bank notification emails from your Gmail. View spending analytics and take control of your finances.",
  },
  {
    name: "google-site-verification",
    content: "vtLmYhHw3tnSUsKvoXibjp5MkzNya-F4BADaFx0kkW0",
  },
];

export function Layout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <Meta />
        <Links />
      </head>
      <body>
        {children}
        <ScrollRestoration />
        <Scripts />
      </body>
    </html>
  );
}

export default function Root() {
  return (
    <QueryClientProvider client={queryClient}>
      <Outlet />
    </QueryClientProvider>
  );
}

export function ErrorBoundary({ error }: Route.ErrorBoundaryProps) {
  if (isRouteErrorResponse(error)) {
    return (
      <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-6xl font-bold mb-4">{error.status}</h1>
          <p className="text-xl text-gray-400 mb-8">
            {error.status === 404 ? "Page not found" : error.statusText}
          </p>
          <Link
            to="/"
            className="px-6 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
          >
            Go Home
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-4xl font-bold mb-4">Something went wrong</h1>
        <p className="text-gray-400 mb-8">An unexpected error occurred</p>
        <Link
          to="/"
          className="px-6 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
        >
          Go Home
        </Link>
      </div>
    </div>
  );
}
