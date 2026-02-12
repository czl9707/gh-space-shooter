"""Shared helpers for SVG output encoding."""

from functools import lru_cache


def _to_compact_name(value: int) -> str:
    digits = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    if value == 0:
        return digits[0]
    out = []
    current = value
    base = len(digits)
    while current >= 0:
        current, remainder = divmod(current, base)
        out.append(digits[remainder])
        current -= 1
        if current < 0:
            break
    return "".join(reversed(out))


def _short_hex(color: str) -> str:
    lower = color.lower()
    if len(lower) == 7 and lower[1] == lower[2] and lower[3] == lower[4] and lower[5] == lower[6]:
        return f"#{lower[1]}{lower[3]}{lower[5]}"
    return lower


def _minify_numeric(value: str | None) -> str:
    if value is None:
        return ""
    text = value
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    if text.startswith("0.") and len(text) > 2:
        text = text[1:]
    if text.startswith("-0.") and len(text) > 3:
        text = "-" + text[2:]
    return text or "0"


@lru_cache(maxsize=256)
def _tl_hex(rgb: tuple[int, int, int]) -> str:
    return _short_hex(f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}")


@lru_cache(maxsize=8192)
def _tl_num(value: float) -> str:
    if isinstance(value, int):
        return str(value)
    if abs(value - round(value)) < 1e-9:
        return str(int(round(value)))
    text = f"{value:.6f}".rstrip("0").rstrip(".")
    if text.startswith("0.") and len(text) > 2:
        text = text[1:]
    if text.startswith("-0.") and len(text) > 3:
        text = "-" + text[2:]
    return text or "0"


@lru_cache(maxsize=8192)
def _tl_num_key_time(value: float) -> str:
    if isinstance(value, int):
        return str(value)
    if abs(value - round(value)) < 1e-9:
        return str(int(round(value)))
    text = f"{value:.5f}".rstrip("0").rstrip(".")
    if text.startswith("0.") and len(text) > 2:
        text = text[1:]
    if text.startswith("-0.") and len(text) > 3:
        text = "-" + text[2:]
    return text or "0"
