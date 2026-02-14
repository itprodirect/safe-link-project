# Module Specifications

Each module is a self-contained package in `src/lsh/modules/<name>/` that implements `ModuleInterface`. This document describes what each module does, how it works, and known limitations.

## Module #1: Homoglyph / IDN Detector

**Directory:** `src/lsh/modules/homoglyph/`
**Input types:** `url`, `text`
**Network required:** No

### What it detects

- Unicode homoglyphs: characters that look identical to ASCII but aren't (Cyrillic "а" vs Latin "a")
- Mixed-script attacks: domain names combining characters from multiple Unicode scripts
- Punycode domains: IDN domains displayed in their decoded form alongside the punycode
- Lookalike substitutions: digit "0" for letter "O", digit "1" for letter "l", etc.

### Technical approach

1. Extract domain from URL
2. Check if domain contains non-ASCII characters → decode punycode and display both forms
3. Run Unicode script analysis (identify which scripts are present)
4. Compare against confusable characters database (Unicode confusables.txt)
5. Check against a brand name list for likely impersonation targets

### Key library

`confusables` (Python package) or the Unicode Consortium's confusables.txt processed directly.

### Limitations

- Cannot detect every visual similarity (font-dependent rendering)
- Brand name list requires manual maintenance
- Subdomain tricks (e.g., `paypal.com.evil.com`) are technically not homoglyphs — handled by Domain Risk module

---

## Module #2: Redirect Chain Expander

**Directory:** `src/lsh/modules/redirect/`
**Input types:** `url`
**Network required:** Yes (opt-in)

### What it detects

- Full redirect chain from shortened/obfuscated URL to final destination
- Number of hops (high hop count = suspicious)
- Intermediate tracking domains
- Final destination domain for downstream analysis

### Technical approach

1. Send HEAD request to URL with `allow_redirects=False`
2. Follow `Location` header manually, recording each hop
3. Cap at 15 redirects (prevent infinite loops)
4. Timeout per hop: 5 seconds
5. Record: URL, status code, server header, redirect type (301/302/307/meta refresh)
6. Pass final URL to Homoglyph and Domain Risk modules for further analysis

### Safety measures

- HEAD only (no body download by default)
- Custom User-Agent: `LinkSafetyHub/0.1 (security-analysis)`
- `--dry-run` resolves DNS only, no HTTP requests
- No cookie jar (prevents tracking)
- No JavaScript execution

### Limitations

