# Homoglyph / IDN Detector

Offline URL hostname analyzer for Unicode lookalike risk:

- extracts hostname from URL input
- surfaces Unicode vs IDNA punycode views
- flags non-ASCII hostnames
- flags mixed-script labels (for example Latin + Cyrillic)
- uses `confusables` to identify likely ASCII lookalikes

Findings are emitted with explicit codes:

- `HMG001_NON_ASCII_HOSTNAME`
- `HMG002_PUNYCODE_VISIBILITY`
- `HMG003_MIXED_SCRIPT_HOSTNAME`
- `HMG004_CONFUSABLE_CHARACTERS`

Each finding contains evidence with both technical detail and incremental risk context (`Risk Delta`, `Cumulative Risk`).
