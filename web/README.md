# Finitum Web Frontend

Finance tracker frontend built with React + TypeScript + Tailwind.

## Setup

```bash
# Install dependencies
bun install

# Create .env file
cp .env.example .env

# Run dev server
bun run dev
```

## Stack

- **React 19** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool (Bun runtime)
- **Tailwind CSS** - Styling
- **React Router** - Routing
- **TanStack Query** - Server state management
- **React Hook Form + Zod** - Form validation
- **Axios** - HTTP client

## Project Structure

```
src/
├── components/
│   ├── auth/           # Login/Signup forms
│   ├── expenses/       # Expense list and form
│   └── layout/         # Navbar, ProtectedRoute
├── pages/              # Page components
├── lib/                # API client, query config
└── types/              # TypeScript types
```

## Key Features

- JWT authentication with refresh token support
- Protected routes
- Expense CRUD operations
- Form validation with Zod
- Automatic API error handling
- Google OAuth integration

## Backend Integration

The frontend expects the FastAPI backend running at `http://localhost:9090` (configurable via `VITE_API_URL`).

Required backend endpoints:
- `POST /signup` - User registration
- `POST /signin` - User login
- `POST /refresh` - Token refresh (YOU NEED TO ADD THIS)
- `GET /me` - Get current user
- `GET /expenses` - List expenses
- `POST /expenses` - Create expense
- `GET /google-authorize` - Google OAuth
