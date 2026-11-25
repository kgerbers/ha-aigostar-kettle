"""Operating-mode selector for the AigoSmart kettle."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .alibaba_api import AlibabaIoTClient
from .const import DOMAIN, KETTLE_MODE, SCAN_INTERVAL_SECONDS

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(seconds=SCAN_INTERVAL_SECONDS)
MODE_OPTIONS = (
    "Met een klik koken",
    "Koken en warm houden",
    "Verwarmen en warm houden",
)
MODE_TO_VALUE = {label: index for index, label in enumerate(MODE_OPTIONS)}
VALUE_TO_MODE = {value: label for label, value in MODE_TO_VALUE.items()}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    entities: list[AigoSmartModeSelect] = []
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
        entities.append(AigoSmartModeSelect(client, iot_id, info))
    hass.data.setdefault(f"{DOMAIN}_entities", {}).setdefault(entry.entry_id, []).extend(entities)
    async_add_entities(entities, update_before_add=True)


class AigoSmartModeSelect(SelectEntity):
    """AigoSmart kettle operating-mode selector."""

    _attr_has_entity_name = True
    _attr_name = "Operating mode"
    _attr_options = list(MODE_OPTIONS)

    def __init__(self, client: AlibabaIoTClient, iot_id: str, info: DeviceInfo) -> None:
        self._client = client
        self._attr_unique_id = f"{iot_id}_mode"
        self._attr_device_info = info
        self._attr_current_option: str | None = None

    def update_token(self, new_token: str) -> None:
        self._client.iot_token = new_token

    def update(self) -> None:
        try:
            props = self._client.get_properties_sync()
            value = int(props[KETTLE_MODE])
            self._attr_current_option = VALUE_TO_MODE.get(value)
            self._attr_available = self._attr_current_option is not None
        except Exception as exc:
            _LOGGER.warning("AigoSmart mode update failed [%s]: %s", self._client.iot_id, exc)
            self._attr_available = False

    def select_option(self, option: str) -> None:
        if option not in MODE_TO_VALUE:
            raise ValueError(f"Unsupported AigoSmart mode: {option}")
        self._client.set_properties_sync({KETTLE_MODE: MODE_TO_VALUE[option]})
        self._attr_current_option = option
