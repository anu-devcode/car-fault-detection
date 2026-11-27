# Development progress — 11 November 2026

This is an Ethiopia-first development prototype. Production remains deferred.

## Implemented and checked

- `/hub`: symptom-based care guidance; immediate owner actions; stop/towing escalation;
  source links; a user-entered city or consented browser location for external Google Maps
  garage/assistance searches. Map listings are not verified or booked by this app.
- Audio results include initial guidance. Explicit urgent symptoms override normal audio
  through `/care/triage`. Guidance is deterministic, not a generated mechanic diagnosis;
  local professional review is still required.
- Photo upload/camera input: optional pretrained EfficientNet-B4 adapter, pinned to
  `Jordo23/vehicle-classifier@7a0a0ee5584202b5eba858cf7464f5ca6b7341b3`. It returns five possible
  identities. No automatic identity verification, VIN/engine/trim inference, or all-car coverage.
- Manual vehicle entry accepts arbitrary makes/models, including makes not covered by the photo
  model. Owner-resource links are curated manufacturer entry points; unknown specifications stay
  unknown. A photo candidate must be reviewed/edited before resource lookup.
- Real research audio import, decoded-audio/group split checks, frozen-encoder transfer training,
  saved heads, source revisions/hashes and metrics. AST is a promising pilot candidate, not the
  declared best automotive model. See the [research model card](../research/transfer-comparison/MODEL_CARD.md).
- Default API still uses the original six-class checkpoint. Research AST requires explicit local
  opt-in. Neither data-rights review nor regional model-quality evaluation has passed release gates.

## Local run

```bash
python -m pip install -e '.[dev,training,transfer,vision]'
# For CPU hosts install matching CPU torch/torchvision wheels first if needed:
# python -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
# Set HF_HOME to a project-owned cache directory.
python scripts/install_vehicle_model.py
```

To keep the original audio model and enable the optional photo model:

```bash
VISION_MODEL_DIR="$PWD/models/vehicle-photo" python -m uvicorn backend:app --port 8000
```

For the local research AST adapter, first run the import/training commands in the model card,
then add `AUDIO_MODEL_BACKEND=research_ast`, `ALLOW_RESEARCH_MODELS=true`, and
`RESEARCH_AUDIO_MODEL_DIR=research/transfer-comparison`. Use the same `HF_HOME` cache used when
training. These variables are process settings; `.env.example` is not loaded automatically.

Run `npm ci` and `npm run dev` in `frontend/`, then open `/hub` on the local frontend.
New large external checkpoints and raw recordings are ignored by Git. The small trained head,
provenance and evaluation reports are committed. Do not redistribute restricted source audio.

## Test evidence

- 29 Python tests: original APIs plus urgent symptom overrides, split leakage, research-model
  opt-in, optional photo operation, file limits/decoding, and manual-source lookup.
- 7 frontend tests: multipart/timeout/errors, confidence/statistics and regional map links.
- Ruff, ESLint, Prettier and Next.js production build succeeded locally.
- Real Chromium checked care escalation, towing search, permission-based geolocation, actual
  pretrained photo-model execution, candidate review, manufacturer links and 390px mobile layout.
  The photo smoke fixture was synthetic and establishes execution only, not identity accuracy.
- The locally trained AST head ran through the real `/predict` endpoint on an imported recording.
- The 96-recording exploratory comparison produced AST test 15/18 and CRNN-only test 12/18.
  Both have false negatives and important source/pretraining overlap risks; no model was promoted.

## Next implementation stages

1. Establish reusable training-data rights and obtain mechanic-reviewed Ethiopian recordings.
   Use `docs/data-collection.md` for the recording/group/consent requirements. Increase sample
   coverage and source diversity before further model selection.
2. Evaluate temporal windows and sound-quality/unknown-input rejection; calibrate scores on a
   dedicated split; compare additional pretrained models, then unfreeze upper layers if warranted.
   Reserve an independent release test set before tuning.
