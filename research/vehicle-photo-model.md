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
