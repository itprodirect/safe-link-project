# QR Decode Module

Local QR payload decode helpers with URL handoff support for `lsh qr-scan`.

## What It Provides

- `decode_qr_payloads_from_image(...)`: decode text payloads from a local image
- `extract_url_payloads(...)`: filter decoded payloads to HTTP(S) URLs
- `QRDecodeDetector`: optional detector-style wrapper for QR decode status signals (`QRC*`)

## CLI Integration

- `lsh qr-scan <image_path>` decodes QR payloads and analyzes the first decoded URL payload
- `lsh qr-scan <image_path> --all` analyzes all decoded URL payloads

## Dependency Notes

- Uses optional dependencies: `Pillow` + `pyzbar`
- `pyzbar` also requires a platform `zbar` backend
- Missing backends are reported as friendly runtime errors instead of breaking the rest of the app
