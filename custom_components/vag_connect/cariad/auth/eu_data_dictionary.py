# Copyright 2026 Prash Balan (@its-me-prash) — GNU AGPL v3.0-or-later
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Loader for the official EU Data Act Data Dictionary (V5.0 Continuous-Data
spec), re-emitted in this project's format. Maps each spec field UUID →
``{name, unit, type, cluster, description}``.

Used to give human names/units to otherwise-opaque portal field identifiers:
the Vehicle Data Scout annotates its findings with the official name, and raw
field discovery names auto-created diagnostic sensors from it. Pure data — no
network, no HA imports — so it is cheap to import anywhere."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

_DICT_PATH = Path(__file__).with_name("eu_data_dictionary.json")


@lru_cache(maxsize=1)
def _load() -> dict[str, dict[str, Any]]:
    """Load + cache the dictionary (without the ``_meta`` block). Missing or
    corrupt file degrades to an empty map — the dictionary is an enrichment,
    never a hard dependency."""
    try:
        raw = json.loads(_DICT_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    if not isinstance(raw, dict):
        return {}
    return {
        k: v for k, v in raw.items()
        if k != "_meta" and isinstance(v, dict)
    }


def lookup(key: str | None) -> dict[str, Any] | None:
    """Return the spec entry for a field UUID. Accepts a dotted path and falls
    back to its last segment (the portal nests the UUID under a path)."""
    if not key:
        return None
    table = _load()
    entry = table.get(key)
    if entry is None and "." in key:
        entry = table.get(key.rsplit(".", 1)[-1])
    return entry


def describe(key: str | None) -> str | None:
    """Human label for a field UUID — ``'Name (unit)'`` / ``'Name'`` — or None
    when the key is unknown to the spec."""
    entry = lookup(key)
    if not entry:
        return None
    name = entry.get("name")
    if not name:
        return None
    unit = entry.get("unit")
    return f"{name} ({unit})" if unit else str(name)


def field_count() -> int:
    """Number of spec fields available (0 if the dictionary failed to load)."""
    return len(_load())
