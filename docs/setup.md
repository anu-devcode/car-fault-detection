# Local setup and data

Use Python 3.10+ and Node.js 22. Run Python commands from the checkout root.

```bash
python -m venv .venv
source .venv/bin/activate
# PowerShell: .\.venv\Scripts\Activate.ps1
# Optional CPU-only PyTorch, before installing the package:
python -m pip install torch --index-url https://download.pytorch.org/whl/cpu
python -m pip install -e '.[dev,training]'
python scripts/check_model.py
python -m uvicorn backend:app --host 127.0.0.1 --port 8000
```

In a second terminal, run `npm ci` then `npm run dev` inside `frontend/`. Set
`NEXT_PUBLIC_API_URL` in `frontend/.env.local` when the API is elsewhere. It is a public build-time
setting, so changing it in hosting requires rebuilding the frontend.

Python settings come from the process environment. Export values explicitly, configure them in
your hosting provider, or use Uvicorn's `--env-file` option with its optional dotenv dependency.
The example env files do not load themselves.

## Dataset layout

**No recordings are included.** The existing pipeline accepts WAV files and uses their immediate
parent directory as the source label. Existing organized data can have intermediate folders:

```text
data/
  train/
    idle state/
      normal_engine_idle/*.wav
      bad_ignition/*.wav
  test/
    idle state/
      normal_engine_idle/*.wav
      bad_ignition/*.wav
```

The inventory command also reports other audio extensions as candidates, but the training
loader currently discovers WAV only. A candidate filename is not proof of decodable audio.

For unsplit source folders under `data/`, `python organize_dataset.py` copies a stratified 80/20
train/test split. The loader then splits 10% of the training partition for validation. Existing
splits are reused. These are file-level splits; they do not enforce separation by vehicle/session.
A reliable future evaluation must group related recordings before splitting.

`python merge_unprocessed_data.py` imports locally supplied AI Mechanic exports and selected
engine-idle recordings from `UNPROCESSED_DATA_DIR`. It does not download data. The original
source URLs, licenses, and recording metadata are not present; establish these before reuse.

```bash
car-fault-dataset --directory /path/to/data
# Set MODELS_DIR to a separate directory to preserve the bundled model.
python main.py
```

Training requires data; model artifacts are not a substitute. See [audit](audit.md) for the
six model labels and limitations of the historical metrics.
