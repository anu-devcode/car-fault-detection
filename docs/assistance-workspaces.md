# Car Care assistance workspaces

Open `/dashboard` after starting the frontend and API.

- **Driver.** Create an account, search published garages by city or within 25 km, call a listed garage, and send a private request to a mechanic who is accepting work. Use My requests to track replies or cancel an open request. A callback number is optional.
- **Mechanic.** A one-time invitation links the account to a garage. Set availability, accept or decline incoming requests, and mark accepted jobs complete. A callback number appears after accepting.
- **Administrator.** Create and edit garage listings, publish or unpublish them, review availability, and grant mechanic access with 24-hour, email-bound invitations. Share invitations privately.

## Local setup

Install the project dependencies, create the database schema, and provision the first administrator. The password prompt keeps credentials out of shell history.

```powershell
$env:PLATFORM_DATABASE_URL = 'sqlite:///data/assistance.sqlite3'
$env:PLATFORM_WEB_ORIGIN = 'http://localhost:3000'
New-Item -ItemType Directory -Force data | Out-Null
python -m car_fault_detection.platform.setup init
python -m car_fault_detection.platform.setup admin --email operator@example.com --name Operator
python -m uvicorn backend:app --host 127.0.0.1 --port 8000
```

In another terminal, run `npm run dev` from `frontend/` and open
`http://localhost:3000/dashboard`. Add listings from the admin account.
The directory is empty until an admin publishes garages.

## Server configuration

SQLite is for local and single-instance development. For a shared service, install
`.[postgres]`, use a managed PostgreSQL connection for `PLATFORM_DATABASE_URL`, and run the
schema initializer once as an explicit setup step. Configure `PLATFORM_WEB_ORIGIN` to the exact
HTTPS frontend origin. Set `PLATFORM_API_URL` on the frontend host at build time to route its
same-origin assistance requests to the API. Leave platform settings unset to run only the original tools.

The database stores Argon2id password hashes, hashes of expiring session and invite tokens,
and role-scoped requests. Auth and directory writes check the configured request origin.
GPS for nearby search is used for that query. Garage coordinates are part of the published listing.
Availability records what a mechanic last selected. A submitted request has no guaranteed
response time, and no message is delivered outside the app.

Before public operation, configure TLS and trusted proxy access, request throttling at the edge,
email verification and recovery, administrator MFA, backups, and an operational process for
verifying garage listings and responding to abuse. Measure database search and request throughput
with representative traffic before choosing a rollout size. The initial SQLite end-to-end check
does not establish live PostgreSQL performance.
