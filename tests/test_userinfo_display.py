"""Keep credential data distinct from URL separators in readable output."""

from urllib.parse import unquote, urlsplit

import pytest

from url_normalize import url_humanize, url_normalize


@pytest.mark.parametrize(
    ("credentials", "expected"),
    [
        ("alice%40example.net:secret", "alice%40example.net:secret"),
        ("user:p%40ss", "user:p%40ss"),
        ("alice%40example.net", "alice%40example.net"),
        ("us%C3%A9r%40example.net:p%C3%A4ss", "usér%40example.net:päss"),
        ("us%C3%A9r%3Aname:p%C3%A4ss", "usér%3Aname:päss"),
        ("us%C3%A9r:p%2F%C3%A4ss", "usér:p%2Fäss"),
        ("us%C3%A9r:p%3B%C3%A4ss", "usér:p%3Bäss"),
        ("us%C3%A9r%5B:p%5D%C3%A4ss", "usér%5B:p%5Däss"),
        ("user%2540name:pass", "user%2540name:pass"),
        ("user%40name:p%FFss", "user%40name:p%FFss"),
        ("User:PaSS", "User:PaSS"),
        ("us%C3%A9r:p%C3%A4ss", "usér:päss"),
    ],
)
def test_humanize_credentials_preserves_encoded_separators(credentials, expected):
    """Retain literal data escapes while showing safe Unicode and original case."""
    # normalize-url 10.0.0's stripAuthentication:false cases also retain %3A/%40:
    # https://github.com/sindresorhus/normalize-url/blob/v10.0.0/test.js
    value = f"https://{credentials}@example.com/resource"
    result = url_humanize(value)
    assert result == f"https://{expected}@example.com/resource"
    assert url_normalize(result) == url_normalize(value)
    assert url_humanize(result) == result
    original, displayed = urlsplit(value), urlsplit(result)
    assert displayed.netloc.count("@") == 1
    assert displayed.hostname == original.hostname
    assert unquote(displayed.username or "") == unquote(original.username or "")
    assert unquote(displayed.password or "") == unquote(original.password or "")


def test_humanize_credentials_preserves_other_components_and_options():
    """Protect only credential escapes while retaining selected URL policies."""
    value = "https://user%40name:p%40ss@example.com/a//b/?email=a%40b&drop=1#@anchor"
    result = url_humanize(
        value,
        collapse_slashes=False,
        remove_trailing_slash=True,
        param_denylist="drop",
    )
    assert result == ("https://user%40name:p%40ss@example.com/a//b?email=a%40b#@anchor")


def test_humanize_ftp_email_username():
    """Use the same credential boundary rule beyond HTTP URLs."""
    value = "ftp://user%40example.net:pass@example.com/file"
    assert url_humanize(value) == value
