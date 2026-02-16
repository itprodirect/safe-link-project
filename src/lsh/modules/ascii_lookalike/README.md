# ASCII Lookalike Detector

Offline detector for ASCII-only brand impersonation patterns.

## Signals

- `ASCII001_AMBIGUOUS_GLYPHS`: single-character ambiguity (for example i/l/1) that matches a known brand token
- `ASCII002_LEET_SUBSTITUTION`: digit-to-letter substitutions (for example 0->o) that normalize to a known brand token

## Scope

- URL input only
- Checks the registrable-domain label
- Conservative by design to limit false positives
- No network lookups
- Supports domain allowlist suppression (default allowlist scope includes `ASCII`)
