# Net IP Detector

Offline detector for URLs that use IP literals or IP-obfuscation tricks as hostnames.

## Signals

- `NET001_PRIVATE_IP_LITERAL`: private/local/loopback/link-local/reserved IP host
- `NET002_PUBLIC_IP_LITERAL`: public IP host
- `NET003_OBFUSCATED_IP`: integer/octal/hex/abbreviated IPv4 encoding
- `NET004_LOCALHOST_ALIAS`: localhost-style alias (`localhost`, `localhost.localdomain`, etc.)
- `NET005_IPV6_MAPPED_V4`: IPv6-mapped IPv4 wrapper (`::ffff:x.x.x.x`)
- `NET006_MIXED_NOTATION`: mixed hex/octal/decimal notation in dotted quads

## Why It Matters

Raw or obfuscated IP links are less transparent than domain names and are common in suspicious campaigns, SSRF probes, and deception attempts.

## Scope

- URL input only
- No network lookups
- Uses deterministic parsing helpers from `src/lsh/core/normalizer.py` for obfuscated IP formats
- Can be allowlist-suppressed only when `NET` (or `ALL`) is explicitly selected in allowlist categories
