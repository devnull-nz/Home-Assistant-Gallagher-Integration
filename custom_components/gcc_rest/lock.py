"""Support for Binary inputs from a command centre server."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from homeassistant.components.lock import LockEntity
from homeassistant.const import STATE_LOCKED, STATE_UNLOCKED

from .const import DOMAIN, CONF_API_REF, CONF_USE_ACCESS_ZONES

from .gallagher.GallagherRest import GallagherRest
from .gallagher.ItemAccessZone import AccessZoneState

import logging

_LOGGER = logging.getLogger(__name__)

_STATES = {
    None: None,
    AccessZoneState.UNKNOWN: None,
    AccessZoneState.FREE: STATE_UNLOCKED,
    AccessZoneState.CODE_OR_CARD: STATE_LOCKED,
    AccessZoneState.SECURE: STATE_LOCKED,
    AccessZoneState.DUAL_AUTHENTICATION: STATE_LOCKED,
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
):
    """Set up entry."""
    _LOGGER.info("Loading binary sensors")

    gallagher: GallagherRest = hass.data[DOMAIN][entry.entry_id][CONF_API_REF]

    if entry.data.get(CONF_USE_ACCESS_ZONES) is True:
        _LOGGER.info("Using GCC access zones")
        locks: list[GCCAccessZoneLock] = []

        access_zones = await hass.async_add_executor_job(
            gallagher.get_available_access_zones
        )

        for access_zone in access_zones:
            lock = GCCAccessZoneLock(access_zone, gallagher, entry)
            locks.append(lock)

        async_add_entities(locks)
    else:
        _LOGGER.info("Not using GCC inputs, ceasing setup of binary sensors")


class GCCAccessZoneLock(LockEntity):
    """GCC REST Access Zone Lock Entity."""

    def __init__(self, gallagher_data, gallagher: GallagherRest, entry: ConfigEntry):
        self._gallagher = gallagher
        self._gallagher_id = gallagher_data["id"]

        self._attr_name = "{} {}".format("GCC", gallagher_data["name"])
        self._attr_unique_id = "{}_{}_{}".format(
            "GCC", entry.entry_id, self._gallagher_id
        )

        self._state = None

        self._attr_code_format = None
        self._is_locked = None

        self._extra_state_attributes = {"status_flags": list(), "zone_count": None}
        self._attr_extra_state_attributes = self._extra_state_attributes

        self._attr_supported_features = 0  # No support features

        gallagher.get_access_zone(self._gallagher_id).register_callback(
            self.proccess_callback
        )

    @property
    def state(self):
        """Return the state of the device."""
        return self._state

    def proccess_callback(self, gcc_update):
        """Callback processor"""

        # print(gcc_update)

        self._state = _STATES[gcc_update["state"]]
        self._is_locked = self._state == STATE_LOCKED

        # print(self._state)

        for attr in gcc_update.keys():
            if attr == "state":
                continue

            self._extra_state_attributes[attr] = gcc_update[attr]

        self.async_write_ha_state()

    def lock(self, **kwargs):
        self._gallagher.get_access_zone(self._gallagher_id).set_secure("secure")

    def unlock(self, **kwargs):
        self._gallagher.get_access_zone(self._gallagher_id).set_secure("free")

    async def async_added_to_hass(self) -> None:
        """Handle entity which will be added."""
        await self.async_base_added_to_hass()

    async def async_base_added_to_hass(self) -> None:
        """Handle entity which will be added."""
        self.proccess_callback(
            self._gallagher.get_access_zone(self._gallagher_id).get_status()
        )
