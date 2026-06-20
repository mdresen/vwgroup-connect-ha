# Copyright 2026 Prash Balan (@its-me-prash) — GNU AGPL v3.0-or-later
# SPDX-License-Identifier: AGPL-3.0-or-later
"""v2.15.0 — MBB durable-strategy wire-in: pure-function unit tests.

Scope: the deterministic, offline-testable pieces of the MBB two-way
integration (the HTTP orchestration in ``api/vw_eu.py`` + the config-flow
steps need a live VW EU account and are validated by the tester):

  a2 (auth core)
    - ``_mbboauth.jwt_aud`` — JWT aud decode (multi-valued → first)
    - ``_mbboauth.register`` input-guard + endpoint constant
    - ``_device_grant.mbb_dag_config`` — VW-only client+scope (mbb scope)

  a3 (S-PIN SecToken + RLU command core)
    - ``compute_spin_hash`` — SHA-512(fromhex(spin) ++ fromhex(challenge)),
      UPPER (the classic hex-not-utf-8 footgun) — known-answer vector
    - ``validate_spin_format`` — local guard so a malformed PIN fails
      BEFORE a challenge request (a wrong hash burns a lockout try)
    - the rolesrights/RLU URL builders (``/api`` prefix, NO brand/country,
      lock/unlock as the path tail) + the SPIN-completed body shape
    - the response parsers (challenge, completed-token, request-id,
      status, garage VINs)

These stay pure-Python — no HA event loop, no aiohttp — so they run
cleanly and assert real behaviour, not tautologies.
"""

from __future__ import annotations

import base64
import json

import pytest

from custom_components.vag_connect.cariad import _mbb
from custom_components.vag_connect.cariad.auth import _mbboauth
from custom_components.vag_connect.cariad.auth._device_grant import (
    MBB_DAG_CLIENT_ID,
    MBB_DAG_SCOPE,
    mbb_dag_config,
)
from custom_components.vag_connect.cariad.exceptions import AuthenticationError


def _make_jwt(claims: dict) -> str:
    """Build a fake JWT with the given payload claims (header/sig are junk)."""
    payload = base64.urlsafe_b64encode(
        json.dumps(claims).encode()
    ).decode().rstrip("=")
    return f"eyJhbGciOiJSUzI1NiJ9.{payload}.signature"


# ── a3: SPIN hash (the canonical footgun) ─────────────────────────────


class TestComputeSpinHash:
    # Known-answer vector computed independently with the documented
    # algorithm: sha512(bytes.fromhex("1234") + bytes.fromhex(challenge)).
    VECTOR = (
        "1BBA1D16BAFCB2AFD1AD7E2C1A747906B79092DC97E625874CE9ACB1BB94C6DD"
        "1D3DE23DC1FA0D79C87E9A6F1A3DB21FED884886EFA7825B6B484B8265F0E0D0"
    )

    def test_known_answer_vector(self) -> None:
        assert (
            _mbb.compute_spin_hash("1234", "ABCDEF0123456789") == self.VECTOR
        )

    def test_is_uppercase_hex(self) -> None:
        h = _mbb.compute_spin_hash("1234", "ABCDEF0123456789")
        assert h == h.upper()
        assert len(h) == 128  # SHA-512 hex digest

    def test_hex_decoded_not_utf8(self) -> None:
        """The footgun guard: hashing must hex-decode the SPIN, so the
        result must DIFFER from a (wrong) utf-8 encoding of the SPIN."""
        import hashlib  # noqa: PLC0415

        spin, challenge = "1234", "ABCDEF0123456789"
        wrong = hashlib.sha512(
            spin.encode("utf-8") + bytes.fromhex(challenge)
        ).hexdigest().upper()
        assert _mbb.compute_spin_hash(spin, challenge) != wrong

    def test_deterministic(self) -> None:
        a = _mbb.compute_spin_hash("4321", "00FF")
        b = _mbb.compute_spin_hash("4321", "00FF")
        assert a == b


class TestValidateSpinFormat:
    def test_accepts_4_and_6_digit(self) -> None:
        _mbb.validate_spin_format("1234")
        _mbb.validate_spin_format("123456")

    def test_rejects_empty(self) -> None:
        with pytest.raises(ValueError):
            _mbb.validate_spin_format("")

    def test_rejects_odd_length(self) -> None:
        with pytest.raises(ValueError):
            _mbb.validate_spin_format("123")

    def test_rejects_non_hex(self) -> None:
        with pytest.raises(ValueError):
            _mbb.validate_spin_format("XYZW")


