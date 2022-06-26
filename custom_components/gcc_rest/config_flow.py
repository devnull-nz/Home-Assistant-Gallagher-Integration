"""Config flow for Gallagher Command Centre Integration integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from .gallagher.GallagherRest import GallagherRest

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN, CONF_HOST, CONF_API_KEY

_LOGGER = logging.getLogger(__name__)


def validate_host_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """

    # print(data)

    if str(data[CONF_HOST]).endswith("/") is False:
        data[CONF_HOST] += "/"

    gallagher = GallagherRest(data[CONF_HOST], data[CONF_API_KEY])
    if gallagher.check_connection(data[CONF_HOST], data[CONF_API_KEY]) is False:
        raise CannotConnect

    # If you cannot connect:
    # throw CannotConnect
    # If the authentication is wrong:
    # InvalidAuth

    # Return info that you want to store in the config entry.
    return {
        "title": "Gallagher Command Centre",
        CONF_HOST: data[CONF_HOST],
        CONF_API_KEY: data[CONF_API_KEY],
        "use_inputs": data["use_inputs"],
        "use_outputs": data["use_outputs"],
        "use_doors": data["use_doors"],
        "use_alarm_zones": data["use_alarm_zones"],
        "use_access_zones": data["use_access_zones"],
        "use_fence_zones": data["use_fence_zones"],
    }


def create_host_data_schema(
    host="https://192.168.1.1:8904",
    api_key="xxxx-xxxx-xxxx-xxxx-xxxx-xxxx",
    use_inputs=True,
    use_outputs=True,
    use_doors=True,
    use_alarm_zones=True,
    use_access_zones=True,
    use_fence_zones=True,
):
    """Returns the schema for the UI configuration interface"""
    return vol.Schema(
        {
            vol.Required(CONF_HOST, description={"suggested_value": host}): str,
            vol.Required(CONF_API_KEY, description={"suggested_value": api_key}): str,
            vol.Required("use_inputs", default=use_inputs): cv.boolean,
            vol.Required("use_outputs", default=use_outputs): cv.boolean,
            vol.Required("use_doors", default=use_doors): cv.boolean,
            vol.Required("use_alarm_zones", default=use_alarm_zones): cv.boolean,
            vol.Required("use_access_zones", default=use_access_zones): cv.boolean,
            vol.Required("use_fence_zones", default=use_fence_zones): cv.boolean,
        }
    )


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Gallagher Command Centre Integration."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=create_host_data_schema()
            )

        errors = {}

        try:
            info = await self.hass.async_add_executor_job(
                validate_host_input, self.hass, user_input
            )
        except CannotConnect:
            errors["base"] = "cannot_connect"
        except InvalidAuth:
            errors["base"] = "invalid_auth"
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
        else:
            return self.async_create_entry(title=info["title"], data=info)

        return self.async_show_form(
            step_id="user",
            data_schema=create_host_data_schema(
                user_input[CONF_HOST], user_input[CONF_API_KEY]
            ),
            errors=errors,
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
