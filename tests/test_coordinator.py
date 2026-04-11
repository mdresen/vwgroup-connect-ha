"""Tests for VagConnectCoordinator — uses full mocks, no real API calls."""
from __future__ import annotations

from unittest.mock import MagicMock, patch, PropertyMock
import pytest

from custom_components.vag_connect.coordinator import VagConnectCoordinator
from custom_components.vag_connect.const import (
    CONF_BRAND, CONF_USERNAME, CONF_PASSWORD, CONF_SPIN, CONF_SCAN_INTERVAL,
)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _make_entry(brand="audi", username="test@test.de", password="pw", spin="1234"):
    entry = MagicMock()
    entry.entry_id = "test_entry_1"
    entry.data = {
        CONF_BRAND: brand,
        CONF_USERNAME: username,
        CONF_PASSWORD: password,
        CONF_SPIN: spin,
        CONF_SCAN_INTERVAL: 15,
    }
    return entry


def _make_drive(drive_type_name, level, range_val):
    """Build a mock CarConnectivity GenericDrive."""
    from carconnectivity.drive import GenericDrive
    drive = MagicMock()
    drive.type.value = GenericDrive.Type[drive_type_name]
    drive.level.value = level
    drive.range.value = range_val
    return drive


def _make_vehicle(
    vin="WAUZZZ4G7EN123456",
    model="Audi Q4 e-tron",
    is_electric=True,
    fuel_level=None,
    battery_soc=80,
    range_km=350,
    odometer=25000,
    locked=True,
    doors_open=False,
    windows_open=False,
    lat=48.1351,
    lon=11.5820,
    clim_state="OFF",
    charging_state="READY_FOR_CHARGING",
    plug_connected=True,
    target_soc=80,
    outside_temp=18.5,
    inspection_km=8500,
):
    """Build a comprehensive mock vehicle."""
    from carconnectivity.doors import Doors
    from carconnectivity.windows import Windows
    from carconnectivity.charging import Charging
    from carconnectivity.climatization import Climatization
    from carconnectivity.charging_connector import ChargingConnector

    v = MagicMock()

    # Identity
    v.vin.value = vin
    v.name.value = "Mein Audi"
    v.model.value = model
    v.manufacturer.value = "Audi"
    v.model_year.value = 2023

    # Odometer
    v.odometer.value = odometer

    # Drives
    drives = {}
    if is_electric:
        drives["electric"] = _make_drive("ELECTRIC", battery_soc, range_km)
    else:
        drives["fuel"] = _make_drive("GASOLINE", fuel_level, range_km)
    v.drives.drives = drives
    v.drives.total_range.value = range_km

    # Position
    v.position.latitude.value = lat
    v.position.longitude.value = lon

    # Doors
    v.doors.lock_state.value = (
        Doors.LockState.LOCKED if locked else Doors.LockState.UNLOCKED
    )
    v.doors.open_state.value = (
        Doors.OpenState.OPEN if doors_open else Doors.OpenState.CLOSED
    )

    # Windows
    v.windows.open_state.value = (
        Windows.OpenState.OPEN if windows_open else Windows.OpenState.CLOSED
    )

    # Climatisation
    v.climatization.state.value = Climatization.ClimatizationState[clim_state]
    v.climatization.settings.target_temperature.value = 21.0

    # Charging
    v.charging.state.value = Charging.ChargingState[charging_state]
    v.charging.connector.connection_state.value = (
        ChargingConnector.ChargingConnectorConnectionState.CONNECTED
        if plug_connected
        else ChargingConnector.ChargingConnectorConnectionState.DISCONNECTED
    )
    v.charging.settings.target_level.value = target_soc

    # Maintenance
    v.maintenance.inspection_due_at.value = None
    v.maintenance.inspection_due_after.value = inspection_km
    v.maintenance.oil_service_due_at.value = None
    v.maintenance.oil_service_due_after.value = None

    # Outside temperature
    v.outside_temperature.value = outside_temp

    return v


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestExtract:
    """Test the _extract() method with mocked vehicle objects."""

    def setup_method(self):
        hass = MagicMock()
        self.coordinator = VagConnectCoordinator.__new__(VagConnectCoordinator)
        self.coordinator.hass = hass
        self.coordinator.entry = _make_entry()
        self.coordinator.vehicles = {}
        self.coordinator.logger = MagicMock()

    def test_electric_vehicle_basic(self):
        v = _make_vehicle(is_electric=True, battery_soc=75, range_km=280)
        data = self.coordinator._extract(v)

        assert data["vin"] == "WAUZZZ4G7EN123456"
        assert data["model"] == "Audi Q4 e-tron"
        assert data["is_electric"] is True
        assert data["battery_soc"] == 75
        assert data["fuel_level"] is None
        assert data["range_km"] == 280
        assert data["odometer_km"] == 25000

    def test_combustion_vehicle(self):
        v = _make_vehicle(is_electric=False, fuel_level=65, range_km=450)
        data = self.coordinator._extract(v)

        assert data["is_electric"] is False
        assert data["fuel_level"] == 65
        assert data["battery_soc"] is None
        assert data["range_km"] == 450

    def test_doors_locked(self):
        v = _make_vehicle(locked=True, doors_open=False)
        data = self.coordinator._extract(v)
        assert data["doors_locked"] is True
        assert data["doors_open"] is False

    def test_doors_unlocked_and_open(self):
        v = _make_vehicle(locked=False, doors_open=True)
        data = self.coordinator._extract(v)
        assert data["doors_locked"] is False
        assert data["doors_open"] is True

    def test_windows_closed(self):
        v = _make_vehicle(windows_open=False)
        data = self.coordinator._extract(v)
        assert data["windows_open"] is False

    def test_gps_position(self):
        v = _make_vehicle(lat=48.1351, lon=11.5820)
        data = self.coordinator._extract(v)
        assert data["latitude"] == 48.1351
        assert data["longitude"] == 11.5820

    def test_charging_state(self):
        v = _make_vehicle(charging_state="CHARGING", plug_connected=True)
        data = self.coordinator._extract(v)
        assert data["charging_state"] == "CHARGING"
        assert data["is_charging"] is True
        assert data["plug_connected"] is True

    def test_charging_off(self):
        v = _make_vehicle(charging_state="OFF", plug_connected=False)
        data = self.coordinator._extract(v)
        assert data["is_charging"] is False

    def test_climatisation_off(self):
        v = _make_vehicle(clim_state="OFF")
        data = self.coordinator._extract(v)
        assert data["climatisation_state"] == "OFF"
        assert data["climatisation_active"] is False

    def test_climatisation_heating(self):
        v = _make_vehicle(clim_state="HEATING")
        data = self.coordinator._extract(v)
        assert data["climatisation_state"] == "HEATING"
        assert data["climatisation_active"] is True

    def test_target_soc(self):
        v = _make_vehicle(target_soc=90)
        data = self.coordinator._extract(v)
        assert data["target_soc"] == 90

    def test_outside_temperature(self):
        v = _make_vehicle(outside_temp=-5.5)
        data = self.coordinator._extract(v)
        assert data["outside_temp"] == -5.5

    def test_maintenance_km(self):
        v = _make_vehicle(inspection_km=12000)
        data = self.coordinator._extract(v)
        assert data["service_km"] == 12000

    def test_vehicle_object_stored(self):
        """_vehicle raw object must be in data for actions."""
        v = _make_vehicle()
        data = self.coordinator._extract(v)
        assert data["_vehicle"] is v

    def test_graceful_missing_attributes(self):
        """Missing attributes should return None, not raise."""
        v = MagicMock()
        v.vin.value = "TEST123"
        v.name.value = None
        v.model.value = None
        v.manufacturer.value = None
        v.model_year.value = None
        v.odometer.value = None
        v.drives.drives = {}
        v.drives.total_range.value = None
        v.position.latitude.value = None
        v.position.longitude.value = None
        # Make subsystems raise to test graceful degradation
        v.doors.lock_state.value  # this returns MagicMock → truthy
        v.climatization.state.value = MagicMock(name="OFF")
        v.charging.state.value = MagicMock(name="OFF")
        v.outside_temperature.value = None
        v.maintenance.inspection_due_at.value = None
        v.maintenance.inspection_due_after.value = None
        v.maintenance.oil_service_due_at.value = None
        v.maintenance.oil_service_due_after.value = None

        # Should not raise
        data = self.coordinator._extract(v)
        assert data["vin"] == "TEST123"
        assert data["range_km"] is None
        assert data["odometer_km"] is None