# ── a3: URL builders — /api prefix, NO brand/country, path-tail verb ──


class TestRluUrlBuilders:
    SET = "https://mal-1a.prd.ece.vwg-connect.com"
    VIN = "wvwzzz1kz000000aa"

    def test_challenge_lock(self) -> None:
        url = _mbb.build_mbb_spin_challenge_url(self.SET, self.VIN, lock=True)
        assert url == (
            f"{self.SET}/api/rolesrights/authorization/v2/vehicles/"
            f"{self.VIN.upper()}/services/rlu_v1/operations/LOCK/"
            "security-pin-auth-requested"
        )

    def test_challenge_unlock_uses_unlock_op(self) -> None:
        url = _mbb.build_mbb_spin_challenge_url(self.SET, self.VIN, lock=False)
        assert "/operations/UNLOCK/" in url

    def test_completed_url(self) -> None:
        assert _mbb.build_mbb_spin_completed_url(self.SET) == (
            f"{self.SET}/api/rolesrights/authorization/v2/"
            "security-pin-auth-completed"
        )

    def test_action_lock_is_path_tail_no_brand_country(self) -> None:
        url = _mbb.build_mbb_rlu_action_url(self.SET, self.VIN, lock=True)
        assert url == f"{self.SET}/api/bs/rlu/v1/vehicles/{self.VIN.upper()}/lock"
        # The deprecated /{brand}/{country}/.../actions form must NOT appear.
        assert "/actions" not in url
        assert "/VW/" not in url

    def test_action_unlock(self) -> None:
        url = _mbb.build_mbb_rlu_action_url(self.SET, self.VIN, lock=False)
        assert url.endswith("/unlock")

    def test_status_url(self) -> None:
        url = _mbb.build_mbb_rlu_status_url(self.SET, self.VIN, "REQ-1")
        assert url == (
            f"{self.SET}/api/bs/rlu/v1/vehicles/{self.VIN.upper()}/requests/"
            "REQ-1/status"
        )

    def test_content_type_is_remote_lock_unlock_vendor(self) -> None:
        assert _mbb.MBB_RLU_CONTENT_TYPE == (
            "application/vnd.vwg.mbb.RemoteLockUnlock_v1_0_0+xml"
        )


class TestCompletedBody:
    def test_shape(self) -> None:
        body = _mbb.build_mbb_completed_body("L1", "CAFE", "HASHVAL")
        assert body == {
            "securityPinAuthentication": {
                "securityPin": {
                    "challenge": "CAFE",
                    "securityPinHash": "HASHVAL",
                },
                "securityToken": "L1",
            }
        }


# ── a3: response parsers ──────────────────────────────────────────────


class TestParsers:
    def test_parse_challenge_full(self) -> None:
        resp = {
            "securityPinAuthInfo": {
                "securityToken": "LEVEL1",
                "securityPinTransmission": {
                    "challenge": "ABCD", "remainingTries": 3,
                },
            }
        }
        assert _mbb.parse_mbb_spin_challenge(resp) == ("LEVEL1", "ABCD", 3)

    def test_parse_challenge_missing(self) -> None:
        assert _mbb.parse_mbb_spin_challenge(None) == (None, None, None)
        assert _mbb.parse_mbb_spin_challenge({}) == (None, None, None)

    def test_parse_challenge_no_remaining(self) -> None:
        resp = {
            "securityPinAuthInfo": {
                "securityToken": "L1",
                "securityPinTransmission": {"challenge": "AA"},
            }
        }
        assert _mbb.parse_mbb_spin_challenge(resp) == ("L1", "AA", None)

    def test_parse_completed_token(self) -> None:
        assert _mbb.parse_mbb_completed_token({"securityToken": "L2"}) == "L2"
        assert _mbb.parse_mbb_completed_token({}) is None
        assert _mbb.parse_mbb_completed_token(None) is None

    def test_parse_request_id(self) -> None:
        resp = {"rluActionResponse": {"requestId": "REQ-42"}}
        assert _mbb.parse_mbb_rlu_request_id(resp) == "REQ-42"
        assert _mbb.parse_mbb_rlu_request_id({}) is None
        assert _mbb.parse_mbb_rlu_request_id(None) is None

    def test_parse_request_id_coerces_int(self) -> None:
        assert _mbb.parse_mbb_rlu_request_id(
            {"rluActionResponse": {"requestId": 99}}
        ) == "99"

    def test_parse_status_wrapped(self) -> None:
        resp = {"requestStatusResponse": {"status": "request_successful"}}
        assert _mbb.parse_mbb_rlu_status(resp) == "request_successful"

    def test_parse_status_bare(self) -> None:
        assert _mbb.parse_mbb_rlu_status({"status": "request_fail"}) == "request_fail"

    def test_parse_status_missing(self) -> None:
        assert _mbb.parse_mbb_rlu_status(None) is None
        assert _mbb.parse_mbb_rlu_status({}) is None


