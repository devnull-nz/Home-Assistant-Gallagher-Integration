"""Support for Covers/Door from a command centre server."""
from __future__ import annotations


from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from homeassistant.components.cover import (
    CoverEntity,
    CoverDeviceClass,
    CoverEntityFeature,
)
from homeassistant.const import STATE_OPEN, STATE_CLOSED

from .const import DOMAIN, CONF_API_REF, CONF_USE_DOORS

from .gallagher.GallagherRest import GallagherRest

import logging

_LOGGER = logging.getLogger(__name__)


STATES = {True: STATE_OPEN, False: STATE_CLOSED, None: None}
DEVICE_CLASS_DOOR = CoverDeviceClass.DOOR


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
):
    """Set up entry."""
    _LOGGER.info("Loading switches")
    gallagher: GallagherRest = hass.data[DOMAIN][entry.entry_id][CONF_API_REF]
    if entry.data.get(CONF_USE_DOORS) is True:
        # We are using doors
        _LOGGER.info("Using GCC Doors")
        covers: list[GCCDoor] = []

        doors = await hass.async_add_executor_job(gallagher.get_available_doors)

        for door in doors:
            cover = GCCDoor(door, gallagher, entry)
            covers.append(cover)

        # print(outputs)
        async_add_entities(covers)

    else:
        _LOGGER.info("Not using GCC doors, ceasing setup of door toggle switches")


class GCCDoor(CoverEntity):
    """GCC Rest Door"""

    def __init__(self, gallagher_data, gallagher: GallagherRest, entry: ConfigEntry):
        self._gallagher = gallagher
        self._gallagher_id = gallagher_data["id"]

        self._state = None

        self._attr_is_closed = None
        self._stat_attr_is_closed = None

        self._attr_supported_features = CoverEntityFeature.OPEN

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

        gallagher.get_door(self._gallagher_id).register_callback(self.proccess_callback)

    def open_cover(self, **kwargs):
        """Open the cover."""
        self._gallagher.get_door(self._gallagher_id).open()

    def proccess_callback(self, gcc_update):
        """Callback processor"""
        self._state = STATES[gcc_update["is_open"]]
        self._stat_attr_is_closed = gcc_update["is_open"] is False

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
            self._gallagher.get_door(self._gallagher_id).get_status()
        )

    @property
    def state(self):
        """Returns state of door"""
        return self._state

    async def async_get_last_state(self):
        """Returns state of door"""
        return self._state
