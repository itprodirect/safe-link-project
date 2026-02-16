"""Analysis modules for Link Safety Hub."""

from lsh.modules.ascii_lookalike import AsciiLookalikeDetector
from lsh.modules.email_auth import EmailAuthDetector
from lsh.modules.homoglyph import HomoglyphDetector
from lsh.modules.net_ip import NetIPDetector
from lsh.modules.redirect import RedirectChainDetector
from lsh.modules.url_structure import URLStructureDetector

__all__ = [
    "AsciiLookalikeDetector",
    "EmailAuthDetector",
    "HomoglyphDetector",
    "NetIPDetector",
    "RedirectChainDetector",
    "URLStructureDetector",
]
