# Security Policy

## Reporting a vulnerability

Please **do not open a public issue** for security problems.

Report vulnerabilities privately to **finitumapp@gmail.com** (or via [GitHub private vulnerability reporting](https://github.com/richardhapb/finitum/security/advisories/new) if enabled). Include steps to reproduce and, if possible, an assessment of impact.

You should receive an acknowledgement within a few days. Please give us a reasonable window to ship a fix before public disclosure.

## Scope

Especially interesting areas:

- The inbound email webhook (`POST /ingest/email`): HMAC signature verification, ingest-token handling, deduplication.
- Authentication: JWT handling, Google sign-in flow.
- Anything that could expose one user's transactions or ingest address to another user.

## Supported versions

Finitum is pre-1.0: only the latest `main` is supported with security fixes.
