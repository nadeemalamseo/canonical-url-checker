# canonical-url-checker

A lightweight checker for canonical URL implementation, HTTP/HTTPS consistency, redirects, duplicate signals, and common canonicalization issues.

## What it does

This Python command-line utility fetches a page and reviews observable canonicalization signals, including:

- HTTP status and final URL
- redirect count and redirect chain
- HTML content type
- canonical `<link rel="canonical">` elements
- missing or multiple canonical elements
- canonical URL normalization and comparison with the final page URL
- relative canonical references
- HTTP-to-HTTPS consistency
- canonical target HTTP status and redirects
- canonical target domain differences
- URL fragments and query-string differences
- self-canonical versus cross-URL canonical signals

JSON output is available for scripts and CI workflows.

## Requirements

- Python 3.10+
- `requests`
- `beautifulsoup4`

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

## Usage

```bash
python canonical_url_checker.py https://example.com/
python canonical_url_checker.py https://example.com/page
python canonical_url_checker.py https://example.com/page --json
python canonical_url_checker.py https://example.com/page --timeout 10
python canonical_url_checker.py https://example.com/page --no-target-fetch
```

Multiple URLs are supported.

## Exit codes

| Code | Meaning |
| --- | --- |
| 0 | No errors or warnings |
| 1 | Warnings were found |
| 2 | An error occurred or an error finding was detected |

These codes describe observable findings, not search-engine indexing or ranking results.

## Important limitations

This tool analyzes the HTML and HTTP responses it can observe. It does not determine whether a search engine selected a canonical URL, indexing status, rankings, or crawler-specific outcomes. It does not render JavaScript, authenticate to private pages, crawl an entire site, or evaluate every duplicate-content signal.

A canonical element is an implementation signal. A search engine may use other signals and may select a different canonical.

## Methodology

See [the methodology](docs/methodology.md) for comparison rules, redirect handling, normalization, safety limits, and interpretation guidance.

## Development

```bash
python -m unittest discover -s tests -v
```

GitHub Actions runs the unit tests across Python 3.10, 3.11, and 3.12.

## Responsible use

Use the checker only against pages you are authorized to inspect. Avoid excessive automated requests and respect the target site's operational constraints.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## Security

See [SECURITY.md](SECURITY.md).

## Related resource

For broader technical SEO implementation and site-level diagnostics, see [MarketLatch SEO Services](https://marketlatch.com/seo-services/).

## License

No open-source license has been granted for this repository at this time. Unless a separate license is added, the contents remain under the repository owner's default copyright.
