"""Number entities for AigoSmart kettle settings."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .alibaba_api import AlibabaIoTClient
from .const import (
    DOMAIN,
    KETTLE_KEEP_WARM_TIME,
    KETTLE_MODE,
    KETTLE_TARGET_TEMPERATURE,
    SCAN_INTERVAL_SECONDS,
)

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(seconds=SCAN_INTERVAL_SECONDS)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    entities: list[NumberEntity] = []
    for device in data["devices"]:
        iot_id = device.get("iotId")
        if not iot_id or device.get("categoryKey") != "ElectricKettle":
            continue
        name = device.get("nickName") or device.get("deviceName") or iot_id[:12]
        info = DeviceInfo(
            identifiers={(DOMAIN, iot_id)},
            name=name,
            manufacturer="Aigostar",
            model=device.get("productName") or "Electric kettle",
        )
        client = AlibabaIoTClient(iot_id, data["iot_token"], data["app_key"], data["app_secret"])
        entities.extend(
            (
                AigoSmartTargetTemperature(client, iot_id, info),
                AigoSmartKeepWarmDuration(client, iot_id, info),
            )
        )
    hass.data.setdefault(f"{DOMAIN}_entities", {}).setdefault(entry.entry_id, []).extend(entities)
    async_add_entities(entities, update_before_add=True)


class AigoSmartTargetTemperature(NumberEntity):
    """Kettle target temperature; changing it does not start heating."""

    _attr_has_entity_name = True
    _attr_name = "Target temperature"
    _attr_native_min_value = 40
    _attr_native_max_value = 100
    _attr_native_step = 5
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_mode = NumberMode.SLIDER

    def __init__(self, client: AlibabaIoTClient, iot_id: str, device_info: DeviceInfo) -> None:
        self._client = client
        self._attr_unique_id = f"{iot_id}_target_temperature"
        self._attr_device_info = device_info
        self._attr_native_value: float | None = None

    def update_token(self, new_token: str) -> None:
        self._client.iot_token = new_token

    def update(self) -> None:
        try:
            props = self._client.get_properties_sync()
            value = props.get(KETTLE_TARGET_TEMPERATURE)
            self._attr_native_value = float(value) if value is not None else None
            self._attr_available = value is not None
        except Exception as exc:
            _LOGGER.warning("AigoSmart target temperature update failed [%s]: %s", self._client.iot_id, exc)
            self._attr_available = False

    def set_native_value(self, value: float) -> None:
        self._client.set_properties_sync({KETTLE_TARGET_TEMPERATURE: int(value)})
        self._attr_native_value = value


class AigoSmartKeepWarmDuration(NumberEntity):
    """Keep-warm duration in hours; the API stores minutes in ``Time``."""

    _attr_has_entity_name = True
    _attr_name = "Keep warm duration"
    _attr_native_min_value = 1
    _attr_native_max_value = 13
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "h"
    _attr_mode = NumberMode.SLIDER

    def __init__(self, client: AlibabaIoTClient, iot_id: str, device_info: DeviceInfo) -> None:
        self._client = client
        self._attr_unique_id = f"{iot_id}_keep_warm_duration"
        self._attr_device_info = device_info
        self._attr_native_value: float | None = None

    def update_token(self, new_token: str) -> None:
        self._client.iot_token = new_token

    def update(self) -> None:
        try:
            props = self._client.get_properties_sync()
            mode = int(props.get(KETTLE_MODE, 0))
            minutes = props.get(KETTLE_KEEP_WARM_TIME)
            self._attr_native_value = round(float(minutes) / 60, 2) if minutes is not None else None
            self._attr_available = mode in (1, 2) and minutes is not None
        except Exception as exc:
            _LOGGER.warning("AigoSmart keep-warm duration update failed [%s]: %s", self._client.iot_id, exc)
            self._attr_available = False

    def set_native_value(self, value: float) -> None:
        self._client.set_properties_sync({KETTLE_KEEP_WARM_TIME: int(round(value * 60))})
        self._attr_native_value = value
