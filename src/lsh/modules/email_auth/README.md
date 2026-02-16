# Email Auth Detector

Offline email-header analyzer for SPF, DKIM, and DMARC trust signals.

## Signals

- `EML000_EMPTY_INPUT`: no header content provided
- `EML001_NO_AUTH_HEADERS`: no authentication result headers available
- `EML101_SPF_FAIL` / `EML102_SPF_WEAK_OR_MISSING`
- `EML201_DKIM_FAIL` / `EML202_DKIM_WEAK_OR_MISSING`
- `EML301_DMARC_FAIL` / `EML302_DMARC_WEAK_OR_MISSING`

## Scope

- Local header analysis only (`email_headers` and `email_file`)
- No DNS/network validation in this phase
- Deterministic parsing from `Authentication-Results` and `Received-SPF`