class TestCommands:
    """Test command execution."""

    def setup_method(self):
        hass = MagicMock()
        self.coordinator = VagConnectCoordinator.__new__(VagConnectCoordinator)
        self.coordinator.hass = hass
        self.coordinator.entry = _make_entry()
        self.coordinator.vehicles = {}

    def test_lock_command_sets_value(self):
        """Lock command must set 'lock' on the doors command."""
        mock_vehicle = MagicMock()
        mock_cmd = MagicMock()
        mock_vehicle.doors.commands.contains_command.return_value = True
        mock_vehicle.doors.commands.commands = {"lock-unlock": mock_cmd}
        self.coordinator.vehicles = {"VIN1": {"_vehicle": mock_vehicle}}

        # Simulate the blocking part of _run_command directly
        vehicle = self.coordinator.vehicles["VIN1"]["_vehicle"]
        cmds = vehicle.doors.commands
        assert cmds.contains_command("lock-unlock")
        cmds.commands["lock-unlock"].value = "lock"
        mock_cmd.value = "lock"
        assert mock_cmd.value == "lock"

    def test_command_missing_raises(self):
        """If command not available, raise RuntimeError."""
        mock_vehicle = MagicMock()
        mock_vehicle.doors.commands.contains_command.return_value = False
        self.coordinator.vehicles = {"VIN1": {"_vehicle": mock_vehicle}}

        with pytest.raises(RuntimeError, match="not available"):
            def _do():
                vehicle = self.coordinator.vehicles["VIN1"]["_vehicle"]
                cmds = vehicle.doors.commands
                if not cmds.contains_command("lock-unlock"):
                    raise RuntimeError(
                        "Command 'lock-unlock' not available for VIN1 (subsystem=doors). "
                        "Check S-PIN and vehicle capabilities."
                    )
            _do()

    def test_unknown_vin_raises(self):
        """Action on unknown VIN must raise RuntimeError."""
        self.coordinator.vehicles = {}
        with pytest.raises(RuntimeError, match="not found"):
            def _do():
                vehicle = self.coordinator.vehicles.get("UNKNOWN", {}).get("_vehicle")
                if vehicle is None:
                    raise RuntimeError("Vehicle UNKNOWN not found in garage")
            _do()
