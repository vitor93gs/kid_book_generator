"""TOON conversion utilities as a standalone service.

This module provides two primary helpers used across the application:

- json_to_toon(obj) -> str: Convert a JSON-like dict into a compact TOON
  string (top-level keys flattened, nested dicts encoded as compact JSON)
- toon_to_json(text) -> dict: Parse a TOON string back into a JSON-like
  dictionary. The parser is resilient to simple nested JSON values encoded
  as compact JSON strings.

The functions are intentionally conservative and focused on the project's
character schema use-cases.
"""
from __future__ import annotations

import json
from typing import Any


def json_to_toon(obj: dict[str, Any]) -> str:
    """Convert a JSON-like mapping into a compact TOON string.

    Top-level keys are converted to `key=value` pairs separated by ``|``. If a
    value is a mapping it is safely encoded as compact JSON (no extra
    whitespace) to avoid ambiguity. Lists are joined with commas.

    Args:
        obj: The mapping to convert.

    Returns:
        A compact TOON string representation.
    """
    parts: list[str] = []
    for k, v in obj.items():
        if isinstance(v, (list, tuple)):
            parts.append(f"{k}={','.join(map(str, v))}")
        elif isinstance(v, dict):
            parts.append(f"{k}={json.dumps(v, separators=(',', ':'))}")
        else:
            parts.append(f"{k}={v}")
    return "|".join(parts)


def _parse_value(token: str) -> Any:
    """Parse an individual TOON value token into a Python object.

    The function first attempts to parse the token as JSON (to support nested
    dicts encoded as compact JSON), then falls back to list/number/string
    heuristics.
    """
    try:
        return json.loads(token)
    except Exception:
        if "," in token:
            return [t for t in token.split(",")]
        if token.isdigit():
            return int(token)
        try:
            f = float(token)
            return f
        except Exception:
            return token


def toon_to_json(text: str) -> dict[str, Any]:
    """Parse a TOON-formatted string back into a JSON-like dictionary.

    Supports both pipe-separated (``|``) and newline-separated key/value
    pairs. Values encoded as compact JSON are parsed with ``json.loads``.

    Args:
        text: The TOON string to parse.

    Returns:
        A dictionary of parsed values.
    """
    if not text:
        return {}
    text = text.strip()
    for fence in ("```toon", "```", "```json"):
        if text.startswith(fence) and text.endswith("```"):
            text = text[len(fence):-3].strip()
    if "|" in text:
        tokens = [t.strip() for t in text.split("|") if t.strip()]
    else:
        tokens = [t.strip() for t in text.splitlines() if t.strip()]
    out: dict[str, Any] = {}
    for tok in tokens:
        if "=" in tok:
            k, v = tok.split("=", 1)
        elif ":" in tok:
            k, v = tok.split(":", 1)
        else:
            continue
        k = k.strip()
        v = v.strip()
        out[k] = _parse_value(v)
    return out
