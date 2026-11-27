# Photo model prototype

Source: [Jordo23/vehicle-classifier](https://huggingface.co/Jordo23/vehicle-classifier), pinned
revision `7a0a0ee5584202b5eba858cf7464f5ca6b7341b3`. The model card identifies an EfficientNet-B4,
8,949 make/model/year labels and MIT model licensing. Underlying VMMRdb data rights need separate
review before release. The publisher reports roughly 50% top-1 accuracy; this project has not
reproduced that result or measured Ethiopian fleet accuracy.

Local installation checksums are recorded in `models/vehicle-photo/provenance.json`. The adapter
loads with `weights_only=True`, validates the CSV against the checkpoint labels, and uses strict
weight loading. New downloaded weights are not committed to Git. Photos are byte/dimension
bounded, decoded as JPEG/PNG/WEBP, processed in memory, and not saved by this app.

The output is five possible matches requiring user confirmation. There is no validated car
presence detector: even a non-car image can yield a confident wrong car label. Exact trim,
engine, VIN, history, mileage and hidden damage cannot be recovered from appearance alone.
Camera quality, model year lookalikes, regional trims and unsupported makes require explicit
coverage testing. Manual vehicle entry remains available independently of this optional model.

Low-score or ambiguous photo outputs recommend manual entry and hide candidate selection in
the UI. This conservative score/margin heuristic is not calibrated recognition accuracy or a
car-presence detector; high-scoring non-car/unsupported inputs may still be wrong.

## Local real-photo probe

An exploratory CPU run used the five openly licensed photos below. The existing vehicle
recognizer was exercised through `/vehicles/identify` with its pinned weights. It returned
`uncertain` on all five images. Its top candidate for the Corolla was a Honda Civic with a
model score of 0.050, so that candidate was withheld in the app. One example cannot establish
the recognition accuracy of the overall model.

A separate [SmolVLM-256M-Instruct candidate](https://huggingface.co/HuggingFaceTB/SmolVLM-256M-Instruct)
at revision `d039ab0d4b9311b617e8ffec1d06c8464364aeb3` was evaluated without uploads or fine-tuning.
Each photo was rotated according to its EXIF orientation, resized to at most 768 pixels per side,
and used with two prompts. The first asked for a short description of the main object. The second
asked for one letter from seven categories. Both used deterministic decoding and a 48-token limit.
The candidate described several subjects correctly but returned the wrong category letter on
all five structured responses. Individual prompts took 24–39 seconds on this CPU. These findings
ruled it out for this iteration of the inspection endpoint.

| Expected view | Sample attribution | License |
| --- | --- | --- |
| Whole car | [2020 Toyota Corolla SE](https://commons.wikimedia.org/wiki/File:2020_Toyota_Corolla_SE_2.0L_sedan,_12.28.19.jpg) by Ghostofakina | CC BY-SA 4.0 |
| Engine bay | [Toyota 1NZ-FE engine](https://commons.wikimedia.org/wiki/File:1.5_L_Toyota_1NZ-FE_engine.jpg) by automachi | CC BY 4.0 |
| Tyre | [Damaged tire](https://commons.wikimedia.org/wiki/File:Damaged_tire.png) by Nikolay Shilov | CC BY-SA 3.0 |
| Dashboard | [Check Engine](https://commons.wikimedia.org/wiki/File:Check_Engine.jpg) by .kkursor | CC0 1.0 |
| Unrelated | [Cat sitting on a desk](https://commons.wikimedia.org/wiki/File:Cat_sitting_on_a_desk_(42921038494).jpg) by freestocks.org | CC0 1.0 |

The app's confirmation workflow was separately checked in mobile Chrome at 390px.
Manual review produced tyre guidance and a notes download containing only selected findings.
A controlled model response supplied a photo suggestion, which reset the selection and left
its checkbox unchecked. This browser check verified the workflow with a model stub.
