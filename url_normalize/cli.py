#!/usr/bin/env python
"""Command line interface for url-normalize."""

import argparse
import sys
from importlib.metadata import version

from .url_humanize import url_humanize
from .url_normalize import url_normalize


def main() -> None:
    """Parse arguments and run url_normalize."""
    # Keep normal output and error diagnostics in UTF-8 on every platform.
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(encoding="utf-8", errors="backslashreplace")

    parser = argparse.ArgumentParser(description="Normalize a URL.")
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"%(prog)s {version('url-normalize')}",
    )
    parser.add_argument("url", help="The URL to normalize.")
    parser.add_argument(
        "-s",
        "--default-scheme",
        default="https",
        help="Default scheme if missing, e.g. https or https:. Default: https",
    )
    parser.add_argument(
        "-f",
        "--filter-params",
        action="store_true",
        help=(
            "Filter query parameters using built-in rules unless overridden by -p. "
            "Unknown domains have an empty default allowlist."
        ),
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
        help=(
            "Keep these comma-separated query parameter names (e.g., 'q,id'); "
            "enables filtering without -f. An empty string selects the empty name."
        ),
    )
    parser.add_argument(
        "--param-denylist",
        type=str,
        help=(
            "Remove these comma-separated query parameter names without -f. "
            "Denied names override allowed names. "
            "An empty string selects the empty name."
        ),
    )
    parser.add_argument(
        "--remove-tracking-params",
        action="store_true",
        help=(
            "Remove the built-in set of exact, case-sensitive tracker names "
            "in addition to custom filtering. Disabled by default."
        ),
    )
    parser.add_argument(
        "--sort-query",
        action="store_true",
        help=(
            "Sort query parameters by normalized key, keeping repeated values "
            "in their original order. Disabled by default."
        ),
    )
    parser.add_argument(
        "--collapse-slashes",
        action=argparse.BooleanOptionalAction,
        default=True,
        help=(
            "Collapse repeated path slashes after resolving dot segments "
            "(default: enabled)."
        ),
    )
    parser.add_argument(
        "--remove-trailing-slash",
        action="store_true",
        help="Remove trailing path slashes while keeping the root slash.",
    )
    parser.add_argument(
        "--keep-empty-components",
        action="store_true",
        help=(
            "Keep empty query (?) and fragment (#) delimiters, "
            "including after filtering."
        ),
    )
    parser.add_argument(
        "--strip-fragment",
        action="store_true",
        help=(
            "Remove the entire fragment and its # delimiter, even with "
            "--keep-empty-components. Disabled by default."
        ),
    )
    parser.add_argument(
        "-H",
        "--humanize",
        action="store_true",
        help="Print a human-readable URL that normalizes to the same value.",
    )

    args = parser.parse_args()

    allowlist = (
        args.param_allowlist.split(",") if args.param_allowlist is not None else None
    )
    denylist = (
        args.param_denylist.split(",") if args.param_denylist is not None else None
    )
    transform_url = url_humanize if args.humanize else url_normalize

    try:
        output_url = transform_url(
            args.url,
            default_scheme=args.default_scheme,
            default_domain=args.default_domain,
            filter_params=args.filter_params,
            param_allowlist=allowlist,
            param_denylist=denylist,
            remove_tracking_params=args.remove_tracking_params,
            sort_query=args.sort_query,
            collapse_slashes=args.collapse_slashes,
            remove_trailing_slash=args.remove_trailing_slash,
            keep_empty_components=args.keep_empty_components,
            strip_fragment=args.strip_fragment,
        )
    except Exception as e:  # noqa: BLE001
        print(f"Error normalizing URL: {e}", file=sys.stderr)  # noqa: T201
        sys.exit(1)
    else:
        print(output_url)  # noqa: T201


if __name__ == "__main__":
    main()  # pragma: no cover
