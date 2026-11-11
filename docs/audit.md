# Repository, production, and dataset audit

Inspected 11 November 2026. These are point-in-time source/public endpoint observations, not
Vercel/Railway account logs or an independent model-quality evaluation.

## Source of truth

The complete project is `https://github.com/A3M-IS/car-fault-detection.git`, inspected at
`edb303dee1ba3c78818e6b2a69be741f8836d133` (`main`). Its homepage matches the supplied Vercel
URL, and its frontend/API contracts match the inspected deployed application. The precise
Vercel deployment commit was not verified through hosting-account access.

The initially supplied `anu-devcode/car-fault-detection` repository contains only Python
placeholders. It is not the full deployed project's source. The main refactor applies to
**A3M-IS/car-fault-detection**, with the earlier scaffold work kept in a separate checkout.

## Production status

| Component | Observed behavior | Assessment |
| --- | --- | --- |
| Vercel frontend `/` | HTTP 200, Next.js, title `Engine Diagnostic AI` | Frontend delivery is live |
| Deployed API URL | Browser bundle points to `https://car-fault-detection-production.up.railway.app` | Separate Railway inference service is required |
| Railway `/` | HTTP 404, JSON `Application not found` | Health/model check cannot succeed at the configured address |
| Railway `/openapi.json` | Same 404 application-not-found response | No running API schema recovered from the advertised service |
| Prediction flow | Client posts multipart field `file` to `/predict` | Live inference could not be established; no recording was submitted to production |
| Original UI scores | Result `96.4%`; records randomized between 94–99% | Not derived from model predictions |
| Original UI statistics | Accuracy `94.2`, response `42ms`, uptime `100%`, static load bars | Not operational measurements |
| Original UI settings | Sensitivity, AES-256 security, and alerts only stored in local UI state | These controls do not implement the advertised behaviors |

The deployed public assets included build `jS67Bmrqfn1yXZd7t4CNw` and page chunk
`/_next/static/chunks/pages/index-41e289f15a2e85a9.js`. The source frontend already supports
`NEXT_PUBLIC_API_URL`; the deployed bundle contains the Railway URL supplied at build time.

The application-not-found response does not establish whether the Railway service was deleted,
renamed, misconfigured, or disconnected. Hosting account settings/logs are needed to determine
that. No production configuration or deployment was changed during this task.

A Chromium navigation to production was attempted but hit `ERR_CERT_AUTHORITY_INVALID` in this
managed browser environment. The public HTTP checks used inherited proxy/CA trust with TLS
verification enabled. Browser verification of the refactored local app succeeded separately.

## Dataset: no dataset available

**There are no audio recordings in this repository checkout or tracked Git tree.** `data/` and
`unprocessedData/` are ignored by Git. There are no included train/validation/test recordings,
feature tables, reproducible evaluation reports, dataset download scripts, or usable source
URLs/license records. The model files are not a dataset.

The code references:

- Existing `data/train` and `data/test` folders, with the leaf folder used as source label.
- A local `ai-mechanic-export/info.labels` dataset export.
- A local `unprocessedData/data` collection of engine-idle recordings.
- Original hardcoded Windows dataset paths. These do not exist in this cloud checkout and
  have been replaced with configurable paths in the refactored tools.

The code describes source labels such as `bad_ignition`, `dead_battery`, `normal_engine_idle`,
`low_oil`, and `serpentine_belt`. These mappings do not establish that recordings are available.
Inventory reports zero local audio files. Source provenance, licenses, recording quality,
class counts/durations, duplicate rates, and split leakage cannot be assessed without the data.

Before retraining, obtain the recordings and source metadata, verify labels/decoding, and
separate vehicles/sessions across splits. The existing pipeline uses file-level stratified
splits, so it cannot establish vehicle/session independence. Mapping background noise to
`Normal` also deserves review before asserting diagnostic reliability.

## Included model artifacts

Unlike the placeholder repository, this project tracks:

- `models/best_model.pth` (approximately 21 MB).
- `models/label_encoder.joblib`.

The encoder contains six grouped labels:

1. Battery / Electrical
2. Belt & Accessory System
3. Braking system
4. Combustion & Ignition
5. Normal
6. Oil system

Checkpoint inspection matched **115 of 115 expected tensors**, with no missing/unexpected keys
or shape mismatches. The refactor preserves the architecture and artifacts. SHA-256:

```text
best_model.pth
7bab85ff8cf3606c8898290b0b4b753eb3aff82e42f13ad2b8b66cb7d90a2590
label_encoder.joblib
a46f0cbfb4f257c716f8d505974f17b943ebf11407c13d8e29ca1f5619765320
```

A local API smoke test decoded a generated one-second 16 kHz sine-wave WAV, ran inference, and
returned HTTP 200 with a model-derived confidence. A corrupt WAV returned 422. This is an
execution/contract check only: synthetic audio is not engine test data, and high confidence
on it does not substantiate diagnostic quality.

The historical README reports 69.6% validation and 53.0% test accuracy and makes near-100% recall
claims. The underlying test data and reports are absent, so none of these metrics was reproduced.
Historical text is preserved under `docs/history/`; it is not presented as current evidence.

## Refactor and validation

Implemented package boundaries for API, audio, ML, and data utilities; feature-based frontend
modules; environment-based paths and CORS; explicit readiness; strict checkpoint loading;
bounded upload reads and cleanup; native fetch with timeout handling; real confidence/session
metrics; dependency groups; CI; and maintained setup/deployment documentation. Tracked Python
bytecode/editor state was removed. Existing deployment command names remain supported.

Validation completed locally:

- 11 Python tests: API availability, CORS, upload type/size, error handling/cleanup, dataset
  inventory, strict checkpoint loading, grouped labels, and confidence calculation.
- 5 frontend tests: confidence display, session aggregation, multipart upload, API errors,
  and timeout behavior.
- Python Ruff checks/formatting; frontend ESLint/Prettier checks; Python wheel packaging.
- Next.js production build includes the `/` route.
- Real Chromium checks against the local frontend and API: upload/inference, matching displayed
  confidence, session statistics/records, theme changes, backend error handling, and 390px
  mobile layout. No page exceptions occurred.

## Remaining production work

1. Restore the Railway API service/domain and configure `ALLOWED_ORIGINS` for the Vercel origin.
   Confirm `/ready`, not only liveness, before testing inference.
2. Build the frontend with the restored API URL and deploy the reviewed refactor from the
   correct repository. The connected GitHub account has read-only access to A3M-IS, so this
   task cannot push a branch there or publish a PR from that branch.
3. Obtain the original dataset/provenance and reproduce held-out model evaluation. API softmax
   confidence is not calibrated accuracy or proof of vehicle safety.
4. Upgrade the frontend framework through a tested release plan. The production dependency
   audit still flags Next.js 14 and transitive dependencies after removing Axios and updating
   an available source-map dependency fix. Audit findings are dependency advisories, not proof
   that each reported exploit is reachable in this Pages Router application. See the final
   dependency-audit summary recorded below.

The refactor improves organization and observed failure behavior; it does not make the live
service operational or establish production diagnostic accuracy.

Dependency audit (`npm audit --omit=dev`): {"critical": 1, "high": 2, "info": 0, "low": 0, "moderate": 0, "total": 3}.
Flagged packages: nanoid, next, postcss.
