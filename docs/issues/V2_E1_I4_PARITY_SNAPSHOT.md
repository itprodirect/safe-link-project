# E1-I4: Contract Parity and Snapshot Governance for v1/v2 Overlap

Parent epic: #3
Milestone: V2-Phase-1
Labels: v2, backend, api, docs

## Summary

Formalize and enforce v1/v2 overlap parity with reproducible snapshot fixtures and update workflow guidance.

## Scope

1. Maintain deterministic snapshot fixtures for overlap payloads.
2. Enforce parity checks in non-optional test lanes.
3. Document fixture update procedure and review expectations.

## Acceptance Criteria

- [ ] Snapshot fixtures exist for canonical URL/email overlap payloads.
- [ ] Test suite validates v1/v2 overlap parity without requiring FastAPI extras.
- [ ] Runtime-variant fields are normalized in snapshot tests.
- [ ] Docs explain when and how to update fixtures.
- [ ] CI includes parity test execution in required lane(s).

## Notes

Current baseline added in branch via `tests/contracts/test_v1_v2_snapshot_parity.py` and `tests/fixtures/contracts/v1_v2_single_payloads.json`.
