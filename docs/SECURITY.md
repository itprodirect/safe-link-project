# Security and Responsible Use

## Scope

Link Safety Hub is a defensive analysis tool. It is not an offensive security scanner.

## Required Usage Rules

You must:

- analyze only content you own or were explicitly authorized to review
- treat exported data as sensitive
- delete temporary exports when done

You must not:

- probe systems you do not own
- access inboxes without consent
- use this tool for exploitation

## Network Safety Policy

- Offline analysis is default behavior.
- Network-dependent modules must require explicit opt-in.
- Redirect expansion should use strict hop and timeout controls.
- Avoid fetching more content than required for the specific check.

## Data Handling

The project is local-first and should not transmit user data by default.

Recommended local hygiene:

- keep test fixtures sanitized
- avoid storing real inbox exports in git
- avoid committing raw suspicious URL lists tied to personal data

## Limits and Expectations

- Findings indicate risk, not certainty.
- False positives are expected in some edge cases (for example IDN domains).
- Users should verify high-risk findings through trusted channels.

## Disclosure Guidance

If you identify active phishing infrastructure:

- report to relevant provider abuse channels
- report to APWG or local authority processes
- do not attempt active takedown actions yourself
