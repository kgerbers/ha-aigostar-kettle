"""Momentary command buttons for AigoSmart kettle heating."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .alibaba_api import AlibabaIoTClient
from .const import DOMAIN, KETTLE_HEATING_SWITCH


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    entities: list[AigoSmartHeatingButton] = []
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
        for command, label in ((1, "Start heating"), (0, "Stop heating")):
            client = AlibabaIoTClient(iot_id, data["iot_token"], data["app_key"], data["app_secret"])
            entities.append(AigoSmartHeatingButton(client, iot_id, info, command, label))
    hass.data.setdefault(f"{DOMAIN}_entities", {}).setdefault(entry.entry_id, []).extend(entities)
    async_add_entities(entities)


class AigoSmartHeatingButton(ButtonEntity):
    """Send a one-shot heating command; the device bit is not persistent."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:kettle-steam"

    def __init__(self, client: AlibabaIoTClient, iot_id: str, info: DeviceInfo, command: int, label: str) -> None:
        self._client = client
        self._command = command
        self._attr_name = label
        self._attr_unique_id = f"{iot_id}_heating_{'start' if command else 'stop'}"
        self._attr_device_info = info

    def update_token(self, new_token: str) -> None:
        self._client.iot_token = new_token

    def press(self) -> None:
        self._client.set_properties_sync({KETTLE_HEATING_SWITCH: self._command})
