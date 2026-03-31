"""Button platform for ABB Terra AC."""
from __future__ import annotations

import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import ABBTerraACCoordinator
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up ABB Terra AC button entities."""
    coordinator: ABBTerraACCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities([ABBTerraACStopButton(coordinator)])


class ABBTerraACStopButton(CoordinatorEntity, ButtonEntity):
    """Emergency stop button for ABB Terra AC."""

    def __init__(self, coordinator: ABBTerraACCoordinator) -> None:
        """Initialize the button."""
        super().__init__(coordinator)
        self._attr_name = "ABB Terra AC Stop Charging"
        self._attr_unique_id = f"{coordinator.host}_stop_button"
        self._attr_icon = "mdi:stop-circle"

        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.host)},
            "name": f"ABB Terra AC ({coordinator.host})",
            "manufacturer": "ABB",
            "model": "Terra AC W11",
        }

    async def async_press(self) -> None:
        """Handle the button press - send STOP command."""
        _LOGGER.info("STOP button pressed - sending stop command")

        success = await self.coordinator.async_stop_charging()

        if not success:
            _LOGGER.error("Failed to send STOP command")
        else:
            _LOGGER.info("Successfully sent STOP command")
