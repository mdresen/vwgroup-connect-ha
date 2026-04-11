"""DataUpdateCoordinator for VAG Connect — uses real CarConnectivity API."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_BRAND,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    CONF_SPIN,
    CONF_USERNAME,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class VagConnectCoordinator(DataUpdateCoordinator):
    """Fetches all vehicle data from CarConnectivity on every update cycle."""

    def __init__(self, hass: HomeAssistant, entry) -> None:
        self.entry = entry
        self._cc = None          # CarConnectivity instance
        self._started = False    # Whether startup() was called
        self.vehicles: dict[str, Any] = {}

        scan_interval = entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{entry.entry_id}",
            update_interval=timedelta(minutes=scan_interval),
        )

    # ------------------------------------------------------------------
    # Private: CarConnectivity lifecycle
    # ------------------------------------------------------------------

    def _init_carconnectivity(self):
        """Build and start CarConnectivity (blocking, run in executor)."""
        from carconnectivity.carconnectivity import CarConnectivity  # noqa: PLC0415

        brand    = self.entry.data[CONF_BRAND]
        username = self.entry.data[CONF_USERNAME]
        password = self.entry.data[CONF_PASSWORD]
        spin     = self.entry.data.get(CONF_SPIN) or None

        connector_cfg: dict[str, Any] = {
            "username": username,
            "password": password,
        }
        if spin:
            connector_cfg["spin"] = spin

        cc = CarConnectivity(config={
            "carConnectivity": {
                "connectors": [{"type": brand, "config": connector_cfg}]
            }
        })
        cc.startup()
        self._cc = cc
        self._started = True
        _LOGGER.debug("CarConnectivity started for brand=%s", brand)

    def _fetch_data(self) -> dict[str, Any]:
        """Fetch all vehicle data (blocking)."""
        if self._cc is None or not self._started:
            self._init_carconnectivity()

        self._cc.fetch_all()

        garage = self._cc.get_garage()
        if garage is None:
            return {}

        result: dict[str, Any] = {}
        for vin in garage.list_vehicle_vins():
            vehicle = garage.get_vehicle(vin)
            if vehicle is not None:
                result[vin] = self._extract(vehicle)

        return result

    def _extract(self, vehicle) -> dict[str, Any]:  # noqa: PLR0912, PLR0915
        """
        Extract all CarConnectivity vehicle attributes into a flat HA-friendly dict.
        Uses the real CarConnectivity object model.
        """
        from carconnectivity.drive import GenericDrive          # noqa: PLC0415
        from carconnectivity.doors import Doors                  # noqa: PLC0415
        from carconnectivity.windows import Windows              # noqa: PLC0415
        from carconnectivity.charging import Charging            # noqa: PLC0415
        from carconnectivity.climatization import Climatization  # noqa: PLC0415

        def _val(attr):
            """Safely read .value from a CarConnectivity attribute."""
            try:
                v = attr.value
                # Return enum name as string for HA state display
                if hasattr(v, 'name'):
                    return v.name
                return v
            except Exception:  # noqa: BLE001
                return None

        data: dict[str, Any] = {}

        # ── Identity ─────────────────────────────────────────────────
        data["vin"]          = _val(vehicle.vin)
        data["nickname"]     = _val(vehicle.name) or _val(vehicle.vin)
        data["model"]        = _val(vehicle.model) or "VAG Vehicle"
        data["manufacturer"] = _val(vehicle.manufacturer) or self.entry.data[CONF_BRAND].title()
        data["model_year"]   = _val(vehicle.model_year)

        # ── Odometer ─────────────────────────────────────────────────
        try:
            data["odometer_km"] = _val(vehicle.odometer)
        except Exception:  # noqa: BLE001
            data["odometer_km"] = None

        # ── Drives: fuel level, range, electric detection ────────────
        data["fuel_level"]  = None
        data["battery_soc"] = None
        data["range_km"]    = None
        data["is_electric"] = False

        try:
            drives = vehicle.drives.drives.values()
            electric_types = {
                GenericDrive.Type.ELECTRIC,
            }
            fuel_types = {
                GenericDrive.Type.FUEL, GenericDrive.Type.GASOLINE,
                GenericDrive.Type.PETROL, GenericDrive.Type.DIESEL,
                GenericDrive.Type.CNG, GenericDrive.Type.LPG,
            }
            total_range = _val(vehicle.drives.total_range)
            if total_range is not None:
                data["range_km"] = total_range

            for drive in drives:
                dtype = drive.type.value if drive.type.value else None
                level = _val(drive.level)
                rng   = _val(drive.range)

                if dtype in electric_types:
                    data["is_electric"] = True
                    data["battery_soc"] = level
                    if data["range_km"] is None:
                        data["range_km"] = rng
                elif dtype in fuel_types:
                    data["fuel_level"] = level
                    if data["range_km"] is None:
                        data["range_km"] = rng
                else:
                    # Unknown type — still grab level/range as fallback
                    if data["fuel_level"] is None:
                        data["fuel_level"] = level
                    if data["range_km"] is None:
                        data["range_km"] = rng
        except Exception as exc:  # noqa: BLE001
            _LOGGER.debug("Drive data error: %s", exc)

        # ── Position ─────────────────────────────────────────────────
        try:
            data["latitude"]  = _val(vehicle.position.latitude)
            data["longitude"] = _val(vehicle.position.longitude)
        except Exception:  # noqa: BLE001
            data["latitude"]  = None
            data["longitude"] = None

        # ── Doors ────────────────────────────────────────────────────
        try:
            lock = vehicle.doors.lock_state.value
            data["doors_locked"] = (lock == Doors.LockState.LOCKED) if lock else None
            open_s = vehicle.doors.open_state.value
            data["doors_open"] = (open_s == Doors.OpenState.OPEN) if open_s else None
        except Exception:  # noqa: BLE001
            data["doors_locked"] = None
            data["doors_open"]   = None

        # ── Windows ──────────────────────────────────────────────────
        try:
            win_state = vehicle.windows.open_state.value
            data["windows_open"] = (win_state == Windows.OpenState.OPEN) if win_state else None
        except Exception:  # noqa: BLE001
            data["windows_open"] = None

        # ── Climatisation ────────────────────────────────────────────
        try:
            clim_state = vehicle.climatization.state.value
            data["climatisation_state"] = clim_state.name if clim_state else None
            data["climatisation_active"] = clim_state not in (
                Climatization.ClimatizationState.OFF,
                Climatization.ClimatizationState.UNKNOWN,
                None,
            )
            data["target_temperature"] = _val(vehicle.climatization.settings.target_temperature)
        except Exception:  # noqa: BLE001
            data["climatisation_state"]  = None
            data["climatisation_active"] = False
            data["target_temperature"]   = None

        # ── Charging ─────────────────────────────────────────────────
        try:
            charge_state = vehicle.charging.state.value
            data["charging_state"]  = charge_state.name if charge_state else None
            data["is_charging"]     = charge_state in (
                Charging.ChargingState.CHARGING,
                Charging.ChargingState.CONSERVATION,
            )
            plug = vehicle.charging.connector.connection_state.value
            data["plug_connected"] = (plug is not None and plug.name not in ("DISCONNECTED", "UNKNOWN", "INVALID"))
            data["plug_state"]      = plug.name if plug else None
            data["target_soc"]      = _val(vehicle.charging.settings.target_level)
        except Exception:  # noqa: BLE001
            data["charging_state"] = None
            data["is_charging"]    = False
            data["plug_connected"] = None
            data["plug_state"]     = None
            data["target_soc"]     = None

        # ── Maintenance ───────────────────────────────────────────────
        try:
            data["service_due_at"]  = _val(vehicle.maintenance.inspection_due_at)
            data["service_km"]      = _val(vehicle.maintenance.inspection_due_after)
            data["oil_service_at"]  = _val(vehicle.maintenance.oil_service_due_at)
            data["oil_service_km"]  = _val(vehicle.maintenance.oil_service_due_after)
        except Exception:  # noqa: BLE001
            data["service_due_at"] = None
            data["service_km"]     = None
            data["oil_service_at"] = None
            data["oil_service_km"] = None

        # ── Outside Temperature ───────────────────────────────────────
        try:
            data["outside_temp"] = _val(vehicle.outside_temperature)
        except Exception:  # noqa: BLE001
            data["outside_temp"] = None

        # Keep raw object for actions (not serialised, not logged)
        data["_vehicle"] = vehicle
        return data

    # ------------------------------------------------------------------
    # HA coordinator interface
    # ------------------------------------------------------------------

    async def _async_update_data(self) -> dict[str, Any]:
        """Called by HA on every poll cycle."""
        try:
            vehicles = await self.hass.async_add_executor_job(self._fetch_data)
            self.vehicles = vehicles
            _LOGGER.debug("VAG Connect: %d vehicle(s) updated", len(vehicles))
            return vehicles
        except Exception as err:  # noqa: BLE001
            # Reset so next poll retries auth from scratch
            self._shutdown()
            raise UpdateFailed(f"VAG Connect update failed: {err}") from err

    def _shutdown(self):
        """Shut down CarConnectivity gracefully."""
        try:
            if self._cc and self._started:
                self._cc.shutdown()
        except Exception:  # noqa: BLE001
            pass
        self._cc = None
        self._started = False

    # ------------------------------------------------------------------
    # Vehicle actions
    # ------------------------------------------------------------------

    async def async_lock(self, vin: str) -> None:
        await self._run_command(vin, "doors", "lock-unlock", "lock")

    async def async_unlock(self, vin: str) -> None:
        await self._run_command(vin, "doors", "lock-unlock", "unlock")

    async def async_start_climatisation(self, vin: str) -> None:
        await self._run_command(vin, "climatization", "start-stop", "start")

    async def async_stop_climatisation(self, vin: str) -> None:
        await self._run_command(vin, "climatization", "start-stop", "stop")

    async def async_start_charging(self, vin: str) -> None:
        await self._run_command(vin, "charging", "start-stop", "start")

    async def async_stop_charging(self, vin: str) -> None:
        await self._run_command(vin, "charging", "start-stop", "stop")

    async def async_flash_lights(self, vin: str) -> None:
        await self._run_command(vin, "lights", "honk-and-flash", "flash")

    async def async_set_target_soc(self, vin: str, target: int) -> None:
        """Set target state of charge (0–100%)."""
        def _do():
            vehicle = self.vehicles.get(vin, {}).get("_vehicle")
            if vehicle is None:
                raise RuntimeError(f"Vehicle {vin} not found")
            vehicle.charging.settings.target_level.value = target
        await self.hass.async_add_executor_job(_do)
        await self.async_request_refresh()

    async def async_set_climatisation_temperature(self, vin: str, temp_c: float) -> None:
        """Set target climatisation temperature in Celsius."""
        def _do():
            vehicle = self.vehicles.get(vin, {}).get("_vehicle")
            if vehicle is None:
                raise RuntimeError(f"Vehicle {vin} not found")
            vehicle.climatization.settings.target_temperature.value = temp_c
        await self.hass.async_add_executor_job(_do)
        await self.async_request_refresh()

    async def _run_command(
        self, vin: str, subsystem: str, command_name: str, value: str
    ) -> None:
        """Generic command executor using CarConnectivity command objects."""
        def _do():
            vehicle = self.vehicles.get(vin, {}).get("_vehicle")
            if vehicle is None:
                raise RuntimeError(f"Vehicle {vin} not found in garage")

            # Navigate to the right commands container
            subsystem_map = {
                "doors":         vehicle.doors,
                "charging":      vehicle.charging,
                "climatization": vehicle.climatization,
                "lights":        vehicle.lights,
            }
            sub = subsystem_map.get(subsystem)
            if sub is None:
                raise RuntimeError(f"Unknown subsystem: {subsystem}")

            cmds = sub.commands
            if not cmds.contains_command(command_name):
                raise RuntimeError(
                    f"Command '{command_name}' not available for {vin} "
                    f"(subsystem={subsystem}). Check S-PIN and vehicle capabilities."
                )
            cmds.commands[command_name].value = value
            _LOGGER.info("VAG %s %s → %s: %s", vin, subsystem, command_name, value)

        await self.hass.async_add_executor_job(_do)
        await self.async_request_refresh()
