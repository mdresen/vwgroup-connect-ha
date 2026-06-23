# Copyright 2026 Prash Balan (@its-me-prash) — GNU AGPL v3.0-or-later
# SPDX-License-Identifier: AGPL-3.0-or-later
"""b1/C1 — cross-channel data merge: union the per-channel snapshots for one
VIN (the Golf GTE case: fuel from one channel, SoC from another, odometer from
a third) into a single VehicleData with provenance."""
from __future__ import annotations

import pytest

from custom_components.vag_connect.cariad._channel_merge import merge_channels
from custom_components.vag_connect.cariad.models import VehicleData


class TestChannelMerge:
    def test_complementary_fields_union(self) -> None:
        a = VehicleData(vin="X", fuel_level=40)
        b = VehicleData(vin="X", battery_soc=80)
        merged = merge_channels([("mbb", a), ("eu_data_act", b)])
        assert merged.fuel_level == 40
        assert merged.battery_soc == 80
        assert merged.source_channel == "eu_data_act+mbb"  # sorted join

    def test_overlap_higher_priority_wins(self) -> None:
        a = VehicleData(vin="X", odometer_km=100, fuel_level=40)
        b = VehicleData(vin="X", odometer_km=200, battery_soc=80)
        merged = merge_channels([("brand_native", a), ("eu_data_act", b)])
        assert merged.odometer_km == 100   # first source wins on overlap
        assert merged.fuel_level == 40
        assert merged.battery_soc == 80
        assert merged.source_channel == "brand_native+eu_data_act"

    def test_drivetrain_reclassified_after_merge(self) -> None:
        a = VehicleData(vin="X", fuel_level=40)       # looks ICE alone
        b = VehicleData(vin="X", battery_soc=80)      # looks EV alone
        merged = merge_channels([("mbb", a), ("eu_data_act", b)])
        assert merged.has_battery is True
        assert merged.has_combustion is True
        assert merged.is_hybrid is True
        assert merged.is_electric is False

    def test_single_contributor_named(self) -> None:
        a = VehicleData(vin="X", fuel_level=40)
        b = VehicleData(vin="X")  # all None
        merged = merge_channels([("mbb", a), ("eu_data_act", b)])
        assert merged.fuel_level == 40
        assert merged.source_channel == "mbb"

    def test_all_empty_no_provenance(self) -> None:
        a = VehicleData(vin="X")
        b = VehicleData(vin="X")
        merged = merge_channels([("mbb", a), ("eu_data_act", b)])
        assert merged.source_channel is None

    def test_inputs_not_mutated(self) -> None:
        a = VehicleData(vin="X", fuel_level=40)
        b = VehicleData(vin="X", battery_soc=80)
        merge_channels([("mbb", a), ("eu_data_act", b)])
        assert a.battery_soc is None   # a untouched
        assert b.fuel_level is None    # b untouched
        assert a.source_channel is None

    def test_cross_vin_is_not_merged(self) -> None:
        a = VehicleData(vin="X", fuel_level=40)
        b = VehicleData(vin="Y", battery_soc=80)  # different VIN — must be ignored
        merged = merge_channels([("mbb", a), ("eu_data_act", b)])
        assert merged.battery_soc is None
        assert merged.fuel_level == 40

    def test_empty_sources_raises(self) -> None:
        with pytest.raises(ValueError):
            merge_channels([])
