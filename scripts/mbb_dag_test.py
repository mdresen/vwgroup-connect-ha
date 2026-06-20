#!/usr/bin/env python3
# Copyright 2026 Prash Balan (@its-me-prash) — Apache License 2.0
"""Local DAG + MBB live test harness.

Drives the RFC-8628 Device Authorization Grant for a chosen brand: prints a
verification LINK you open in your browser and confirm (your credentials stay
in YOUR browser — never in this script). Once you confirm, it obtains a real
``identity.vwgroup.io`` id_token and uses it to test the MBB token exchange
(``cariad/auth/_mbboauth.py``) against the LIVE server — proving whether the
legacy MBB path mints a durable refreshable token past the Play-Integrity wall.

NEVER prints tokens — only lengths, booleans and HTTP status codes.

Usage:  py scripts/mbb_dag_test.py [skoda|audi|seat|cupra]   (default: skoda)
"""

from __future__ import annotations

import asyncio
import base64
import json
import sys
from pathlib import Path
from typing import Any

# Repo root on sys.path so the custom_components package imports.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# MBB register endpoint (classic Car-Net flow) — grounded in the e-Remote DEX.
_MBB_REGISTER_URL = (
    "https://mbboauth-1d.prd.ece.vwg-connect.com/mbbcoauth/mobile/register/v1"
)
_MBB_UA = "WeConnect/5.17.6 (Android 14; okhttp/3.14.9)"


def _jwt_claims(token: str) -> dict[str, Any]:
    """Decode a JWT's PUBLIC payload claims (aud/iss/exp/azp). Never returns or
    logs the signature/raw token — just the metadata claims used to reason
    about compatibility."""
    try:
        payload_b64 = token.split(".")[1]
        payload_b64 += "=" * (-len(payload_b64) % 4)  # pad
        data = json.loads(base64.urlsafe_b64decode(payload_b64))
        return {k: data.get(k) for k in ("iss", "aud", "azp", "exp", "scope")}
    except Exception:  # noqa: BLE001
        return {}


async def _mbb_register(
    session: Any, id_token: str, desired_client_id: str | None = None
) -> str | None:
    """POST the classic Car-Net MBB register/v1 step. Returns the registered
    client_id on success, else None. ``desired_client_id`` pins the client_id
    in the body so the registered client == the id_token's aud (MBB requires
    id_token.aud == X-Client-Id at the token exchange)."""
    body = {
        "client_name": "vag-connect-mbb-probe",
        "platform": "google",
        "client_brand": "VW",
        "appId": "de.volkswagen.carnet.eu.eremote",
        "appName": "WeConnect",
        "appVersion": "5.17.6",
        "id_token": id_token,
    }
    if desired_client_id:
        body["client_id"] = desired_client_id
        body["scope"] = "sc2:fal"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": _MBB_UA,
        "Authorization": f"Bearer {id_token}",
    }
    try:
        async with session.post(_MBB_REGISTER_URL, json=body, headers=headers) as resp:
            text = await resp.text()
            if resp.status in (200, 201):
                try:
                    cid = json.loads(text).get("client_id")
                except ValueError:
                    cid = None
                print(f"    [register OK] HTTP {resp.status} — client_id "
                      f"{'returned: ' + cid[:8] + '…' if cid else 'NOT in response'}")
                return cid
            print(f"    [register rejected] HTTP {resp.status}: {text[:160]}")
            return None
    except Exception as exc:  # noqa: BLE001
        print(f"    [register error] {exc}")
        return None


