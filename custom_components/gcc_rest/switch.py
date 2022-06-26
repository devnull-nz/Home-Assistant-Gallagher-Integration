"""Support for switch outputs from a command centre server."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from homeassistant.components.switch import SwitchEntity

from .const import DOMAIN, CONF_API_REF, CONF_USE_OUTPUTS

from .gallagher.GallagherRest import GallagherRest

import logging

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
):
    """Set up entry."""
    _LOGGER.info("Loading switches")
    gallagher: GallagherRest = hass.data[DOMAIN][entry.entry_id][CONF_API_REF]

    if entry.data.get(CONF_USE_OUTPUTS) is True:
        _LOGGER.info("Using GCC outputs")
        switches: list[GCCSwitch] = []

        outputs = await hass.async_add_executor_job(gallagher.get_available_outputs)

        for output in outputs:
            switch = GCCSwitch(output, gallagher, entry)
            switches.append(switch)

        # print(outputs)
        async_add_entities(switches)
    else:
        _LOGGER.info("Not using GCC output, ceasing setup of switches")


class GCCSwitch(SwitchEntity):

    """GCC REST swtich."""

    def __init__(self, gallagher_data, gallagher: GallagherRest, entry: ConfigEntry):
        self._gallagher = gallagher
        self._gallagher_id = gallagher_data["id"]

        self._is_on = None

        # print(gallagher_data)

        self._attr_name = "{} {}".format("GCC", gallagher_data["name"])
        self._attr_unique_id = "{}_{}_{}".format(
            "GCC", entry.entry_id, self._gallagher_id
        )
        self._extra_state_attributes = {
            "description": None,
            "division": None,
            "controller": None,
            "status_flags": None,
        }

        self._attr_extra_state_attributes = self._extra_state_attributes

        gallagher.get_output(self._gallagher_id).register_callback(
            self.proccess_callback
        )

    @property
    def is_on(self):
        """Return true if the binary sensor is on."""
        return self._is_on

    def proccess_callback(self, gcc_update):
        """Callback processor"""
        self._is_on = gcc_update["state"]

        for attr in gcc_update.keys():
            if attr == "state":
                continue
            self._extra_state_attributes[attr] = gcc_update[attr]
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Handle entity which will be added."""
        await self.async_base_added_to_hass()

    async def async_base_added_to_hass(self) -> None:
        """Handle entity which will be added."""
        self.proccess_callback(
            self._gallagher.get_output(self._gallagher_id).get_status()
        )

    async def async_get_last_state(self):
        return self._is_on

    def turn_on(self, **kwargs) -> None:
        """Turn the entity on."""
        self._gallagher.get_output(self._gallagher_id).on()

    def turn_off(self, **kwargs):
        """Turn the entity off."""
        self._gallagher.get_output(self._gallagher_id).off()
