"""Persistent switch controls for an AigoSmart kettle."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .alibaba_api import AlibabaIoTClient
from .const import (
    DOMAIN,
    KETTLE_KEEP_WARM_SWITCH,
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
    entities: list[AigoSmartKettleSwitch] = []
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
        entities.append(AigoSmartKettleSwitch(client, iot_id, info))
    hass.data.setdefault(f"{DOMAIN}_entities", {}).setdefault(entry.entry_id, []).extend(entities)
    async_add_entities(entities, update_before_add=True)


class AigoSmartKettleSwitch(SwitchEntity):
    """Persistent keep-warm switch backed by a boolean TSL property."""

    _attr_has_entity_name = True

    def __init__(self, client: AlibabaIoTClient, iot_id: str, info: DeviceInfo) -> None:
        self._client = client
        self._key = KETTLE_KEEP_WARM_SWITCH
        self._attr_name = "Keep warm"
        # Keep the original unique ID so existing installations migrate
        # without creating a second Keep Warm entity.
        self._attr_unique_id = f"{iot_id}_{KETTLE_KEEP_WARM_SWITCH.lower()}"
        self._attr_device_info = info
        self._attr_is_on = False

    def update_token(self, new_token: str) -> None:
        self._client.iot_token = new_token

    def update(self) -> None:
        try:
            props = self._client.get_properties_sync()
            value = props.get(self._key)
            self._attr_is_on = bool(value)
            self._attr_available = value is not None
        except Exception as exc:
            _LOGGER.warning("AigoSmart switch update failed [%s/%s]: %s", self._client.iot_id, self._key, exc)
            self._attr_available = False

    def turn_on(self, **kwargs: object) -> None:
        self._client.set_properties_sync({self._key: 1})
        self._attr_is_on = True

    def turn_off(self, **kwargs: object) -> None:
        self._client.set_properties_sync({self._key: 0})
        self._attr_is_on = False
