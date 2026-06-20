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
import sys
from pathlib import Path

# Repo root on sys.path so the custom_components package imports.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


async def main(brand: str) -> int:
    from aiohttp import ClientSession

    from custom_components.vag_connect.cariad.auth import _mbboauth
    from custom_components.vag_connect.cariad.auth._device_grant import (
        DAG_ENABLED_BRANDS,
        DeviceAuthorizationGrant,
    )
    from custom_components.vag_connect.cariad.models import BRANDS

    if brand not in DAG_ENABLED_BRANDS:
        print(f"[!] '{brand}' is not DAG-enabled. Pick one of: "
              f"{sorted(DAG_ENABLED_BRANDS)}")
        return 2
    cfg = BRANDS[brand]
    print(f"[*] Brand: {brand}  client_id: {cfg.client_id[:8]}…")

    async with ClientSession() as session:
        dag = DeviceAuthorizationGrant(session, cfg.client_id, scope="openid profile")
        print("[*] Requesting device code …", flush=True)
        dc = await dag.request_device_code()

        print("\n" + "=" * 64)
        print("  OPEN THIS LINK IN YOUR BROWSER AND CONFIRM THE LOGIN:")
        print("   ", dc.verification_uri_complete or dc.verification_uri)
        print("  (if the code isn't pre-filled, enter:", dc.user_code, ")")
        print("  Waiting up to", dc.expires_in, "s for you to confirm …")
        print("=" * 64 + "\n", flush=True)

        try:
            tokens = await dag.poll_for_tokens(dc.device_code, dc.interval, dc.expires_in)
        except Exception as exc:  # noqa: BLE001
            print(f"[!] device-grant did not complete: {exc}")
            return 1

        print(f"[ok] got id_token (len={len(tokens.id_token)}), "
              f"access_token (len={len(tokens.access_token)}). NOT printing them.")

        # ── The actual MBB test: exchange the id_token for an MBB bearer ──
        candidates = {
            "shared mod2/eRemote 9523ee15": _mbboauth.MBB_SHARED_CLIENT_ID,
            "VW e-Remote dilab 9496332b": "9496332b-ea03-4091-a224-8c746b885068@apps_vw-dilab_com",
        }
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
                print(f"    [rejected] {exc}")

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
