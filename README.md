url-normalize
=============

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

Inspired by Sam Ruby's [urlnorm.py]
(<http://intertwingly.net/blog/2004/08/04/Urlnorm>)

Example:

```sh
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
> https://www.foo.com/foo
```

History:

* 1.4.3: Added LICENSE file
* 1.4.2: Added an optional param sort_query_params (True by default)
* 1.4.1: Added param default_scheme to url_normalize ('https' by default)
* 1.4.0: A bit of code refactoring and cleanup
* 1.3.3: Support empty string and double slash urls (//domain.tld)
* 1.3.2: Same code support both Python 3 and Python 2.
* 1.3.1: Python 3 compatibility
* 1.2.1: PEP8, setup.py
* 1.1.2: support for shebang (#!) urls
* 1.1.1: using 'http' schema by default when appropriate
* 1.1.0: added handling of IDN domains
* 1.0.0: code pep8
* 0.1.0: forked from Sam Ruby's urlnorm.py

License: MIT License