async def main(brand: str) -> int:
    from aiohttp import ClientSession

    from custom_components.vag_connect.cariad.auth import _mbboauth
    from custom_components.vag_connect.cariad.auth._device_grant import (
        DAG_ENABLED_BRANDS,
        DeviceAuthorizationGrant,
        portal_dag_config,
    )
    from custom_components.vag_connect.cariad.models import BRANDS

    # Optional 2nd CLI arg = an explicit client_id override (to test whether a
    # specific client — e.g. the e-Remote 9496332b — is device-grant-able, so
    # its id_token's aud matches what MBB wants).
    override = sys.argv[2] if len(sys.argv) > 2 else None

    # Resolve the device-grant client. VW EU's *app* client is DAG-dead
    # (unauthorized_client), but its EU-Data-Act *portal* client works at the
    # same /oidc/v1/device_authorization endpoint (live-verified 2026-06-12) —
    # so "volkswagen" routes through the portal client here.
    portal = portal_dag_config(brand)
    if override:
        client_id, scope, route = override, "openid profile cars", "override"
    elif brand in DAG_ENABLED_BRANDS:
        client_id, scope, route = BRANDS[brand].client_id, "openid profile", "app"
    elif portal is not None:
        client_id, scope, route = portal[0], portal[1], "portal"
    else:
        print(f"[!] '{brand}' has no device-grant route. App-DAG: "
              f"{sorted(DAG_ENABLED_BRANDS)}; portal-DAG: volkswagen/seat/cupra.")
        return 2
    print(f"[*] Brand: {brand}  route: {route}-device-grant  "
          f"client_id: {client_id[:8]}…  scope: {scope}")

    async with ClientSession() as session:
        dag = DeviceAuthorizationGrant(
            session, client_id, scope=scope,
            strategy="device_grant_portal" if route == "portal" else "device_grant",
        )
        print("[*] Requesting device code …", flush=True)
        dc = await dag.request_device_code()

        print("\n" + "=" * 64)
        print("  OPEN THIS LINK IN YOUR BROWSER AND CONFIRM THE LOGIN:")
        print("   ", dc.verification_uri_complete or dc.verification_uri)
        print("  (if the code isn't pre-filled, enter:", dc.user_code, ")")
        print("  Waiting up to", dc.expires_in, "s for you to confirm …")
        print("=" * 64 + "\n", flush=True)

        try:
            tokens = await dag.poll_for_tokens(
                dc.device_code, interval=dc.interval, expires_in=dc.expires_in)
        except Exception as exc:  # noqa: BLE001
            print(f"[!] device-grant did not complete: {exc}")
            return 1

        print(f"[ok] got id_token (len={len(tokens.id_token)}), "
              f"access_token (len={len(tokens.access_token)}). NOT printing them.")

        # ── Decode the id_token's PUBLIC claims (aud/iss/exp only — never the
        #    signature/token). aud tells us immediately whether this token is
        #    even MBB-compatible (MBB binds to a recognised app aud). ──
        claims = _jwt_claims(tokens.id_token)
        print(f"[*] id_token claims:  iss={claims.get('iss')}  "
              f"aud={claims.get('aud')}  azp={claims.get('azp')}")

        # ── Step 1: MBB register (the missing step). Classic Car-Net flow
        #    POSTs the id_token + app metadata to /mobile/register/v1 and gets
        #    back the X-Client-Id to use for the token exchange. ──
        # Pin the register to the id_token's own aud so registered == aud.
        aud = claims.get("aud")
        aud_str = aud[0] if isinstance(aud, list) else aud
        print(f"\n[*] MBB register/v1 (pinned client_id = aud {str(aud_str)[:8]}…) …",
              flush=True)
        reg_client_id = await _mbb_register(session, tokens.id_token, desired_client_id=aud_str)

        # ── Step 2: token exchange. Try (a) the id_token's own aud as
        #    X-Client-Id (the match MBB wants), (b) whatever register returned,
        #    (c) the static candidates. ──
        candidates: dict[str, str] = {}
        if aud_str:
            candidates["aud-as-clientid " + str(aud_str)[:8]] = str(aud_str)
        if reg_client_id and reg_client_id != aud_str:
            candidates["REGISTERED " + reg_client_id[:8]] = reg_client_id
        candidates["shared mod2/eRemote 9523ee15"] = _mbboauth.MBB_SHARED_CLIENT_ID
        any_ok = False
        for label, cid in candidates.items():
            print(f"\n[*] MBB exchange with X-Client-Id = {label} …", flush=True)
            try:
                mbb = await _mbboauth.exchange_id_token(session, tokens.id_token, client_id=cid)
                print(f"    [OK] HTTP 200 — access_token len={len(mbb.access_token)}, "
                      f"durable refresh_token present: {bool(mbb.refresh_token)}, "
                      f"expires_at_set={bool(mbb.expires_at)}")
                any_ok = True
            except Exception as exc:  # noqa: BLE001
                # exception message already carries the HTTP status + body head
                print(f"    [rejected] {str(exc)[:160]}")

        print("\n" + ("=" * 64))
        if any_ok:
            print("  RESULT: the MBB path MINTED a token past the App-Check wall. ")
            print("  The MBB adapter approach is viable — durable two-way is on.")
        else:
            print("  RESULT: no candidate client was accepted by the MBB endpoint.")
            print("  (id_token aud may need to match the X-Client-Id, or the flow ")
            print("   needs the mbbcoauth/mobile/register/v1 step first.)")
        print("=" * 64)
    return 0


if __name__ == "__main__":
    brand_arg = sys.argv[1].lower() if len(sys.argv) > 1 else "skoda"
    raise SystemExit(asyncio.run(main(brand_arg)))
