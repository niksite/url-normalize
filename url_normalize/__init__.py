"""URI normalizator."""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from future import standard_library

standard_library.install_aliases()

# pylint: disable=C0413
from .url_normalize import url_normalize  # NOQA
