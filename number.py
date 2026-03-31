"""Number platform for ABB Terra AC."""
from __future__ import annotations

import logging

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfElectricCurrent
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
    """Set up ABB Terra AC number entities."""
    coordinator: ABBTerraACCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities([ABBTerraACCurrentLimitNumber(coordinator)])


class ABBTerraACCurrentLimitNumber(CoordinatorEntity, NumberEntity):
    """Number entity for current limit control."""

    _attr_native_min_value = 0
    _attr_native_max_value = 16
    _attr_native_step = 1
    _attr_native_unit_of_measurement = UnitOfElectricCurrent.AMPERE
    _attr_mode = NumberMode.SLIDER

    def __init__(self, coordinator: ABBTerraACCoordinator) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator)
        self._attr_name = "ABB Terra AC Current Limit"
        self._attr_unique_id = f"{coordinator.host}_current_limit_control"

        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.host)},
            "name": f"ABB Terra AC ({coordinator.host})",
            "manufacturer": "ABB",
            "model": "Terra AC W11",
        }

    @property
    def native_value(self) -> float | None:
        """Return the current limit."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get("charging_current_limit", 0)

    async def async_set_native_value(self, value: float) -> None:
        """Set the current limit."""
        _LOGGER.info("Setting current limit to %sA", value)

        success = await self.coordinator.async_set_current_limit(value)

        if not success:
            _LOGGER.error("Failed to set current limit to %sA", value)
        else:
            _LOGGER.info("Successfully set current limit to %sA", value)
