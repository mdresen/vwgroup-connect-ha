# Copyright 2026 Prash Balan (@its-me-prash) — Apache License 2.0
# SPDX-License-Identifier: Apache-2.0
"""MBB OAuth token exchange — the legacy stack that PREDATES the App-Check wall.

The MBB ("msg" / Car-Net) OAuth backend at
``mbboauth-1d.prd.ece.vwg-connect.com/mbbcoauth`` is the pre-CARIAD generation.
A hybrid ``id_token`` minted at ``identity.vwgroup.io`` can be exchanged here
for a **durable, refreshable** MBB bearer — which is exactly the piece missing
for (a) two-way on the brands whose modern CARIAD-BFF token path is gated
behind Google Play-Integrity attestation (VW EU), and (b) legacy MBB-backed
combustion/PHEV cars that the modern IDK apps never onboard.

Grounded, not guessed:
- Token path ``/mbbcoauth/mobile/oauth2/v1/token``, revoke
  ``/mbbcoauth/mobile/oauth2/v1/revoke``, header ``X-Client-Id``, scope
  ``sc2:fal`` and the shared client ``9523ee15-…`` were all read from the
  We Connect e-Remote (``de.volkswagen.carnet.eu.eremote``) and SEAT/CUPRA
  ``mod2connectapp`` DEX in the 2026-06 app-atlas.
- A 2026-06 live probe of ``/mbbcoauth/mobile/oauth2/v1/token`` returned
  **HTTP 403** (auth-reject), NOT a 404 — i.e. the endpoint is live, the path
  is correct, and it rejects on missing credentials rather than behind the
  Play-Integrity wall that blocks the CARIAD BFF.

Scope of THIS module: the token exchange + refresh + revoke only (the auth
foundation). The MBB read path (homeRegion → VSR/FAL) already lives in
``cariad/_mbb.py``; command (S-PIN secure-token) wiring is a separate step.
Nothing here is wired into the live auth chain yet — it is exercised by the
local DAG test harness (``scripts/mbb_dag_test.py``) until a tester confirms a
real token exchange against their account.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any

from aiohttp import ClientError, ClientSession, ClientTimeout

from ..exceptions import AuthenticationError

# ── Endpoints (DEX + live-probe confirmed 2026-06) ──────────────────────────
MBB_OAUTH_BASE = "https://mbboauth-1d.prd.ece.vwg-connect.com/mbbcoauth"
MBB_TOKEN_URL = f"{MBB_OAUTH_BASE}/mobile/oauth2/v1/token"
MBB_REVOKE_URL = f"{MBB_OAUTH_BASE}/mobile/oauth2/v1/revoke"

# Shared legacy MBB client present in BOTH We Connect e-Remote and the
# SEAT/CUPRA mod2 apps (atlas ``_SHARED_UUIDS``). The MBB ``X-Client-Id`` is a
# bare UUID (no ``@apps_vw-dilab_com`` suffix) — a DIFFERENT identifier from
# the IDK/dilab OAuth client.
MBB_SHARED_CLIENT_ID = "9523ee15-f6e0-4eb9-9907-59d058d7e16e"

_MBB_SCOPE = "sc2:fal"
_TIMEOUT = ClientTimeout(total=20)
_UA = "okhttp/3.14.9"


@dataclass
class MbbTokenSet:
    """Token set minted by the MBB OAuth backend.

    Unlike the CARIAD hybrid token, this one carries a usable
    ``refresh_token`` (the whole point — durable, no ~2h re-login).
    """

    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_at: float = 0.0  # Unix ts; 0 = unknown

    def is_valid(self) -> bool:
        return bool(self.access_token)

    def needs_refresh(self) -> bool:
        if not self.expires_at:
            return False
        return time.time() >= self.expires_at - 60


def _headers(client_id: str) -> dict[str, str]:
    return {
        "X-Client-Id": client_id,
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
        "User-Agent": _UA,
    }


def _parse_token_payload(payload: dict[str, Any]) -> MbbTokenSet:
    access = payload.get("access_token", "")
    if not access:
        raise AuthenticationError("MBB token response missing access_token")
    expires_in = payload.get("expires_in")
    expires_at = time.time() + float(expires_in) if expires_in else 0.0
    return MbbTokenSet(
        access_token=access,
        refresh_token=payload.get("refresh_token", ""),
        token_type=payload.get("token_type", "Bearer"),
        expires_at=expires_at,
    )


async def _post_token(
    session: ClientSession, data: dict[str, str], client_id: str
) -> MbbTokenSet:
    try:
        async with session.post(
            MBB_TOKEN_URL, data=data, headers=_headers(client_id), timeout=_TIMEOUT
        ) as resp:
            body = await resp.text()
            if resp.status != 200:
                raise AuthenticationError(
                    f"MBB token exchange HTTP {resp.status}: {body[:200]}"
                )
            try:
                payload = json.loads(body)
            except ValueError as exc:
                raise AuthenticationError(
                    f"MBB token response not JSON: {body[:120]}"
                ) from exc
            return _parse_token_payload(payload)
    except ClientError as exc:
        raise AuthenticationError(f"MBB token exchange failed: {exc}") from exc


async def exchange_id_token(
    session: ClientSession,
    id_token: str,
    *,
    client_id: str = MBB_SHARED_CLIENT_ID,
    scope: str = _MBB_SCOPE,
) -> MbbTokenSet:
    """Exchange a hybrid ``identity.vwgroup.io`` id_token for an MBB bearer.

    Classic Car-Net/MBB grant: ``grant_type=id_token`` with the id_token in the
    ``token`` form field + ``scope=sc2:fal`` and the ``X-Client-Id`` header.
    """
    if not id_token:
        raise AuthenticationError("MBB exchange requires a non-empty id_token")
    data = {"grant_type": "id_token", "token": id_token, "scope": scope}
    return await _post_token(session, data, client_id)


async def refresh(
    session: ClientSession,
    refresh_token: str,
    *,
    client_id: str = MBB_SHARED_CLIENT_ID,
) -> MbbTokenSet:
    """Refresh an MBB bearer using its refresh_token (the durable path)."""
    if not refresh_token:
        raise AuthenticationError("MBB refresh requires a non-empty refresh_token")
    data = {"grant_type": "refresh_token", "token": refresh_token}
    return await _post_token(session, data, client_id)
