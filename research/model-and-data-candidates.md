# Model and dataset candidates

Inspected 11 November 2026. Publisher-reported figures are not reproduced results.

| Candidate | Evidence | Initial decision |
| --- | --- | --- |
| Existing six-class CRNN | Checkpoint matches 115 tensors; original dataset absent | Preserve; reuse encoder for a source-separated transfer-learning pilot |
| [MIT AST AudioSet](https://huggingface.co/MIT/ast-finetuned-audioset-10-10-0.4593) | BSD-3-Clause model card; 86.6M parameters; general audio classes | Credible pretrained comparator, higher CPU cost; not a car-diagnostic model |
| [Revix knock model](https://huggingface.co/cxlrd/revix-AST-engine-knock) | MIT card; specialized binary knock task; card mixes AST/ViT preprocessing descriptions | Candidate only after reproducing its processor/model contract; claimed 90.83% is not independently verified |
| [MechSense](https://huggingface.co/krishx009/mechsense-engine-whisperer) | Model card describes bearing datasets and eight bearing classes | Industrial bearing transfer may not match combustion-car faults; not a direct replacement |
| [Jordo vehicle classifier](https://huggingface.co/Jordo23/vehicle-classifier) | MIT model card, EfficientNet-B4, 8,949 make/model/year labels; reported ~50% top-1 | Broad candidate for a confirmation-first photo prototype; verify checkpoint and data rights separately |
| [OtoMobile](https://zenodo.org/records/3382945) | 65 annotated failing-component recordings; files restricted to educational/research access | Do not bypass access restrictions; not available for automatic training |
| [KweriMoto](https://huggingface.co/datasets/rayyyyy007/kwerimoto-engine-sounds) | Healthy/knock/misfire, recording-group metadata, mixed original sources | Inspect per-source rights and split construction before selecting recordings; no blanket commercial permission |
| [Procedural engines](https://huggingface.co/datasets/rdoerfler/procedural-engine-sounds) | Synthetic engine audio; CC BY-NC 4.0 | Research-only supplementary material, not genuine fault labels or proof of generalization |
| [VAFD-related repository](https://github.com/amrrashed/Beyond-Sensors-Audio-Based-ML-for-Real-Time-Vehicle-Fault-Emergency-Classification) | Audio files are public; repository API reports no license | Not approved for reuse solely because files are downloadable |

Keep downloaded audio and new training checkpoints outside Git. Commit reproducible import
code, provenance, dataset summaries, configuration, and metrics. A pilot is not permission to
ship a commercial model; data and weights can carry different terms.
