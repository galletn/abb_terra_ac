"""Config flow for ABB Terra AC integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from pymodbus.client import ModbusTcpClient

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN, CONF_UNIT_ID

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Optional(CONF_PORT, default=502): int,
        vol.Optional(CONF_UNIT_ID, default=1): int,
    }
)


class ABBTerraACConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for ABB Terra AC."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # Test connection
            host = user_input[CONF_HOST]
            port = user_input.get(CONF_PORT, 502)
            unit_id = user_input.get(CONF_UNIT_ID, 1)

            if await self.hass.async_add_executor_job(
                self._test_connection, host, port, unit_id
            ):
                # Create unique ID based on host
                await self.async_set_unique_id(f"{host}:{port}")
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=f"ABB Terra AC ({host})",
                    data=user_input,
                )
            else:
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    def _test_connection(self, host: str, port: int, unit_id: int) -> bool:
        """Test connection to the wallbox."""
        try:
            client = ModbusTcpClient(host=host, port=port, timeout=3)

            if not client.connect():
                return False

            # Try to read the first register
            result = client.read_holding_registers(
                address=16384, count=1, device_id=unit_id
            )

            client.close()

            return not result.isError()

        except Exception as err:
            _LOGGER.error("Connection test failed: %s", err)
            return False
