"""Switch platform for ABB Terra AC."""
from __future__ import annotations

import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import ABBTerraACCoordinator
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

DEFAULT_CHARGING_CURRENT = 6  # Default charging current in amps


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up ABB Terra AC switch entities."""
    coordinator: ABBTerraACCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities([ABBTerraACStartPauseSwitch(coordinator)])


class ABBTerraACStartPauseSwitch(CoordinatorEntity, SwitchEntity):
    """Start/Pause switch for ABB Terra AC."""

    def __init__(self, coordinator: ABBTerraACCoordinator) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._attr_name = "ABB Terra AC Charging"
        self._attr_unique_id = f"{coordinator.host}_start_pause"

        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.host)},
            "name": f"ABB Terra AC ({coordinator.host})",
            "manufacturer": "ABB",
            "model": "Terra AC W11",
        }

    @property
    def is_on(self) -> bool | None:
        """Return true if charging (current limit > 0)."""
        if self.coordinator.data is None:
            return None

        current_limit = self.coordinator.data.get("charging_current_limit", 0)
        return current_limit > 0

    @property
    def icon(self) -> str:
        """Return the icon."""
        if self.is_on:
            return "mdi:ev-station"
        return "mdi:pause-circle-outline"

    async def async_turn_on(self, **kwargs) -> None:
        """Start charging via start command, then set default current."""
        _LOGGER.info("Starting charging at %sA", DEFAULT_CHARGING_CURRENT)

        success = await self.coordinator.async_start_charging()
        if success:
            await self.coordinator.async_set_current_limit(DEFAULT_CHARGING_CURRENT)
            _LOGGER.info("Successfully started charging")
        else:
            _LOGGER.error("Failed to start charging")

    async def async_turn_off(self, **kwargs) -> None:
        """Stop charging via stop command and set current to 0A."""
        _LOGGER.info("Stopping charging")

        success = await self.coordinator.async_stop_charging()
        if success:
            await self.coordinator.async_set_current_limit(0)
            _LOGGER.info("Successfully stopped charging")
        else:
            _LOGGER.error("Failed to stop charging")
