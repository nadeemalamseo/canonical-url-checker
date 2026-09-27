# Canonical URL Checker

A practical command-line checker for reviewing canonical link elements, redirects, HTTP/HTTPS consistency, canonical targets, and common canonicalization issues.

## Get the tool

This is a **command-line tool**, not a browser-based checker.

[Download the latest source as a ZIP](https://github.com/nadeemalamseo/canonical-url-checker/archive/refs/heads/main.zip) or open the [GitHub repository](https://github.com/nadeemalamseo/canonical-url-checker).

After downloading and extracting:

```bash
python -m pip install -r requirements.txt
python canonical_url_checker.py https://example.com/page
python canonical_url_checker.py https://example.com/page --json
```

## What the results mean

The checker reports observable HTTP and HTML signals. It does not determine which canonical a search engine will select or whether a page will rank or be indexed.
