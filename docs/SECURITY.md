# Security & Responsible Use

## Scope of This Tool

Link Safety Hub is a **defensive** security tool. It helps users understand risks in links, messages, and emails they receive. It does not perform offensive security testing, vulnerability scanning, or penetration testing.

## Rules for Use

### You MUST

- Only analyze content you received or own (your emails, links sent to you, your QR codes)
- Get explicit verbal or written permission before scanning someone else's email exports
- Treat exported email data as sensitive — store it locally, delete when done
- Report actual phishing to the impersonated brand and to relevant authorities (IC3, Anti-Phishing Working Group)

### You MUST NOT

- Use this tool to probe or test systems you don't own
- Access other people's email accounts without their consent
- Store or share analyzed email content beyond what's needed for the analysis
- Use findings to harass or shame individuals (e.g., publicly posting someone's weak email security)
- Modify the tool to perform active exploitation of discovered vulnerabilities

## Safe Analysis Practices

### Compromised inbox cleanup

If helping a family member clean up a potentially compromised inbox:

1. **Get their explicit consent** — treat it like an incident response engagement
2. **Export to local files** — download as .mbox or .eml, don't browse the inbox live
3. **Scan on a clean machine** — ideally not the same machine the compromise occurred on
4. **Produce a cleanup list** — the tool generates a queue of suspicious items to review
5. **Do account recovery separately** — password reset, enable MFA, audit recovery options
6. **Delete the export when done** — don't keep copies of someone else's email

### Network safety

- The redirect expander follows links using HEAD requests (minimal data transfer)
- The content snapshot fetches HTML only (no JavaScript execution)
- All network calls respect robots.txt and include a descriptive User-Agent
- Use `--dry-run` to see what would be fetched without making network calls
- Consider running network modules through a VPN if checking highly suspicious links

## Data Handling

This tool processes data locally by default. No data is sent to external services unless explicitly enabled (e.g., future VirusTotal integration).

The tool does NOT:
- Phone home or send telemetry
- Store analysis results unless you explicitly save them
- Require an internet connection for offline modules (#1, #5, #6, #9, #10)
- Cache or log URLs you check

## Limitations (Be Honest About What This Can't Do)

- This is not a replacement for enterprise email security (Proofpoint, Mimecast, etc.)
- Static analysis cannot detect all malicious content — sophisticated phishing may pass checks
- Domain age and registration data have false positives (new legitimate sites exist)
- QR code analysis only works on the decoded URL — it can't detect malicious QR overlays in the physical world
- Email header analysis tells you about authentication, not about content safety
- This tool provides information and recommendations, not guarantees

## Disclosure

If you discover a real phishing campaign or compromised infrastructure while using this tool, consider responsible disclosure:
- Report phishing URLs to Google Safe Browsing: https://safebrowsing.google.com/safebrowsing/report_phish/
- Report to the Anti-Phishing Working Group: reportphishing@apwg.org
- Report to the impersonated brand's abuse team
- File a complaint with IC3 (FBI): https://www.ic3.gov/