- JavaScript redirects and meta refresh tags require Content Snapshot module (#4)
- Some URL shorteners block HEAD requests — fallback to GET with stream=True and immediate close
- Cannot follow redirects behind authentication walls

---

## Module #5: Email Auth Checker

**Directory:** `src/lsh/modules/email_auth/`
**Input types:** `email_headers`, `email_file`
**Network required:** No (header parsing), Optional (live DNS lookups for SPF/DKIM/DMARC records)

### What it detects

- SPF pass/fail/softfail/none from `Received-SPF` or `Authentication-Results` headers
- DKIM signature validation status
- DMARC policy and alignment
- Suspicious header patterns: mismatched `From` and `Return-Path`, unusual `Received` chain
- Missing authentication (no SPF, no DKIM = higher risk)

### Technical approach

1. Parse raw email headers (RFC 2822)
2. Extract `Authentication-Results`, `Received-SPF`, `DKIM-Signature`, `ARC-*` headers
3. Evaluate pass/fail status from header values
4. Optionally query DNS for the sender domain's SPF/DKIM/DMARC records to cross-validate
5. Flag common spoofing indicators: display name mismatch, envelope vs header from mismatch

### Key libraries

- `email` (stdlib) for header parsing
- `dkimpy` for DKIM verification (if validating signatures directly)
- `dnspython` for DNS lookups (optional, network mode)

### Limitations

- Header-only analysis trusts the receiving mail server's Authentication-Results — a compromised server could lie
- DKIM verification requires the full email body (not just headers)
- Cannot determine if a "pass" means the email is safe — only that it came from the stated domain

---

## Module #7: QR Code Decoder

**Directory:** `src/lsh/modules/qr_decode/`
**Input types:** `qr_image`
**Network required:** No (decode only), Yes (if analyzing decoded URL)

### What it detects

- Encoded URL from QR code image
- Non-URL payloads (vCard, WiFi config, plain text) — flagged as info
- After decoding, pipes URL through the full analysis pipeline

### Technical approach

1. Accept image file (PNG, JPEG, screenshot)
2. Decode QR code using `pyzbar` or `qreader`
3. If decoded content is a URL, create new AnalysisInput(type="url") and return to orchestrator
4. If not a URL, return an INFO-level finding describing the content

### Key libraries

- `pyzbar` (requires libzbar system dependency)
- `Pillow` for image handling
- Alternative: `opencv-python` + `qreader` for better detection on photos

### Limitations

- Cannot detect physical QR code overlay attacks (sticker placed over legitimate QR)
- Image quality affects decode success — screenshots generally work better than photos
- Multiple QR codes in one image: currently decodes the first one found

---

## Module #9: Family Mode Explainer

**Directory:** `src/lsh/modules/family_mode/`
**Input types:** N/A (operates on Finding objects, not raw input)
**Network required:** No

### What it does

Takes technical Findings from other modules and generates plain-English explanations with clear action steps. This is a **presentation layer**, not a detection module.

### Technical approach

1. Receive a list of Finding objects
2. For each finding, generate a `family_explanation` using template strings
3. Generate action recommendations based on severity and category
4. Produce a summary that a non-technical person can act on

### Template examples

```
HOMOGLYPH:
"This link looks like it goes to {brand}, but it uses trick characters
to disguise a fake website. The real address is {decoded_domain}.
→ Do NOT click this link.
→ If you need to visit {brand}, type the address directly in your browser."

SPF_FAIL:
"This email claims to be from {sender}, but the sending server isn't
authorized to send on their behalf. This is a common sign of a spoofed email.
→ Don't click any links or download attachments.
→ If you were expecting this email, contact {sender} by phone to verify."
```

### Design principle

Family Mode should always answer three questions: What is the risk? Why should I care? What should I do?

### Limitations

- Template-based explanations can feel generic — future enhancement: LLM-powered natural language generation
- Cannot account for every possible context — recommendations are conservative by default

---

## Module #3: Domain Risk Profiler (Phase 2+)

**Directory:** `src/lsh/modules/domain_risk/`
**Network required:** Yes

Checks domain age (WHOIS), DNS configuration, TLD reputation, and typosquat similarity to popular brands.

---

## Module #4: Content Snapshot Analyzer (Phase 3+)

**Directory:** `src/lsh/modules/content_snapshot/`
**Network required:** Yes

Safe headless fetch of page HTML (no JS). Checks for fake login forms, brand logo impersonation, hidden iframes.

---

## Module #6: Attachment Triage (Phase 3+)

**Directory:** `src/lsh/modules/attachment/`
**Network required:** No

Static analysis of email attachments: file type verification, hash generation, macro detection in Office documents, embedded URL extraction.

---

## Module #8: Password Hygiene (Phase 4)

**Directory:** `src/lsh/modules/password/`
**Network required:** Optional (HIBP API)

Local-only password strength and reuse detection. No passwords are stored or transmitted. Optional integration with Have I Been Pwned's k-anonymity API.

---

## Module #10: Offline Inbox Scanner (Phase 3)

**Directory:** `src/lsh/modules/inbox_scanner/`
**Network required:** No (scan), Optional (for redirect/domain checks on found URLs)

Parses .mbox and .eml files, extracts all URLs and sender information, runs each through the analysis pipeline, and produces a prioritized cleanup queue sorted by risk score.
