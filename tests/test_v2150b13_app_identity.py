# Copyright 2026 Prash Balan (@its-me-prash) — GNU AGPL v3.0-or-later
# SPDX-License-Identifier: AGPL-3.0-or-later
"""b13 (H5) — VW EU We Connect app-identity fidelity pin.

The fs-car / MBB command endpoints gate on the app-identification headers. The
hardcoded We Connect app version is bumped to the live build whenever an App
Atlas dismantle confirms it; this pins the current value so it can't silently
drift stale (the lesson from the #503 VW-NA scope regression).
"""
from __future__ import annotations

from pathlib import Path

_VW_EU = Path(__file__).resolve().parents[1] / (
    "custom_components/vag_connect/cariad/api/vw_eu.py"
)


def test_weconnect_app_version_is_current() -> None:
    """Verified against the dismantled com.volkswagen.weconnect APK
    (versionName 3.63.2, androguard 2026-06). Do NOT lower this without a
    fresh dismantle — a fidelity check on the fs-car endpoints rejects stale
    versions, which is exactly how an unverified value regresses a channel."""
    src = _VW_EU.read_text(encoding="utf-8")
    assert '"Volkswagen", "3.63.2"' in src
    assert "3.51.1" not in src  # the stale value must not creep back
