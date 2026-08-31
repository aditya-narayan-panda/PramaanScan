# PramaanScan Frontend

A production-ready React + TypeScript frontend for PramaanScan, connected to every endpoint
exposed by the analyzed FastAPI backend. **No mock or fabricated data is used anywhere** — every
screen either calls a real endpoint or, in the couple of spots the backend genuinely doesn't
support yet, says so honestly instead of inventing numbers.

## Stack

React 18 · Vite · TypeScript · Tailwind CSS · shadcn/ui (Radix primitives) · React Router 6 ·
Axios · TanStack Query · React Hook Form + Zod · Framer Motion · Recharts · `qr-scanner` / `qrcode`

## Getting started

```bash
npm install
cp .env.example .env        # point VITE_API_BASE_URL at your running backend
npm run dev
```

The app expects the backend at `http://127.0.0.1:8000/api/v1` by default — change
`VITE_API_BASE_URL` in `.env` if yours runs elsewhere. CORS must be enabled on the backend for
the dev origin (`http://localhost:5177`).

```bash
npm run build      # type-checks (tsc -b) then builds to dist/
npm run preview    # preview the production build locally
```

## What's real vs. what's an honest placeholder

Every endpoint the backend exposes is wired up:

| Area | Endpoints used |
|---|---|
| Public verification | `POST /verify/file`, `GET /verify/communication/{id}` |
| Provenance lookup | `GET /communications/{id}`, `.../versions`, `.../current` |
| Registration | `POST /communications`, `PUT/DELETE /communications/{id}` |
| Listing | `GET /communications` (paginated, searchable) |
| QR | `GET /communications/{id}/qr`, `.../qr/image` |
| Auth | `POST /auth/admin/login`, `/auth/institution/login`, `/auth/refresh`, `/auth/logout`, `GET /auth/me` |
| Dashboard | `GET /dashboard/stats` |
| Analytics | `GET /analytics/overview`, `/analytics/verifications`, `/analytics/media` |
| Admin | full CRUD on `/admin/institutions`, `/admin/users` |
| Logs | `GET /verification/logs`, `GET /admin/audit-logs` |
| Key management | `POST /revocation/key`, `GET /revocation/key/{id}` |
| Profile | `GET/PUT /profile`, `POST /profile/password`, `GET/PUT /settings` |

Two things are intentionally **not** faked:

- **Institution editing** — the backend supports listing/creating/suspending institutions but not
  a full "edit" form; the UI only exposes what's supported.
- **Signing itself** — by backend design, private Ed25519 keys never touch the API. The
  "Upload & Sign" page computes a real SHA-256 of your file client-side (Web Crypto API) and lets
  you paste in the signature your institution's offline signing process produced — it does not,
  and cannot, fabricate a signature.

If a future backend version adds an endpoint this frontend doesn't yet call, look in
`src/api/*.ts` — each file is a thin, typed wrapper per resource, so wiring up new endpoints is a
small, isolated change.

## Folder structure

```
src/
  api/          typed axios wrappers, one file per backend resource
  components/
    ui/         shadcn-style primitives (button, card, dialog, table, ...)
    layout/     navbars, sidebars, portal shells
    common/     StatusBadge, RiskGauge, EmptyState, ProtectedRoute, ...
    qr/         camera scanner + QR image generator
    verification/  file dropzone, result cards, media analysis panel
  context/      Auth + Theme providers
  hooks/        toast, local-activity tracking
  pages/
    public/     landing, verify, result, provenance, about, contact, faq
    auth/       admin + institution login
    institution/  dashboard, upload & sign, generate QR, documents, logs, analytics, profile
    admin/      dashboard, institutions, users, documents, logs, keys, analytics, audit, settings
    shared/     profile settings + analytics view reused by both portals
    errors/     404 / 403 / 500
  App.tsx       route tree
  main.tsx      providers + entry point
```

## Auth model

JWT access + refresh tokens, stored in `localStorage`. An Axios response interceptor
transparently refreshes an expired access token once via `/auth/refresh`; if that fails, the user
is logged out and redirected to the correct portal's login page. Routes are guarded by role
(`ADMIN` vs `AUTHORITY`) via `ProtectedRoute`.

## Theming

Light / dark / system, persisted to `localStorage`, applied via a `.dark` class on `<html>` and
CSS custom properties (see `src/index.css`). Primary color is Government Blue (`#1D4ED8`).
