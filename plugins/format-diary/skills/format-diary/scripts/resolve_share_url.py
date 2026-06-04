#!/usr/bin/env python3
"""Resolve a Google Share URL (https://share.google/...) to its target URL.

Usage:
    python resolve_share_url.py https://share.google/63KCWNHaYSbAF4hgJ

Can also be imported:
    from resolve_share_url import resolve_share_url
    target = resolve_share_url("https://share.google/63KCWNHaYSbAF4hgJ")

Uses only the Python standard library.
"""
from __future__ import annotations

import argparse
import html
import re
import sys
import time
from urllib.request import Request, urlopen

DEFAULT_TIMEOUT = 15.0
DEFAULT_RETRIES = 2
_RETRY_BACKOFF = 1.0  # seconds, multiplied by the attempt number

_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

# share.google often resolves via a meta-refresh / JS hop rather than a plain
# HTTP 3xx redirect, so we inspect the final page for those patterns too.
_META_REFRESH_RE = re.compile(
    r"""<meta[^>]+http-equiv=["']?refresh["']?[^>]+content=["'][^"']*url=([^"'>]+)""",
    re.IGNORECASE,
)
_JS_REDIRECT_RE = re.compile(
    r"""(?:location\.(?:href|replace)\s*=?\s*\(?|window\.location\s*=)\s*["']([^"']+)["']""",
    re.IGNORECASE,
)


def resolve_share_url(
    url: str,
    timeout: float = DEFAULT_TIMEOUT,
    retries: int = DEFAULT_RETRIES,
) -> str:
    """Return the URL that a Google Share link points to.

    Follows HTTP redirects and, if needed, a meta-refresh or JS location hop
    found in the landing page. Falls back to the final HTTP URL.

    On a network error (including rate limiting / HTTP 429) the request is
    retried up to ``retries`` extra times with a linear backoff. The last error
    is re-raised if all attempts fail; callers should keep the original URL in
    that case rather than dropping it.
    """
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            return _fetch_target(url, timeout)
        except Exception as exc:  # noqa: BLE001 - retry any fetch failure
            last_error = exc
            if attempt < retries:
                time.sleep(_RETRY_BACKOFF * (attempt + 1))

    assert last_error is not None  # loop runs at least once
    raise last_error


def _fetch_target(url: str, timeout: float) -> str:
    request = Request(url, headers={"User-Agent": _USER_AGENT})
    with urlopen(request, timeout=timeout) as response:
        final_url = response.geturl()
        charset = response.headers.get_content_charset() or "utf-8"
        body = response.read().decode(charset, errors="replace")

    for pattern in (_META_REFRESH_RE, _JS_REDIRECT_RE):
        match = pattern.search(body)
        if match:
            candidate = html.unescape(match.group(1).strip())
            if candidate.startswith("http"):
                return candidate

    return final_url


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Resolve a Google Share URL to its target URL."
    )
    parser.add_argument("url", help="the https://share.google/... link to resolve")
    parser.add_argument(
        "-t",
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT,
        metavar="SECONDS",
        help=f"network timeout in seconds (default: {DEFAULT_TIMEOUT:g})",
    )
    parser.add_argument(
        "-r",
        "--retries",
        type=int,
        default=DEFAULT_RETRIES,
        metavar="N",
        help=f"extra attempts on network failure (default: {DEFAULT_RETRIES})",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help=(
            "fail (exit 1) when the URL can't be resolved instead of falling "
            "back to printing the original URL"
        ),
    )
    args = parser.parse_args(argv[1:])

    if args.timeout <= 0:
        parser.error("--timeout must be a positive number")
    if args.retries < 0:
        parser.error("--retries must be zero or a positive integer")

    try:
        print(resolve_share_url(args.url, timeout=args.timeout, retries=args.retries))
    except Exception as exc:  # noqa: BLE001 - surface any failure to the caller
        if args.strict:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        # Couldn't resolve (e.g. HTTP 429 rate limit): keep the original URL so
        # the link is never lost. Note the failure on stderr for visibility.
        print(f"warning: could not resolve, keeping original URL: {exc}", file=sys.stderr)
        print(args.url)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
