# Methodology

This checker evaluates canonicalization signals visible in the supplied page HTTP response and HTML. It is a diagnostic aid, not a search-engine canonical-selection simulator.

## Checks

1. Normalize the requested HTTP(S) URL by lower-casing the scheme and hostname, removing fragments, and using `/` for an empty path.
2. Fetch the page with redirects enabled and record the requested URL, final URL, status, redirect chain, content type, and response size.
3. Parse HTML for `<link rel="canonical" href="...">` elements.
4. Resolve relative canonical references against the final page URL.
5. Report missing, empty, invalid, or multiple canonical elements.
6. Compare the first canonical URL with the normalized final page URL.
7. Flag HTTP canonicals on HTTPS pages and canonical host differences.
8. When the canonical differs from the page URL, optionally fetch the canonical target and record its HTTP status and redirects.

## Interpretation

A self-canonical is an observable implementation pattern, not a ranking guarantee. A cross-URL canonical may be intentional; the tool reports the difference for review. Multiple canonical elements are reported as an error because the tool cannot determine which one should be preferred.

Search engines may use additional signals when selecting a canonical URL. This checker does not claim to reproduce those systems.

## Safety limits

- Requests are made only to URLs supplied by the user and, when enabled, the canonical target declared by the page.
- Redirects are followed only as part of those requested fetches.
- Response bodies are limited to 2 MiB by default.
- A finite request timeout is applied.
- The tool does not crawl links, sitemap URLs, or an entire domain.
- Private authentication is not supported.

## Exit codes

- 0: no errors or warnings
- 1: warnings found
- 2: an error was found or input could not be processed

Exit codes describe checker findings, not indexing or ranking outcomes.