3. Validate photo recognition on the local fleet, including Ethiopian imports, EVs and unsupported
   models. Add broader source-backed catalogue data, market/VIN confirmation and service schedules.
4. Review guidance with Ethiopian mechanics, add reviewed localization, and integrate a real
   garage-provider directory with verified capabilities/contact details. Maps search is the initial adapter.
5. Resolve dependency advisories, privacy/retention/authentication and performance requirements.
   Production is a separate stage that the user has explicitly postponed.

Low-score or ambiguous photo outputs recommend manual entry and hide candidate selection in
the UI. This conservative score/margin heuristic is not calibrated recognition accuracy or a
car-presence detector; high-scoring non-car/unsupported inputs may still be wrong.

## Photo inspection and recording improvements

The existing hub accepts a camera photo or a file. Use make/model matching on a whole-car
photo. Use visible-clue inspection for views of tyres, dashboard symbols, body panels, and
accessible components. The inspection model returns a restricted vocabulary; the app pairs
supported clues with follow-up checks and keeps vehicle matching separate. The operator must
review actual performance on representative photos before releasing the feature.

The visible-clue checklist also works with the API when automatic recognition is unavailable.
Choose the area and check only clues you can see. A photo suggestion selects a possible area,
and every clue starts unchecked. Follow-up guidance appears for selected clues. Downloaded text
notes include the selected observations and their follow-up steps for a mechanic. The download
is created in the browser and contains no photograph.

Start Ollama on the API host with a local vision model, for example by running
`ollama pull gemma3:4b` after installing Ollama. Install the Python `vision` extra, set
`PHOTO_INSPECTION_MODEL=gemma3:4b` and restart the API. The backend uses the loopback host
and sends resized image pixels without the original EXIF metadata. The app does not save
the inspection result between sessions. See [Ollama vision](https://docs.ollama.com/capabilities/vision)
and [structured outputs](https://docs.ollama.com/capabilities/structured-outputs).

Microphone capture now stops automatically after ten seconds, releases the microphone,
and asks for a fresh recording when the clip is too short, quiet, or heavily clipped.
The research trainer supports `--windows 3` to average embeddings from beginning, middle,
and end windows per recording. Split separation is checked at recording level before
windowing. Compare with `--windows 1` on the same manifest and use a distinct `--output`
directory for each run. Existing AST research checkpoints default to one central window.

### Expanded sound experiment

Both candidates used the same 132 real recordings from the pinned research dataset
(96 training, 18 validation, and 18 test). The head is trained over the bundled CRNN's frozen
features. The earlier 96-recording pilot used 60 training recordings. The extra 36 clips
went to training while the evaluation selection stayed fixed.

| CRNN input | Validation macro F1 | Test macro F1 | Correct on test | Engine knock detected |
| --- | ---: | ---: | ---: | ---: |
| Centre second | 0.816 | 0.648 | 13 / 18 | 1 / 6 |
| Beginning, middle, and end | 1.000 | 0.816 | 15 / 18 | 3 / 6 |

The three-window head classified one engine-knock clip as healthy and two as misfire.
This is a small research comparison on a previously used evaluation split with unverified
original data rights and no independent mechanic-labeled set. The bundled six-class model
remains the default. Research audio, metrics and weights from these commands stay under
the ignored local `data/` directory.

```bash
python scripts/import_research_pilot.py --allow-research-only --train-per-class 32 --eval-per-class 6 --output data/research/expanded
python scripts/train_transfer_pilot.py --dataset data/research/expanded --output data/research/crnn-windows-1 --encoders crnn --windows 1
python scripts/train_transfer_pilot.py --dataset data/research/expanded --output data/research/crnn-windows-3 --encoders crnn --windows 3
AUDIO_MODEL_BACKEND=research_crnn ALLOW_RESEARCH_MODELS=true python -m uvicorn backend:app --port 8000
```
