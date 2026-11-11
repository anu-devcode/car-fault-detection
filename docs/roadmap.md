# Car care hub: development roadmap

Initial market: Ethiopia. Accept any user-entered make/model; do not equate that with
recognition accuracy or parts/repair coverage for every vehicle. Expand the region through
configuration when the user base expands. English is the initial interface language.

## Work stages

1. **Development controls and research.** Keep pushing tested milestones directly to `main`.
   Block Vercel Git deployments and Railway builds. Record candidate data/model provenance.
2. **Care guidance and garages.** Add symptom-aware next steps, simple safe owner checks,
   stop-driving/tow escalation, and user-initiated nearby garage search for Ethiopia. A model
   result is a clue, not a confirmed diagnosis. Urgent symptoms override an apparently normal
   audio classification. Never infer a verified nearby business or opening hours from a map link.
3. **Data and transfer learning.** Acquire permitted real audio with source/recording IDs;
   check audio and duplicates; split by source before windowing. Fine-tune a head over a
   pretrained encoder and compare against an untouched baseline. Keep a separate held-out test
   split. Record metrics, limitations, checksums, and all model/source revisions. Retain the
   current six-class checkpoint until a candidate passes an independent comparison.
4. **Photo identification.** Reuse a pretrained make/model classifier. Return several possible
   matches and require user confirmation. Support photo upload/camera capture and manual entry.
   A photo cannot establish exact trim, VIN, engine, service history, mileage, or concealed damage.
5. **Vehicle knowledge.** Attach source-linked manuals, maintenance context, and confirmed
   vehicle details. Separate unknown/estimated/verified fields. Do not invent universal service
   intervals or imply US-market specifications apply to Ethiopian imports.
6. **Evaluation and expansion.** Collect consented Ethiopian vehicle/session recordings,
   mechanic-confirmed labels, non-engine/noisy inputs, and representative vehicle photographs.
   Evaluate false negatives, unknown inputs, calibration, device/vehicle separation, and model
   coverage. Add reviewed Amharic/localization support and a verified garage-provider adapter.
7. **Production stage, later.** Resolve framework advisories, security/privacy/retention,
   performance and model-quality gates. Only enable hosting after the user requests release.

## Development-only hosting controls

- Root and `frontend/vercel.json`: `git.deploymentEnabled=false`.
- Railway watches only `production-release/**`, which normal development does not modify.
- Railway's build command additionally runs `scripts/deployment_guard.py`, which fails closed
  unless `CAR_HUB_ALLOW_DEPLOY=true` is explicitly set. This variable must stay unset during
  development. Local tests/builds do not call this hosting guard.
- GitHub Actions runs checks only; no deployment jobs are defined.
- Existing provider dashboard settings and other repositories are outside these local guards.
  Keep Railway autodeploy disabled in its service settings as well. No hosting credentials or
  deployment commands are used during development.

References: [Vercel Git configuration](https://vercel.com/docs/project-configuration/git-configuration),
[Railway watch patterns](https://docs.railway.com/config-as-code/reference),
[Railway autodeploy control](https://docs.railway.com/deployments/github-autodeploys).

## Model decision

Do not select a “best” model from a publisher's accuracy claim. Compare candidates on the
same source-separated, legally usable data and latency/memory budget. The existing CRNN is
already pretrained on car sounds; it is the first inexpensive transfer-learning baseline.
AST/CLAP are general pretrained audio candidates, not validated automotive diagnostics.
Broad vehicle-photo models offer possible identities; they cannot know everything about a car.
