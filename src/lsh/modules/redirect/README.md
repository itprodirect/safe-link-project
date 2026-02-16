# Redirect Chain Detector

Opt-in network detector for redirect-chain behavior.

## Signals

- `RED000_NETWORK_URL_REQUIRED`: network mode needs explicit `http(s)` URL
- `RED001_REDIRECT_CHAIN_PRESENT`: one or more redirect hops
- `RED002_CROSS_DOMAIN_REDIRECT`: chain crosses registrable domains
- `RED003_MAX_HOPS_REACHED`: configured hop limit reached
- `RED004_REDIRECT_LOOP_DETECTED`: repeated URL loop in chain
- `RED005_REQUEST_TIMEOUT`: timeout during network checks
- `RED006_REQUEST_ERROR`: request exception interrupted checks
- `RED007_NON_HTTP_REDIRECT_TARGET`: non-http(s) redirect target

## Safety Design

- Off by default; requires `--network`
- HEAD requests only
- explicit timeout and max-hop controls
- no content fetch beyond redirect headers
