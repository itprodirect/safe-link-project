# Dependency Audit Policy

## Purpose

Keep third-party Python dependencies at an acceptable security baseline and block known-vulnerable packages from merging into `main`.

## CI Enforcement

- CI runs `pip-audit --progress-spinner off --strict --skip-editable` on Python `3.11`.
- The dependency-audit step is **blocking** (non-zero exit fails the job).

Workflow reference: `.github/workflows/ci.yml`

## Local Usage

From the repo root:

```bash
python -m pip_audit --progress-spinner off --strict --skip-editable
```

or:

```bash
make audit
```

## Triage Workflow

When `pip-audit` fails in CI:

1. Confirm the failure is a real third-party advisory (not a local editable package resolution issue).
2. Identify vulnerable package + advisory ID from CI logs.
3. Attempt direct dependency update (preferred).
4. If transitive, update or pin the top-level package that brings it in.
5. Re-run `pip-audit` and full CI checks.
6. Document remediation in PR notes and session log.

## Temporary Exception Policy

Temporary exceptions are allowed only when no safe upgrade path exists the same day.

Required controls:

1. Open an issue with:
   - advisory ID(s)
   - impact assessment
   - mitigation and owner
   - expiry date
2. Add a temporary CI ignore (`--ignore-vuln <ID>`) with an inline comment linking that issue.
3. Remove the exception before expiry.

No permanent exceptions.

## Review Cadence

- Audit gate: every PR/push (CI).
- Manual dependency review: at least monthly.
- Any active exception: reviewed weekly until removed.
