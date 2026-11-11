# Car Fault Detection

Development repository: [anu-devcode/car-fault-detection](https://github.com/anu-devcode/car-fault-detection).
The full application was imported and refactored from
[A3M-IS/car-fault-detection](https://github.com/A3M-IS/car-fault-detection), with its history retained.

Audio-based engine fault classification using a PyTorch CRNN, a FastAPI inference service,
and a Next.js dashboard. This is a research prototype; a prediction does not establish
whether a vehicle is safe to drive.

**Dataset: no dataset is included in this repository.** A model checkpoint and a six-class
label encoder are tracked. Their architecture compatibility and local inference were checked;
diagnostic accuracy cannot be verified without the original labeled test recordings.

**Production:** the [Vercel frontend](https://car-fault-detection.vercel.app/) responds, but
its configured Railway API returned HTTP 404 “Application not found” during the audit.
See [repository, production, and dataset findings](docs/audit.md).

## Car care hub development

The local `/hub` now includes symptom-aware recommendations, safe immediate owner actions,
Ethiopia garage/towing map searches, optional photo-based vehicle candidates, and manual vehicle
profiles with official source links. These are development features; photo matches are not
verified identities and audio results do not establish driving safety.

A real research-only transfer-learning pilot has been run on 96 sourced recordings. Pretrained
AST features performed better than the existing CRNN features in that small comparison, but
neither result establishes production readiness. See [development progress](docs/development-progress.md),
[the research model card](research/transfer-comparison/MODEL_CARD.md), and [the roadmap](docs/roadmap.md).
Git pushes are for development; hosting deployment guards remain enabled.

## Repository layout

```text
src/car_fault_detection/
  api/             # FastAPI application factory and upload/health routes
  audio/           # Shared audio decoding, augmentation, and mel features
  ml/              # CRNN architecture, inference, data loaders, training, evaluation
  data/            # Dataset inventory, organization, and source-data merge utilities
  config.py        # Shared model settings and environment-based paths
  training.py      # Offline training orchestration
  visualization.py # Training plots and existing WAV discovery helper
frontend/src/
  pages/           # Next.js route entry points
  features/diagnostics/ # Dashboard presentation, session hook, and tab panels
  lib/             # API client, WAV conversion, confidence/statistics utilities
  styles/          # Global UI styles
apps/              # Optional local Streamlit application
scripts/           # Dataset and checkpoint inspection commands
tests/             # Python API, inventory, and inference tests
frontend/tests/    # Frontend confidence/statistics tests
docs/              # Architecture, setup, deployment, and audit
models/            # Existing tracked checkpoint and label encoder
.github/workflows/ # Backend and frontend CI checks
```

Root Python modules remain compatibility entry points. `backend:app`, `python main.py`, and
`streamlit run app.py` keep their command names after installing the package. New code belongs
in the package and frontend feature modules. Generated Python caches and editor state are no
longer tracked.

## Quick start

Use Python 3.10+ and Node.js 22. From the repository root:

```bash
python -m venv .venv
source .venv/bin/activate
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn backend:app --host 127.0.0.1 --port 8000
```

In another terminal:

```bash
cd frontend
npm ci
# Optional: copy .env.example to .env.local and set NEXT_PUBLIC_API_URL
npm run dev
```

The frontend defaults to `http://localhost:8000`. Open `http://localhost:3000`.
Environment examples are templates: configure/export variables explicitly or pass an env file;
Python code does not load `.env` automatically. For CPU-only PyTorch, installation instructions
are in [setup](docs/setup.md).

## Dataset and model checks

```bash
car-fault-dataset
car-fault-dataset --directory /path/to/recordings
python scripts/check_model.py
```

Inventory reports candidate file counts, source labels, and split directories without claiming
that contents or labels are valid. No training dataset is downloaded automatically.
The checkpoint validator rejects incompatible weights instead of silently using random
parameters. Read [dataset findings](docs/audit.md) before training.

## Offline training and local dashboard

```bash
python -m pip install -e '.[training]'
# Supply licensed, labeled data first; see docs/setup.md
python organize_dataset.py
python main.py

# Optional Streamlit adapter
python -m pip install -e '.[dashboard]'
streamlit run apps/streamlit_app.py
```

Training overwrites model artifacts in `MODELS_DIR`; use a separate artifact directory when
experimenting. No retraining was performed as part of the refactor.

## Validation

```bash
python -m pip install -e '.[dev,training]'
ruff check .
ruff format --check .
python -m pytest -q
cd frontend
npm run lint
npm run format:check
npm test
npm run build
```

API confidence is a softmax score from the loaded model, not calibrated accuracy. The dashboard
shows actual request timing and session counts; missing confidence is shown as unavailable.
It does not simulate uptime, prediction scores, load charts, or encryption controls.

See [architecture](docs/architecture.md), [setup](docs/setup.md), and
[deployment](docs/deployment.md). Original project claims are archived under `docs/history/`
and are not a substitute for reproducible evaluation reports.
