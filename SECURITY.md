# Security

Do not submit credentials, private URLs, personal data, or confidential page content in issues.

If you believe the checker has a security vulnerability, describe the affected behavior, reproduction steps, and impact without publishing secrets. Use GitHub's private vulnerability reporting feature when available; otherwise contact the repository maintainer through the GitHub profile.

The checker makes network requests only to the URL supplied by the user and, when enabled, the canonical URL declared by that page. It does not crawl discovered links or require authentication. A response-size limit and request timeout reduce accidental resource consumption.
