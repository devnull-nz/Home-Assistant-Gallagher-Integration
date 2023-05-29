"""The Gallagher Command Centre Integration integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import (
    DOMAIN,
    CONF_API_REF,
    CONF_HOST,
    CONF_API_KEY,
    CONF_USE_INPUTS,
    CONF_USE_OUTPUTS,
    CONF_USE_ALARM_ZONES,
    CONF_USE_ACCESS_ZONES,
    CONF_USE_DOORS,
    CONF_USE_FENCE_ZONES,
)

from .gallagher.GallagherRest import GallagherRest


import logging
import time

_LOGGER = logging.getLogger(__name__)

# The platforms we support
PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.SWITCH,
    Platform.ALARM_CONTROL_PANEL,
    Platform.LOCK,
    Platform.COVER,
    # Platform.SELECT,
    Platform.SENSOR,
]


async def async_gcc_rest_setup(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """A Doc String"""
    if DOMAIN not in hass.data.keys():
        _LOGGER.debug("hass.data[DOMAIN] doesn't exist, creating... ")
        hass.data[DOMAIN] = {}
    else:
        _LOGGER.debug("hass.data[DOMAIN] found")

    hass.data[DOMAIN][entry.entry_id] = storage = {}
    _LOGGER.info("Loading API module")

    await hass.async_add_executor_job(load_api, storage, entry)
    gallagher: GallagherRest = storage[CONF_API_REF]

    if entry.data.get(CONF_USE_INPUTS) is True:
        # We are using inputs
        gallagher.set_item_inputs(None)

    if entry.data.get(CONF_USE_OUTPUTS) is True:
        # We are using outputs
        gallagher.set_item_outputs(None)

    if entry.data.get(CONF_USE_ALARM_ZONES) is True:
        # We are using alarm zones
        gallagher.set_item_alarm_zones(None)

    if entry.data.get(CONF_USE_ACCESS_ZONES) is True:
        # We are using access zones
        gallagher.set_item_access_zones(None)

    if entry.data.get(CONF_USE_DOORS) is True:
        # We are using doors
        gallagher.set_item_doors(None)

    if entry.data.get(CONF_USE_FENCE_ZONES) is True:
        # We are using fence zones
        gallagher.set_item_fence_zones(None)

    await hass.async_add_executor_job(gallagher.start)
    await hass.async_add_executor_job(time.sleep, 1)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


def load_api(storage, entry: ConfigEntry):
    """A Doc String"""
    # We have to seperate this to a seperate function as the __init__ function is not async
    storage[CONF_API_REF] = GallagherRest(
        entry.data.get(CONF_HOST), entry.data.get(CONF_API_KEY)
    )
