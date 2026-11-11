# Research AST transfer head — not a production model

Trained 11 November 2026. This is a three-class research candidate, not a replacement for
the bundled six-class model. Release is blocked; the data's original rights, diagnostic labels,
regional validity and non-engine rejection have not been established.

## Actual experiment

- 96 real recordings from pinned KweriMoto revision
  `0335c63789e2ceedfbf521983db59642420864c2`: 60 train, 18 validation, 18 exploratory test.
- Classes: healthy, engine knock, misfire. Synthetic knock is excluded. AudioSet recordings
  must carry the explicit car tag. Published recording groups are kept in their assigned splits;
  identical decoded audio is rejected across splits.
- Both encoders receive the central one-second segment. The CRNN uses its existing mel
  preprocessing; AST uses its checkpoint's feature extractor. Features are standardized using
  training statistics only.
- Encoders remain frozen. A new linear classifier head is trained for 100 AdamW epochs; the
  checkpoint epoch and encoder are selected using validation macro F1. This is transfer learning
  with head fitting, not full-network fine-tuning.

| Encoder | Validation macro F1 | Selected epoch |
| --- | ---: | ---: |
| Existing car CRNN | 0.7410 | 9 |
| MIT AST AudioSet | 0.9441 | 3 |

AST was selected on validation. Its exploratory test accuracy was **15/18 (83.3%)**, macro F1
**0.8308**. It detected **4/6 knock clips**; two knocks were classified as misfire. The first
CRNN-only run achieved 12/18 (66.7%) and detected 1/6 knock clips. These tiny counts are not
reliable estimates of real-world safety or future fleet accuracy.

## Important evaluation limits

The test subset was inspected during development; it is not a release lockbox. AST was
pretrained on AudioSet, and this pilot includes AudioSet-derived recordings. Source separation
within KweriMoto does **not** establish separation from encoder pretraining. Original CRNN
pretraining overlap also cannot be excluded. This is an exploratory feasibility comparison,
not proof that AST is the best model for Ethiopian vehicles. Misfire recordings come from a
cleaner source, so recording conditions can confound fault labels.

There are no Ethiopian fleet/device tests, mechanic-confirmed fault labels, calibrated confidence
or validated non-engine rejection. An arbitrary photograph/audio sample can still cause a
confident wrong prediction. Do not use this candidate to clear a vehicle for driving.

## Reproduce locally

```bash
python -m pip install -e '.[transfer,training,dev]'
# Use a project-owned HF_HOME. CPU-only Torch is documented in docs/setup.md.
python scripts/import_research_pilot.py --allow-research-only
python scripts/train_transfer_pilot.py --encoders crnn ast --output research/transfer-comparison
```

`metrics.json` records the actual run, configuration and source revision. `data-provenance.json`
contains recording IDs and hashes, not raw audio. `head.npz` contains only the new head, training
normalization and class names; load with `allow_pickle=False`. The frozen encoder is the pinned
[MIT AST checkpoint](https://huggingface.co/MIT/ast-finetuned-audioset-10-10-0.4593), revision
`f826b80d28226b62986cc218e5cec390b1096902` (model card BSD-3-Clause). Model and audio rights differ.

An explicit local adapter is available after download:

```bash
AUDIO_MODEL_BACKEND=research_ast ALLOW_RESEARCH_MODELS=true \
RESEARCH_AUDIO_MODEL_DIR=research/transfer-comparison \
python -m uvicorn backend:app --host 127.0.0.1 --port 8000
```

Without these flags, the original six-class CRNN remains the default. The AST adapter loads
cached encoder weights only and does not silently download a model during application startup.

Next: establish reusable data rights; acquire independent Ethiopian vehicle/session recordings
and technician-confirmed labels; benchmark multi-window inference, unknown inputs, calibration
and source/vehicle-domain shifts; then consider unfreezing upper AST layers with an independent
release test set. Do not optimize repeatedly against this exploratory test subset.
