import re
import unicodedata
from dataclasses import dataclass

_PREFIX = "go"


@dataclass(frozen=True, slots=True)
class Route:
    node: str
    args: tuple[str, ...] = ()


def encode(node: str, *args: str) -> str:
    """Option id for navigating to `node`. Self-contained, so taps on old menus still work."""
    return ":".join((_PREFIX, node, *args))


def decode(option_id: str) -> Route | None:
    parts = option_id.split(":")
    if len(parts) < 2 or parts[0] != _PREFIX or not parts[1]:
        return None
    return Route(node=parts[1], args=tuple(parts[2:]))


def normalize(text: str) -> str:
    """Lowercase, strip accents and punctuation: '¿Envíos?' -> 'envios'."""
    decomposed = unicodedata.normalize("NFKD", text.lower())
    stripped = "".join(c for c in decomposed if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", stripped).strip()
