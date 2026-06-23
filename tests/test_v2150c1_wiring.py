# Copyright 2026 Prash Balan (@its-me-prash) — GNU AGPL v3.0-or-later
# SPDX-License-Identifier: AGPL-3.0-or-later
"""b1/C1 wiring — client supplementary-channel readers + coordinator merge glue.
Single-channel (no supplementary armed) stays byte-for-byte unchanged; commands
and get_status are never touched."""
from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import AsyncMock, MagicMock

from custom_components.vag_connect.cariad.api.vw_eu import VWEUClient
from custom_components.vag_connect.cariad.exceptions import AuthenticationError
from custom_components.vag_connect.cariad.models import VehicleData
from custom_components.vag_connect.coordinator import VagConnectCoordinator


def _client() -> VWEUClient:
    return VWEUClient(MagicMock(), "u@t.de", "pw")


class TestSupplementaryReaders:
    def test_empty_when_not_armed(self) -> None:
        assert _client().supplementary_readers("VIN") == []

    def test_lists_armed_authproxy(self) -> None:
        c = _client()
        conn = MagicMock()
        conn.get_vehicle_data = AsyncMock(
            return_value=VehicleData(vin="VIN", odometer_km=5)
        )
        c._supplementary_authproxy = conn
        readers = c.supplementary_readers("VIN")
        assert len(readers) == 1
        assert readers[0][0] == "website_authproxy"
        assert asyncio.run(readers[0][1]).odometer_km == 5

    def test_read_authproxy_reauth_retry(self) -> None:
        c = _client()
        conn = MagicMock()
        conn.get_vehicle_data = AsyncMock(
            side_effect=[AuthenticationError("stale"), VehicleData(vin="VIN", odometer_km=7)]
        )
        conn.refresh = AsyncMock()
        res = asyncio.run(c._read_authproxy(conn, "VIN"))
        assert res is not None and res.odometer_km == 7
        conn.refresh.assert_awaited_once()

    def test_read_authproxy_error_is_none(self) -> None:
        c = _client()
        conn = MagicMock()
        conn.get_vehicle_data = AsyncMock(side_effect=RuntimeError("boom"))
        assert asyncio.run(c._read_authproxy(conn, "VIN")) is None


def _coord_stub(client: Any, entry_data: dict[str, Any]) -> Any:
    stub = type("S", (), {})()
    stub._cariad_client = client
    stub.entry = MagicMock()
    stub.entry.data = entry_data
    stub._primary_channel_name = VagConnectCoordinator._primary_channel_name.__get__(stub)
    return stub


class TestPrimaryChannelName:
    def test_eu_portal(self) -> None:
        client = MagicMock()
        client._eu_portal = object()
        assert _coord_stub(client, {})._primary_channel_name() == "eu_data_act"

    def test_website(self) -> None:
        from custom_components.vag_connect.const import CONF_WEBSITE_AUTHPROXY
        stub = _coord_stub(MagicMock(), {CONF_WEBSITE_AUTHPROXY: True})
        assert stub._primary_channel_name() == "website_authproxy"

    def test_mbb(self) -> None:
        client = MagicMock()
        client._eu_portal = None
        stub = _coord_stub(client, {"dag_initial_tokens": {"strategy": "mbb"}})
        assert stub._primary_channel_name() == "mbb"


class TestMergeSupplementary:
    def test_no_readers_attr_returns_primary(self) -> None:
        stub = _coord_stub(MagicMock(spec=[]), {})
        primary = VehicleData(vin="X", battery_soc=80)
        out = asyncio.run(VagConnectCoordinator._merge_supplementary(stub, "X", primary))
        assert out is primary

    def test_empty_readers_returns_primary(self) -> None:
        client = MagicMock()
        client.supplementary_readers = MagicMock(return_value=[])
        primary = VehicleData(vin="X", battery_soc=80)
        out = asyncio.run(
            VagConnectCoordinator._merge_supplementary(_coord_stub(client, {}), "X", primary)
        )
        assert out is primary

    def test_merges_supplementary_onto_primary(self) -> None:
        client = MagicMock()
        client._eu_portal = object()  # primary name → eu_data_act

        async def _supp() -> VehicleData:
            return VehicleData(vin="X", odometer_km=12345)

        client.supplementary_readers = MagicMock(
            return_value=[("website_authproxy", _supp())]
        )
        primary = VehicleData(vin="X", battery_soc=80)
        out = asyncio.run(
            VagConnectCoordinator._merge_supplementary(_coord_stub(client, {}), "X", primary)
        )
        assert out.battery_soc == 80          # primary kept
        assert out.odometer_km == 12345       # supplementary filled the gap
        assert out.source_channel == "eu_data_act+website_authproxy"
