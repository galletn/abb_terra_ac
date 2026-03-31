"""Sensor platform for ABB Terra AC."""
from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import ABBTerraACCoordinator
from .const import DOMAIN, CHARGING_STATES


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up ABB Terra AC sensors."""
    coordinator: ABBTerraACCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        # Current sensors
        ABBTerraACSensor(
            coordinator,
            "charging_current_l1",
            "Charging Current L1",
            UnitOfElectricCurrent.AMPERE,
            SensorDeviceClass.CURRENT,
            SensorStateClass.MEASUREMENT,
        ),
        ABBTerraACSensor(
            coordinator,
            "charging_current_l2",
            "Charging Current L2",
            UnitOfElectricCurrent.AMPERE,
            SensorDeviceClass.CURRENT,
            SensorStateClass.MEASUREMENT,
        ),
        ABBTerraACSensor(
            coordinator,
            "charging_current_l3",
            "Charging Current L3",
            UnitOfElectricCurrent.AMPERE,
            SensorDeviceClass.CURRENT,
            SensorStateClass.MEASUREMENT,
        ),
        ABBTerraACSensor(
            coordinator,
            "total_current",
            "Total Charging Current",
            UnitOfElectricCurrent.AMPERE,
            SensorDeviceClass.CURRENT,
            SensorStateClass.MEASUREMENT,
        ),
        ABBTerraACSensor(
            coordinator,
            "charging_current_limit",
            "Current Limit",
            UnitOfElectricCurrent.AMPERE,
            SensorDeviceClass.CURRENT,
            SensorStateClass.MEASUREMENT,
        ),
        ABBTerraACSensor(
            coordinator,
            "max_current",
            "Max Current",
            UnitOfElectricCurrent.AMPERE,
            SensorDeviceClass.CURRENT,
            SensorStateClass.MEASUREMENT,
        ),
        # Voltage sensors
        ABBTerraACSensor(
            coordinator,
            "voltage_l1",
            "Voltage L1",
            UnitOfElectricPotential.VOLT,
            SensorDeviceClass.VOLTAGE,
            SensorStateClass.MEASUREMENT,
        ),
        ABBTerraACSensor(
            coordinator,
            "voltage_l2",
            "Voltage L2",
            UnitOfElectricPotential.VOLT,
            SensorDeviceClass.VOLTAGE,
            SensorStateClass.MEASUREMENT,
        ),
        ABBTerraACSensor(
            coordinator,
            "voltage_l3",
            "Voltage L3",
            UnitOfElectricPotential.VOLT,
            SensorDeviceClass.VOLTAGE,
            SensorStateClass.MEASUREMENT,
        ),
        # Power and energy sensors
        ABBTerraACSensor(
            coordinator,
            "active_power",
            "Active Power",
            UnitOfPower.WATT,
            SensorDeviceClass.POWER,
            SensorStateClass.MEASUREMENT,
        ),
        ABBTerraACSensor(
            coordinator,
            "energy_delivered",
            "Energy Delivered",
            UnitOfEnergy.WATT_HOUR,
            SensorDeviceClass.ENERGY,
            SensorStateClass.TOTAL_INCREASING,
        ),
        # Status sensors
        ABBTerraACChargingStateSensor(coordinator),
        ABBTerraACSensor(
            coordinator,
            "error_code",
            "Error Code",
            None,
            None,
            None,
        ),
        ABBTerraACSensor(
            coordinator,
            "socket_lock_state",
            "Socket Lock State",
            None,
            None,
            None,
        ),
        ABBTerraACSensor(
            coordinator,
            "communication_timeout",
            "Communication Timeout",
            UnitOfTime.SECONDS,
            SensorDeviceClass.DURATION,
            None,
        ),
        # Info sensors
        ABBTerraACSensor(
            coordinator,
            "serial_number",
            "Serial Number",
            None,
            None,
            None,
        ),
        ABBTerraACSensor(
            coordinator,
            "firmware_version",
            "Firmware Version",
            None,
            None,
            None,
        ),
    ]

    async_add_entities(entities)


class ABBTerraACSensor(CoordinatorEntity, SensorEntity):
    """ABB Terra AC sensor."""

    def __init__(
        self,
        coordinator: ABBTerraACCoordinator,
        key: str,
        name: str,
        unit: str | None,
        device_class: SensorDeviceClass | None,
        state_class: SensorStateClass | None,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._key = key
        self._attr_name = f"ABB Terra AC {name}"
        self._attr_unique_id = f"{coordinator.host}_{key}"
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_state_class = state_class

        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.host)},
            "name": f"ABB Terra AC ({coordinator.host})",
            "manufacturer": "ABB",
            "model": "Terra AC W11",
            "sw_version": coordinator.data.get("firmware_version") if coordinator.data else None,
        }

    @property
    def native_value(self) -> float | str | None:
        """Return the state of the sensor."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get(self._key)


class ABBTerraACChargingStateSensor(ABBTerraACSensor):
    """Charging state sensor with text representation."""

    def __init__(self, coordinator: ABBTerraACCoordinator) -> None:
        """Initialize the charging state sensor."""
        super().__init__(
            coordinator,
            "charging_state",
            "Charging State",
            None,
            None,
            None,
        )

    @property
    def native_value(self) -> str | None:
        """Return the charging state as text."""
        if self.coordinator.data is None:
            return None

        state_code = self.coordinator.data.get("charging_state")
        if state_code is None:
            return None

        return CHARGING_STATES.get(state_code, f"Unknown ({state_code})")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra attributes."""
        if self.coordinator.data is None:
            return {}

        state_code = self.coordinator.data.get("charging_state")
        return {
            "state_code": state_code,
            "is_charging": state_code == 4,
        }
