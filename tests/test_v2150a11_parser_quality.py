# Copyright 2026 Prash Balan (@its-me-prash) — GNU AGPL v3.0-or-later
# SPDX-License-Identifier: AGPL-3.0-or-later
"""v2.15.0a11 — EU Data Act read-path data-quality hardening.

Parity-with-and-beyond TommiG1 on the parser: sentinel filtering (the raw
65535-as-SoC bug), monotonic-aware dedup (odometer never regresses), and a
dataset-level captured-at freshness floor so bare value-fields rank.
"""
from __future__ import annotations

from custom_components.vag_connect.cariad.auth._eu_data_act import (
    _dataset_captured_ts,
    _is_monotonic,
    _is_sentinel,
    _walk_fields,
)


class TestSentinels:
    def test_global_uint_max_dropped(self) -> None:
        out = _walk_fields({"soc": 80, "range_km": 65535, "odo32": 4294967295})
        assert out.get("soc") == "80"
        assert "range_km" not in out  # 65535 = uint16 "no reading"
        assert "odo32" not in out  # 4294967295 = uint32 max

    def test_int32_max_dropped(self) -> None:
        assert _is_sentinel("anything", 2147483647) is True
        assert _is_sentinel("anything", 2147483646) is False

    def test_field_specific_minus1_only_for_charging_time(self) -> None:
        # -1 is a sentinel for charging-time fields…
        out = _walk_fields({"remaining_charging_time": -1, "battery": 60})
        assert "remaining_charging_time" not in out
        assert out.get("battery") == "60"
        # …but a valid reading anywhere else (e.g. a temperature) — must be kept.
        assert _walk_fields({"temperature_c": -1}).get("temperature_c") == "-1"

    def test_tyre_pressure_status_codes_dropped(self) -> None:
        out = _walk_fields(
            {"tyre_pressure_actual_fl": 0, "tyre_pressure_actual_fr": 230}
        )
        assert "tyre_pressure_actual_fl" not in out  # 0 = unsupported
        assert out.get("tyre_pressure_actual_fr") == "230"
        # 0/1 elsewhere is a normal reading
        assert _walk_fields({"door_open": 1}).get("door_open") == "1"

    def test_string_sentinels_also_dropped(self) -> None:
        assert "x" not in _walk_fields({"x": "65535"})

    def test_bool_is_never_a_sentinel(self) -> None:
        assert _is_sentinel("x", True) is False
        assert _walk_fields({"plugged": True}).get("plugged") == "True"


class TestMonotonic:
    def test_odometer_never_regresses_on_older_snapshot(self) -> None:
        # second event is OLDER and LOWER (out-of-order portal delivery)
        payload = [
            {"odometer": 50000, "carCapturedTimestamp": "2026-06-22T10:00:00Z"},
            {"odometer": 49000, "carCapturedTimestamp": "2026-06-22T09:00:00Z"},
        ]
        assert _walk_fields(payload).get("odometer") == "50000"

    def test_odometer_advances_on_higher_reading(self) -> None:
        payload = [
            {"mileage": 49000, "carCapturedTimestamp": "2026-06-22T09:00:00Z"},
            {"mileage": 50000, "carCapturedTimestamp": "2026-06-22T10:00:00Z"},
        ]
        assert _walk_fields(payload).get("mileage") == "50000"

    def test_non_monotonic_uses_latest_ts(self) -> None:
        # SoC legitimately goes DOWN — must follow latest timestamp, not max
        payload = [
            {"soc": 80, "carCapturedTimestamp": "2026-06-22T09:00:00Z"},
            {"soc": 55, "carCapturedTimestamp": "2026-06-22T10:00:00Z"},
        ]
        assert _walk_fields(payload).get("soc") == "55"
        assert _is_monotonic("soc") is False


class TestDatasetCapturedAt:
    def test_captured_time_detected(self) -> None:
        payload = {
            "vehicle_car_captured_timestamp": "2026-06-22T10:00:00Z",
            "soc": 80,
        }
        ts = _dataset_captured_ts(payload)
        assert ts is not None
        # bare value-field still parses fine alongside the captured-time field
        assert _walk_fields(payload).get("soc") == "80"

    def test_max_captured_time_wins(self) -> None:
        payload = [
            {"car_captured_time": "2026-06-22T08:00:00Z"},
            {"car_captured_time": "2026-06-22T12:00:00Z"},
        ]
        ts = _dataset_captured_ts(payload)
        later = _dataset_captured_ts([{"car_captured_time": "2026-06-22T08:00:00Z"}])
        assert ts is not None and later is not None and ts > later

    def test_no_captured_time_is_none(self) -> None:
        assert _dataset_captured_ts({"soc": 80}) is None
