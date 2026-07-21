# Finitum Web Frontend

Frontend for [Finitum](../README.md), built with React Router v7 (framework mode) + TypeScript + Tailwind, running on Bun.

## Setup

```bash
bun install
bun run dev        # dev server (expects the API at VITE_API_URL, default http://localhost:9090)
```

Other scripts:

```bash
bun run build      # production build
bun run start      # serve the production build
bun run typecheck  # react-router typegen + tsc
bun run lint       # eslint
```

## Stack

- **React 19** + **React Router v7** (framework mode, file routes)
- **TypeScript**, **Tailwind CSS**
- **TanStack Query** for server state
- **React Hook Form + Zod** for forms
- **Axios** API client with JWT handling

## Structure

```
app/
├── routes/         # File routes: home, guide, login, signup, dashboard, profile, privacy, terms
├── components/     # Shared components (auth forms, layout, expenses)
├── lib/            # API client (api.ts), query client, category helpers
├── types/          # TypeScript types
└── root.tsx        # App shell
```

Key routes:

- `home.tsx` -- public landing page
- `guide.tsx` -- how-it-works onboarding (forwarding setup overview)
- `profile.tsx` -- the email-forwarding setup flow (ingest address, Gmail confirmation capture, filter generator) and account settings
- `dashboard.tsx` -- transactions and analytics

## Backend integration

The frontend talks to the FastAPI backend (`VITE_API_URL`). Auth uses JWT (signup/signin) with optional Google sign-in (login only -- no Gmail access). The bank list and forwarding-filter senders come from `GET /banks`, which is derived from the parser definitions in `../src/parsers/regex.json`.