class TestGarageEnumeration:
    def test_vins_string_list(self) -> None:
        resp = {"userVehicles": {"vehicle": ["VIN1", "VIN2"]}}
        assert _mbb.parse_mbb_vehicle_vins(resp) == ["VIN1", "VIN2"]

    def test_vins_single_string(self) -> None:
        resp = {"userVehicles": {"vehicle": "VINSOLO"}}
        assert _mbb.parse_mbb_vehicle_vins(resp) == ["VINSOLO"]

    def test_vins_object_list(self) -> None:
        resp = {"userVehicles": {"vehicle": [{"vin": "VINOBJ"}]}}
        assert _mbb.parse_mbb_vehicle_vins(resp) == ["VINOBJ"]

    def test_vins_empty(self) -> None:
        assert _mbb.parse_mbb_vehicle_vins(None) == []
        assert _mbb.parse_mbb_vehicle_vins({}) == []
        assert _mbb.parse_mbb_vehicle_vins({"userVehicles": {}}) == []

    def test_vehicles_url(self) -> None:
        url = _mbb.build_mbb_vehicles_url(
            "https://msg.volkswagen.de", "volkswagen", "DE"
        )
        assert url == (
            "https://msg.volkswagen.de/fs-car/usermanagement/users/v1/VW/DE/"
            "vehicles"
        )


# ── a2: auth-core ─────────────────────────────────────────────────────


class TestJwtAud:
    def test_list_aud_returns_first(self) -> None:
        tok = _make_jwt({"aud": ["VWGMBB01DELIV1", "other"]})
        assert _mbboauth.jwt_aud(tok) == "VWGMBB01DELIV1"

    def test_string_aud(self) -> None:
        tok = _make_jwt({"aud": "single-aud"})
        assert _mbboauth.jwt_aud(tok) == "single-aud"

    def test_missing_aud(self) -> None:
        assert _mbboauth.jwt_aud(_make_jwt({"sub": "x"})) is None

    def test_garbage_token(self) -> None:
        assert _mbboauth.jwt_aud("not-a-jwt") is None
        assert _mbboauth.jwt_aud("") is None


class TestRegisterGuards:
    def test_register_url_constant(self) -> None:
        assert _mbboauth.MBB_REGISTER_URL == (
            "https://mbboauth-1d.prd.ece.vwg-connect.com/mbbcoauth/"
            "mobile/register/v1"
        )

    @pytest.mark.asyncio
    async def test_register_rejects_empty_id_token(self) -> None:
        with pytest.raises(AuthenticationError):
            await _mbboauth.register(None, "")  # type: ignore[arg-type]


class TestMbbDagConfig:
    def test_volkswagen_returns_eremote_client_and_mbb_scope(self) -> None:
        cfg = mbb_dag_config("volkswagen")
        assert cfg is not None
        client_id, scope = cfg
        assert client_id == MBB_DAG_CLIENT_ID
        assert client_id.startswith("9496332b-")
        # The load-bearing 'mbb' scope is what makes the id_token aud the
        # MBB backend audience — without it the exchange 400s.
        assert "mbb" in scope.split()
        assert scope == MBB_DAG_SCOPE

    def test_non_vw_brands_return_none(self) -> None:
        for brand in ("audi", "skoda", "seat", "cupra", "porsche", ""):
            assert mbb_dag_config(brand) is None

    def test_case_insensitive(self) -> None:
        assert mbb_dag_config("Volkswagen") is not None


class TestBrandSegmentUnchanged:
    """The rlu path is brandless, but the VSR read path still segments."""

    def test_vw_segment(self) -> None:
        assert _mbb.mbb_brand_segment("volkswagen") == "VW"

    def test_audi_segment(self) -> None:
        assert _mbb.mbb_brand_segment("audi") == "Audi"
