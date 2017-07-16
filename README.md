url-normalize
=============

[![Build Status](https://travis-ci.org/niksite/url-normalize.svg?branch=master)](https://travis-ci.org/niksite/url-normalize)
[![Coverage Status](https://coveralls.io/repos/github/niksite/url-normalize/badge.svg?branch=master)](https://coveralls.io/github/niksite/url-normalize?branch=master)

URI Normalization function:
   * Take care of IDN domains.
   * Always provide the URI scheme in lowercase characters.
   * Always provide the host, if any, in lowercase characters.
   * Only perform percent-encoding where it is essential.
   * Always use uppercase A-through-F characters when percent-encoding.
   * Prevent dot-segments appearing in non-relative URI paths.
   * For schemes that define a default authority, use an empty authority if the default is desired.
   * For schemes that define an empty path to be equivalent to a path of "/", use "/".
   * For schemes that define a port, use an empty port if the default is desired
   * All portions of the URI must be utf-8 encoded NFC from Unicode strings

Inspired by Sam Ruby's urlnorm.py: http://intertwingly.net/blog/2004/08/04/Urlnorm

Example:
```
$ pip install url-normalize
Collecting url-normalize
...
Successfully installed future-0.16.0 url-normalize-1.3.3
$ python
Python 3.6.1 (default, Jul  8 2017, 05:00:20)
[GCC 4.9.2] on linux
Type "help", "copyright", "credits" or "license" for more information.
> from url_normalize import url_normalize
> print(url_normalize('www.foo.com:80/foo'))
> http://www.foo.com/foo
```

History:
   * 07 Jul 2017: Python 2/3 compatibility.
   * 05 Jan 2016: Python 3 compatibility
   * 29 Dec 2015: PEP8, setup.py
   * 10 Mar 2010: support for shebang (#!) urls
   * 28 Feb 2010: using 'http' schema by default when appropriate
   * 28 Feb 2010: added handling of IDN domains
   * 28 Feb 2010: code pep8-zation
   * 27 Feb 2010: forked from Sam Ruby's urlnorm.py

License: "Python" (PSF) License
