# Copyright 2026 Prash Balan (@its-me-prash) — GNU AGPL v3.0-or-later
# SPDX-License-Identifier: AGPL-3.0-or-later
"""v2.15.0a12 — EU Data Act curated-mapping expansion (additive) + unmapped log."""
from __future__ import annotations

from custom_components.vag_connect.cariad.auth._eu_data_act import (
    map_dataset_to_vehicle_data,
)
from custom_components.vag_connect.cariad.models import VehicleData


def _map(fields: dict[str, str]) -> VehicleData:
    return map_dataset_to_vehicle_data(fields, VehicleData(vin="X"))


class TestNewMappings:
    def test_charge_rate(self) -> None:
        assert _map({"battery_state_report.charge_rate": "12"}).charging_rate_kmh == 12

    def test_plug_state_connected(self) -> None:
        d = _map({"charging_plug1_connectionstate": "connected"})
        assert d.plug_state == "connected"
        assert d.plug_connected is True

    def test_plug_state_disconnected(self) -> None:
        d = _map({"plug_connection_state": "disconnected"})
        assert d.plug_connected is False


class TestRegressionExistingMappingsUntouched:
    def test_soc_still_maps(self) -> None:
        assert _map({"soc": "80"}).battery_soc == 80

    def test_odometer_still_maps(self) -> None:
        assert _map({"mileage": "50000"}).odometer_km == 50000

    def test_unmapped_fields_are_ignored_not_fatal(self) -> None:
        d = _map({"totally_unknown_field": "1", "soc": "80"})
        assert d.battery_soc == 80  # known maps, unknown silently ignored

    def test_empty_fields_safe(self) -> None:
        d = _map({})
        assert d.vin == "X"
        assert d.battery_soc is None
