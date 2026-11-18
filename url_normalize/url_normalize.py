"""URL normalize main module.

Copyright (c) 2020 Nikolay Panov
This module is part of url-normalize package and is released under the MIT License:
https://opensource.org/licenses/MIT

"""

from __future__ import annotations

from typing import overload

from ._url import cleanup_url_input, deconstruct_url, reconstruct_url
from .normalize_fragment import normalize_fragment
from .normalize_host import normalize_host
from .normalize_path import normalize_path
from .normalize_port import normalize_port
from .normalize_query import normalize_query
from .normalize_scheme import DEFAULT_SCHEME, normalize_scheme
from .normalize_userinfo import normalize_userinfo
from .param_filter import _ParamRules  # noqa: TC001 - resolve runtime annotations
from .provide_url_domain import provide_url_domain
from .provide_url_scheme import provide_url_scheme


@overload
def url_normalize(
    url: str,
    *,
    default_scheme: str = DEFAULT_SCHEME,
    default_domain: str | None = None,
    filter_params: bool = False,
    param_allowlist: _ParamRules | None = None,
    param_denylist: _ParamRules | None = None,
    remove_tracking_params: bool = False,
    sort_query: bool = False,
    collapse_slashes: bool = True,
    remove_trailing_slash: bool = False,
    keep_empty_components: bool = False,
    strip_fragment: bool = False,
) -> str: ...


@overload
def url_normalize(
    url: None,
    *,
    default_scheme: str = DEFAULT_SCHEME,
    default_domain: str | None = None,
    filter_params: bool = False,
    param_allowlist: _ParamRules | None = None,
    param_denylist: _ParamRules | None = None,
    remove_tracking_params: bool = False,
    sort_query: bool = False,
    collapse_slashes: bool = True,
    remove_trailing_slash: bool = False,
    keep_empty_components: bool = False,
    strip_fragment: bool = False,
) -> None: ...


def url_normalize(  # noqa: PLR0913
    url: str | None,
    *,  # Force keyword-only arguments
    default_scheme: str = DEFAULT_SCHEME,
    default_domain: str | None = None,
    filter_params: bool = False,
    param_allowlist: _ParamRules | None = None,
    param_denylist: _ParamRules | None = None,
    remove_tracking_params: bool = False,
    sort_query: bool = False,
    collapse_slashes: bool = True,
    remove_trailing_slash: bool = False,
    keep_empty_components: bool = False,
    strip_fragment: bool = False,
) -> str | None:
    """URI normalization routine.

    Sometimes you get an URL by a user that just isn't a real
    URL because it contains unsafe characters like ' ' and so on.
    This function can fix some of the problems in a similar way
    browsers handle data entered by the user:

    >>> url_normalize('http://de.wikipedia.org/wiki/Elf (Begriffsklärung)')
    'http://de.wikipedia.org/wiki/Elf%20(Begriffskl%C3%A4rung)'

    Explicit relative references keep their relative form. Document-relative paths
    resolve internal dots, retain unresolved parents, and honor the slash options.

    Params:
        url : str | None : URL to normalize
        default_scheme : str : scheme for bare hosts and network-path references;
            accepts surrounding whitespace and an optional trailing colon
        default_domain : str | None : optional
            Default domain to use for absolute paths (starting with '/')
        filter_params : bool : optional
            Enable built-in allowlist filtering when no custom rule is supplied
            (False by default)
        param_allowlist : optional
            Override with one name, a sequence or set of names, or a domain map whose
            values are single names, sequences or sets. Any value other than None
            enables filtering, including an empty collection, regardless of
            filter_params.
        param_denylist : optional
            Remove one name, a sequence or set of names, or names from a domain map.
            Applied without filter_params; denied names override allowed names.
            An empty collection removes nothing.
        remove_tracking_params : bool : optional
            Remove the built-in set of exact, case-sensitive tracker names
            in addition to custom filtering (False by default). Does not enable
            the built-in domain allowlist; removal overrides allowed names.
        sort_query : bool : optional
            Sort by normalized, percent-encoded query key after filtering,
            retaining equal-key order and value separators (False by default).
        collapse_slashes : bool : optional
            Collapse literal path slashes after resolving dot segments
            (True by default); set False to preserve repeated slashes
        remove_trailing_slash : bool : optional
            Remove trailing literal slashes after dot resolution and optional
            collapsing, keeping the root slash (False by default)
        keep_empty_components : bool : optional
            Preserve query and fragment delimiters when their content is empty,
            including a query emptied by parameter filtering (False by default)
        strip_fragment : bool : optional
            Remove the entire fragment and its delimiter (False by default),
            overriding keep_empty_components for the fragment only

    Returns:
        str | None : a normalized url

    Raises:
        TypeError: If the cleaned URL is nonempty and default_scheme is not a string.
        ValueError: If the cleaned URL is nonempty and default_scheme has invalid
            syntax, even if the URL already has a scheme. URL parsing can also raise
            ValueError for malformed input.

    """
    if url is not None:
        url = cleanup_url_input(url)
    if not url:
        return url
    url = provide_url_domain(url, default_domain)
    url = provide_url_scheme(url, default_scheme)
    url_elements = deconstruct_url(url)
    url_elements = url_elements._replace(host=normalize_host(url_elements.host))
    url_elements = url_elements._replace(
        scheme=normalize_scheme(url_elements.scheme),
        userinfo=normalize_userinfo(url_elements.userinfo),
        query=normalize_query(
            url_elements.query,
            host=url_elements.host,
            filter_params=filter_params,
            param_allowlist=param_allowlist,
            param_denylist=param_denylist,
            remove_tracking_params=remove_tracking_params,
            sort_query=sort_query,
        ),
        query_present=keep_empty_components and url_elements.query_present,
        fragment="" if strip_fragment else normalize_fragment(url_elements.fragment),
        fragment_present=(
            not strip_fragment
            and keep_empty_components
            and url_elements.fragment_present
        ),
    )
    url_elements = url_elements._replace(
        port=normalize_port(url_elements.port, url_elements.scheme),
        path=normalize_path(
            url_elements.path,
            url_elements.scheme,
            collapse_slashes=collapse_slashes,
            remove_trailing_slash=remove_trailing_slash,
        ),
    )
    return reconstruct_url(url_elements)
