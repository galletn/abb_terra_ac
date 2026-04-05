"""ABB Terra AC Wallbox integration for Home Assistant."""
from __future__ import annotations

import logging
from datetime import timedelta

from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ModbusException

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, CONF_UNIT_ID, DEFAULT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR, Platform.NUMBER, Platform.SWITCH, Platform.BUTTON]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up ABB Terra AC from a config entry."""
    coordinator = ABBTerraACCoordinator(
        hass,
        entry.data[CONF_HOST],
        entry.data.get(CONF_PORT, 502),
        entry.data.get(CONF_UNIT_ID, 1),
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register services
    async def handle_set_current_limit(call):
        """Handle set_current_limit service."""
        current = call.data.get("current")
        await coordinator.async_set_current_limit(current)

    async def handle_start_charging(call):
        """Handle start_charging service."""
        current = call.data.get("current", 6)
        await coordinator.async_start_charging()
        await coordinator.async_set_current_limit(current)

    async def handle_stop_charging(call):
        """Handle stop_charging service."""
        await coordinator.async_stop_charging()

    hass.services.async_register(DOMAIN, "set_current_limit", handle_set_current_limit)
    hass.services.async_register(DOMAIN, "start_charging", handle_start_charging)
    hass.services.async_register(DOMAIN, "stop_charging", handle_stop_charging)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


class ABBTerraACCoordinator(DataUpdateCoordinator):
    """Coordinator to manage fetching ABB Terra AC data."""

    def __init__(
        self,
        hass: HomeAssistant,
        host: str,
        port: int,
        unit_id: int,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.host = host
        self.port = port
        self.unit_id = unit_id
        self._client = None

    def _get_client(self) -> ModbusTcpClient:
        """Get or create Modbus client."""
        if self._client is None:
            self._client = ModbusTcpClient(
                host=self.host,
                port=self.port,
                timeout=3,
            )
        return self._client

    async def _async_update_data(self) -> dict:
        """Fetch data from the wallbox."""
        return await self.hass.async_add_executor_job(self._update_data)

    def _update_data(self) -> dict:
        """Fetch data from the wallbox (sync)."""
        client = self._get_client()

        try:
            # Always try to connect (reconnect if needed)
            if not client.is_socket_open():
                if not client.connect():
                    raise UpdateFailed("Failed to connect to wallbox")

            # Read all registers from 0x4000 (16384) to 0x4020 (16416)
            result = client.read_holding_registers(
                address=16384, count=33, device_id=self.unit_id
            )

            if result.isError():
                # Try reconnecting once
                client.close()
                if not client.connect():
                    raise UpdateFailed("Failed to reconnect to wallbox")

                result = client.read_holding_registers(
                    address=16384, count=33, device_id=self.unit_id
                )

                if result.isError():
                    raise UpdateFailed(f"Modbus read error: {result}")

            registers = result.registers

            # Parse register data
            # Note: 32-bit values are stored as [high_word, low_word]
            # For ABB, the actual value is in the LOW word (odd index)
            data = {
                "serial_number": f"{registers[0]:04X}{registers[1]:04X}{registers[2]:04X}{registers[3]:04X}",
                "firmware_version": f"{registers[4]}.{registers[5]}",
                "max_current": registers[7] * 0.001,  # mA to A (32-bit, use low word)
                "error_code": registers[8],
                "socket_lock_state": registers[11],  # Use low word
                "charging_state": (registers[13] >> 8) & 0xFF,  # High byte of low word
                "charging_current_limit": registers[15] * 0.001,  # mA to A (32-bit, use low word)
                "charging_current_l1": registers[17] * 0.001,  # mA to A (32-bit, use low word)
                "charging_current_l2": registers[19] * 0.001,  # mA to A (32-bit, use low word)
                "charging_current_l3": registers[21] * 0.001,  # mA to A (32-bit, use low word)
                "voltage_l1": registers[23] * 0.1,  # 0.1V to V (32-bit, use low word)
                "voltage_l2": registers[25] * 0.1,  # 0.1V to V (32-bit, use low word)
                "voltage_l3": registers[27] * 0.1,  # 0.1V to V (32-bit, use low word)
                "active_power": registers[29],  # W (32-bit, use low word)
                "energy_delivered": registers[31],  # Wh (32-bit, use low word)
                "communication_timeout": registers[32],  # seconds (16-bit)
            }

            # Calculate total current and power
            data["total_current"] = (
                data["charging_current_l1"]
                + data["charging_current_l2"]
                + data["charging_current_l3"]
            )

            return data

        except ModbusException as err:
            raise UpdateFailed(f"Modbus error: {err}") from err
        except Exception as err:
            raise UpdateFailed(f"Unexpected error: {err}") from err

    async def async_write_register(self, address: int, values: list[int]) -> bool:
        """Write to a register."""
        return await self.hass.async_add_executor_job(
            self._write_register, address, values
        )

    def _write_register(self, address: int, values: list[int]) -> bool:
        """Write to a register (sync)."""
        client = self._get_client()

        try:
            # Ensure connection is open
            if not client.is_socket_open():
                if not client.connect():
                    _LOGGER.error("Failed to connect to wallbox for write")
                    return False

            if len(values) == 1:
                result = client.write_register(
                    address=address, value=values[0], device_id=self.unit_id
                )
            else:
                result = client.write_registers(
                    address=address, values=values, device_id=self.unit_id
                )

            if result.isError():
                _LOGGER.error("Modbus write error: %s", result)
                return False

            return True

        except Exception as err:
            _LOGGER.error("Error writing register: %s", err)
            return False

    async def async_set_current_limit(self, amps: float) -> bool:
        """Set charging current limit."""
        milliamps = int(amps * 1000)
        low_word = milliamps & 0xFFFF
        high_word = (milliamps >> 16) & 0xFFFF

        success = await self.async_write_register(16640, [high_word, low_word])

        if success:
            # Optimistic update — set the value in coordinator data immediately
            # so HA entity reflects the target, not the stale register value.
            # The charger takes time to apply; next poll will read the real value.
            if self.data is not None:
                self.data["charging_current_limit"] = amps
            self.async_set_updated_data(self.data)

        return success

    async def async_start_charging(self) -> bool:
        """Start charging (write 0 to register 16645)."""
        return await self.async_write_register(16645, [0])

    async def async_stop_charging(self) -> bool:
        """Stop charging (write 1 to register 16645)."""
        return await self.async_write_register(16645, [1])
