# -*- coding: utf-8 -*-
"""
URI normalizator.

URI Normalization function:
 * Take care of IDN domains.
 * Always provide the URI scheme in lowercase characters.
 * Always provide the host, if any, in lowercase characters.
 * Only perform percent-encoding where it is essential.
 * Always use uppercase A-through-F characters when percent-encoding.
 * Prevent dot-segments appearing in non-relative URI paths.
 * For schemes that define a default authority, use an empty authority if the
   default is desired.
 * For schemes that define an empty path to be equivalent to a path of "/",
   use "/".
 * For schemes that define a port, use an empty port if the default is desired
 * All portions of the URI must be utf-8 encoded NFC from Unicode strings

Inspired by Sam Ruby's urlnorm.py:
    http://intertwingly.net/blog/2004/08/04/Urlnorm
This fork author: Nikolay Panov (<pythonista@npanov.com>)

History:
 * 1.4.0: A bit of code refactoring and cleanup
 * 1.3.2: Support empty string and double slash urls (//domain.tld)
 * 1.3.1: Same code support both Python 3 and Python 2.
 * 1.3: Python 3 compatibility
 * 1.2: PEP8, setup.py
 * 1.1.2: support for shebang (#!) urls
 * 1.1.1: using 'http' schema by default when appropriate
 * 1.1: added handling of IDN domains
 * 1.0: code pep8-zation
 * 0.1: forked from Sam Ruby's urlnorm.py
"""

from __future__ import absolute_import

from .url_normalize import url_normalize

__license__ = "Python"
__version__ = "1.4.0"

__all__ = ["url_normalize"]
