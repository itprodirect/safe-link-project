# Net IP Detector

Offline detector for URLs that use IP literals as hostnames.

## Signals

- `NET001_PRIVATE_IP_LITERAL`: private/local/loopback/link-local/reserved IP host
- `NET002_PUBLIC_IP_LITERAL`: public IP host

## Why It Matters

Raw IP links are less transparent than domain names and are common in suspicious campaigns.

## Scope

- URL input only
- No network lookups
- Can be allowlist-suppressed only when `NET` (or `ALL`) is explicitly selected in allowlist categories
