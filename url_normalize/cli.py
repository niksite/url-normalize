#!/usr/bin/env python
"""Command line interface for url-normalize."""

import argparse
import sys
from importlib.metadata import version

from .url_humanize import url_humanize
from .url_normalize import url_normalize


def main() -> None:
    """Parse arguments and run url_normalize."""
    # Force UTF-8 output to prevent UnicodeEncodeError on Windows
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")

    parser = argparse.ArgumentParser(description="Normalize a URL.")
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"%(prog)s {version('url-normalize')}",
    )
    parser.add_argument("url", help="The URL to normalize.")
    parser.add_argument(
        "-c",
        "--charset",
        default="utf-8",
        help="The charset of the URL. Default: utf-8",
    )
    parser.add_argument(
        "-s",
        "--default-scheme",
        default="https",
        help="The default scheme to use if missing. Default: https",
    )
    parser.add_argument(
        "-f",
        "--filter-params",
        action="store_true",
        help="Filter common tracking parameters.",
    )
    parser.add_argument(
        "-d",
        "--default-domain",
        type=str,
        help="Default domain to use for absolute paths (starting with '/').",
    )
    parser.add_argument(
        "-p",
        "--param-allowlist",
        type=str,
        help="Comma-separated list of query parameters to allow (e.g., 'q,id').",
    )
    parser.add_argument(
        "-H",
        "--humanize",
        action="store_true",
        help="Print a human-readable URL that normalizes to the same value.",
    )

    args = parser.parse_args()

    allowlist = args.param_allowlist.split(",") if args.param_allowlist else None
    transform_url = url_humanize if args.humanize else url_normalize

    try:
        output_url = transform_url(
            args.url,
            charset=args.charset,
            default_scheme=args.default_scheme,
            default_domain=args.default_domain,
            filter_params=args.filter_params,
            param_allowlist=allowlist,
        )
    except Exception as e:  # noqa: BLE001
        print(f"Error normalizing URL: {e}", file=sys.stderr)  # noqa: T201
        sys.exit(1)
    else:
        print(output_url)  # noqa: T201


if __name__ == "__main__":
    main()  # pragma: no cover
