# Ethiopian vehicle data collection

The current pilot is research-only and does not validate Ethiopian fleet performance. More
clips alone do not solve source bias or unreliable diagnosis labels.

## Required metadata for new consented recordings

- Random/pseudonymous vehicle ID and recording/session ID. Do not use plate numbers as IDs.
- Make, model, model year if known, powertrain/fuel type, recording device and placement.
- Operating context: engine off/starting/idling/driving/braking/turning; background conditions.
- Mechanic-confirmed condition and confirmation method; retain uncertain/unknown labels rather
  than guessing. Link pre/post repair recordings using the same vehicle grouping.
- Explicit recording-use consent, source owner, permitted research/commercial use, retention
  period and withdrawal process. Remove unnecessary speech, identifying metadata and bystander data.
- Audio duration/rate/channels and content hashes; reject corrupt/clipped/silent captures.

Record only when it is safe. Do not ask drivers to reproduce brake, steering, overheating,
fire/fuel or other dangerous symptoms. Seek qualified assistance instead.

## Evaluation design

Partition by vehicle/session/source before making windows or augmentations. Keep related
pre/post repair clips and different microphone takes together. Test across devices, garages,
vehicle makes, fuel types and background noise. Include non-car speech/music, unrelated machinery,
EVs and unknown faults; a classifier must be able to say it is uncertain or unsupported.

Reserve a new mechanic-labeled release test set that is not inspected for model selection.
Report confusion matrices and per-fault false negatives, not only headline accuracy. Confirm
that any pretrained model's training corpus does not contain the release evaluation recordings.
