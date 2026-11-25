"""Diagnostic and state sensors for AigoSmart devices.

The AigoSmart product models expose different TSL property names.  This
initial platform deliberately publishes the complete property map as sensor
attributes so a new appliance can be mapped without guessing a command that
could start heating.  Once the kettle TSL is known, safe command entities can
be added using the same AlibabaIoTClient.
"""
from __future__ import annotations

import json
import logging
from datetime import timedelta
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .alibaba_api import AlibabaIoTClient
from .const import (
    DOMAIN,
    KETTLE_TEMPERATURE_KEYS,
    SCAN_INTERVAL_SECONDS,
)

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(seconds=SCAN_INTERVAL_SECONDS)


def _first_value(props: dict[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        if key in props:
            return props[key]
    return None


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    entities: list[SensorEntity] = []
    for device in data["devices"]:
        iot_id = device.get("iotId")
        if not iot_id:
            continue
        name = device.get("nickName") or device.get("deviceName") or iot_id[:12]
        client = AlibabaIoTClient(
            iot_id=iot_id,
            iot_token=data["iot_token"],
            app_key=data["app_key"],
            app_secret=data["app_secret"],
        )
        device_info = _device_info(iot_id, name, device)
        entities.extend(
            (
                AigoSmartDeviceSensor(client, iot_id, name, device, device_info),
                AigoSmartTemperatureSensor(client, iot_id, device_info),
            )
        )

    hass.data.setdefault(f"{DOMAIN}_entities", {}).setdefault(entry.entry_id, []).extend(entities)
    async_add_entities(entities, update_before_add=True)


def _device_info(iot_id: str, name: str, raw_device: dict[str, Any]) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, iot_id)},
        name=name,
        manufacturer="Aigostar",
        model=raw_device.get("productName") or raw_device.get("categoryName") or "AigoSmart device",
        sw_version=raw_device.get("firmwareVersion") or raw_device.get("moduleVersion"),
    )


class AigoSmartDeviceSensor(SensorEntity):
    """Expose safe device status and raw TSL properties for mapping."""

    _attr_has_entity_name = True
    _attr_name = "Device status"
    _attr_icon = "mdi:devices"

    def __init__(
        self,
        client: AlibabaIoTClient,
        iot_id: str,
        name: str,
        raw_device: dict[str, Any],
        device_info: DeviceInfo,
    ) -> None:
        self._client = client
        self._attr_unique_id = f"{iot_id}_status"
        self._attr_device_info = device_info
        self._attr_native_value = "unknown"
        self._attr_extra_state_attributes: dict[str, Any] = {
            "iot_id": iot_id,
            "device_name": raw_device.get("deviceName"),
            "product_key": raw_device.get("productKey"),
            "raw_device": json.dumps(raw_device, sort_keys=True, default=str),
        }
        self._props: dict[str, Any] = {}

    def update_token(self, new_token: str) -> None:
        self._client.iot_token = new_token

    @property
    def native_value(self) -> str:
        return str(self._attr_native_value)

    def update(self) -> None:
        try:
            props = self._client.get_properties_sync()
            self._props = props
            temperature = _first_value(props, KETTLE_TEMPERATURE_KEYS)
            self._attr_native_value = "online"
            attrs = dict(self._attr_extra_state_attributes or {})
            attrs["properties"] = props
            attrs["property_keys"] = sorted(props)
            if temperature is not None:
                attrs["current_temperature_candidate"] = temperature
            self._attr_extra_state_attributes = attrs
            self._attr_available = True
        except Exception as exc:
            _LOGGER.warning("AigoSmart [%s] update failed: %s", self._client.iot_id, exc)
            self._attr_native_value = "unavailable"
            self._attr_available = False


class AigoSmartTemperatureSensor(SensorEntity):
    """Current water temperature reported by the kettle."""

    _attr_has_entity_name = True
    _attr_name = "Water temperature"
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(self, client: AlibabaIoTClient, iot_id: str, device_info: DeviceInfo) -> None:
        self._client = client
        self._attr_unique_id = f"{iot_id}_temperature"
        self._attr_device_info = device_info
        self._attr_native_value: float | None = None

    def update_token(self, new_token: str) -> None:
        self._client.iot_token = new_token

    def update(self) -> None:
        try:
            props = self._client.get_properties_sync()
            value = props.get("temperature")
            self._attr_native_value = float(value) if value is not None else None
            self._attr_available = value is not None
        except Exception as exc:
            _LOGGER.warning("AigoSmart temperature update failed [%s]: %s", self._client.iot_id, exc)
            self._attr_available = False

