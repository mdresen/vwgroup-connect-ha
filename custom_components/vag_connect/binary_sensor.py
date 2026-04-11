"""Binary sensors for VAG Connect — correct data keys from coordinator."""
from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import VagConnectCoordinator
from .entity_base import VagConnectEntity


@dataclass(frozen=True)
class VagBinarySensorDescription(BinarySensorEntityDescription):
    data_key: str = ""
    condition: str | None = None


BINARY_DESCRIPTIONS: tuple[VagBinarySensorDescription, ...] = (
    VagBinarySensorDescription(
        key="doors_locked",
        data_key="doors_locked",
        name="Türen verriegelt",
        device_class=BinarySensorDeviceClass.LOCK,
        icon="mdi:car-door-lock",
    ),
    VagBinarySensorDescription(
        key="doors_open",
        data_key="doors_open",
        name="Türen offen",
        device_class=BinarySensorDeviceClass.DOOR,
        icon="mdi:car-door",
    ),
    VagBinarySensorDescription(
        key="windows_open",
        data_key="windows_open",
        name="Fenster offen",
        device_class=BinarySensorDeviceClass.WINDOW,
        icon="mdi:car-windshield-outline",
    ),
    VagBinarySensorDescription(
        key="plug_connected",
        data_key="plug_connected",
        name="Ladekabel verbunden",
        device_class=BinarySensorDeviceClass.PLUG,
        icon="mdi:power-plug",
        condition="electric",
    ),
    VagBinarySensorDescription(
        key="is_charging",
        data_key="is_charging",
        name="Lädt",
        device_class=BinarySensorDeviceClass.BATTERY_CHARGING,
        icon="mdi:battery-charging",
        condition="electric",
    ),
    VagBinarySensorDescription(
        key="climatisation_active",
        data_key="climatisation_active",
        name="Klimatisierung aktiv",
        device_class=BinarySensorDeviceClass.RUNNING,
        icon="mdi:thermometer",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: VagConnectCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[VagConnectBinarySensor] = []

    for vin, vehicle in coordinator.vehicles.items():
        is_electric = vehicle.get("is_electric", False)
        for desc in BINARY_DESCRIPTIONS:
            if desc.condition == "electric" and not is_electric:
                continue
            entities.append(VagConnectBinarySensor(coordinator, vin, desc))

    async_add_entities(entities)


class VagConnectBinarySensor(VagConnectEntity, BinarySensorEntity):
    entity_description: VagBinarySensorDescription

    def __init__(self, coordinator, vin, description):
        super().__init__(coordinator, vin, description.key)
        self.entity_description = description

    @property
    def is_on(self) -> bool | None:
        val = self._vehicle.get(self.entity_description.data_key)
        if val is None:
            return None
        return bool(val)
