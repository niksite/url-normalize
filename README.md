url-normalize
=============

URI Normalization function:

Take care of IDN domains.
Always provide the URI scheme in lowercase characters.
Always provide the host, if any, in lowercase characters.
Only perform percent-encoding where it is essential.
Always use uppercase A-through-F characters when percent-encoding.
Prevent dot-segments appearing in non-relative URI paths.
For schemes that define a default authority, use an empty authority if the default is desired.
For schemes that define an empty path to be equivalent to a path of "/", use "/".
For schemes that define a port, use an empty port if the default is desired
All portions of the URI must be utf-8 encoded NFC from Unicode strings
Inspired by Sam Ruby's urlnorm.py: http://intertwingly.net/blog/2004/08/04/Urlnorm

History:

10 Feb 2010: support for shebang (#!) urls
28 Feb 2010: using 'http' schema by default when appropriate
28 Feb 2010: added handling of IDN domains
28 Feb 2010: code pep8-zation
27 Feb 2010: forked from Sam Ruby's urlnorm.py
