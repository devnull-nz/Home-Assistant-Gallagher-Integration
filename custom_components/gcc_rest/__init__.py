"""The Gallagher Command Centre Integration integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, CONF_API_REF

# from .gallagher.GallagherRest import GallagherRest
from .gcc_rest import *

import logging

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Gallagher Command Centre Integration from a config entry."""

    return await async_gcc_rest_setup(hass, entry)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.info("Unloading gcc_rest entry {entry.entry_id}".format)
    if DOMAIN in hass.data.keys():  # Check that the DOMAIN exists
        if unload_ok := await hass.config_entries.async_unload_platforms(
            entry, PLATFORMS
        ):
            hass.data[DOMAIN][entry.entry_id][CONF_API_REF].stop()
            hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
