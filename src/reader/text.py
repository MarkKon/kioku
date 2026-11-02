"""Small text helpers shared by search and output."""

import re
import unicodedata


def norm(text: str) -> str:
    """Lower-case ASCII words, for matching: `\\int` → `int`, `Itô` → `ito`."""
    text = re.sub(r"\\([a-zA-Z]+)", r" \1 ", text)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def matches(term: str, hay: str) -> bool:
    """Every word of the term occurs in the (normed) haystack."""
    words = norm(term).split()
    return bool(words) and all(w in hay for w in words)


def short(text: str, n: int = 60) -> str:
    text = " ".join(text.split())
    return text if len(text) <= n else text[: n - 1] + "…"
