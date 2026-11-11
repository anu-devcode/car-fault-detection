# Deployment

The current Vercel frontend is reachable, but the configured Railway address returned an
application-not-found response. Changes here have not been deployed. Account-level logs,
service/domain settings, and environment configuration must be inspected to establish the cause.

## GitHub source

Development continues in `anu-devcode/car-fault-detection` on `main`. The full application was
imported from A3M-IS with source history retained. Select the development repository in Vercel
and Railway before deploying from it; a Git remote change does not transfer hosting projects.

## Backend: Railway (or another Python host)

- Repository root: project root.
- Install: `python -m pip install -r requirements.txt`.
- Start: use `railway.json`/`Procfile`, both targeting `backend:app` with one Gunicorn worker.
- Set `ALLOWED_ORIGINS=https://car-fault-detection.vercel.app`; include other required origins
  as comma-separated values. Localhost is the default for development only.
- Provide `models/best_model.pth` and `models/label_encoder.joblib`, or point `MODELS_DIR` at
  the artifact directory. Only use trusted, validated checkpoint and joblib files.
- The included artifacts match the code, but their measured accuracy is not reproduced here.
- For a CPU host, use the official CPU PyTorch wheel before package installation as described
  in setup; avoid downloading GPU dependencies unnecessarily.

Verify `GET /health` (liveness) and `GET /ready` (prediction readiness) separately. Railway's
healthcheck points to `/health`; a successful deployment healthcheck alone does not mean that
inference is available. Check logs for initialization failures rather than repeatedly reloading
weights during requests.

## Frontend: Vercel

- Root directory stays **`frontend`**.
- Install `npm ci`; build `npm run build`.
- Set `NEXT_PUBLIC_API_URL` to the restored API origin before building.
- Rebuild after changing that value. The browser bundle currently deployed points to
  `https://car-fault-detection-production.up.railway.app`.

Before promotion, verify real health/readiness, a known labeled recording, malformed audio,
upload limits, backend errors, and CORS from the intended frontend origin. The local smoke test
uses synthetic audio and establishes code execution only; it is not model-quality validation.
See [audit](audit.md) for exact observations and outstanding limitations.
