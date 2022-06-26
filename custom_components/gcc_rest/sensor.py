"""Support for Binary inputs from a command centre server."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components.sensor import SensorEntity

from .const import DOMAIN, CONF_API_REF, CONF_USE_FENCE_ZONES

from .gallagher.GallagherRest import GallagherRest


import logging

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
):
    """Set up entry."""
    _LOGGER.info("Loading sensors")

    gallagher: GallagherRest = hass.data[DOMAIN][entry.entry_id][CONF_API_REF]

    if entry.data.get(CONF_USE_FENCE_ZONES) is True:
        _LOGGER.info("Using GCC fence zones (sensor)")
        sensors: list[GCCFenceZoneSensor] = []

        fences = await hass.async_add_executor_job(gallagher.get_available_fence_zones)

        for fence in fences:
            sensor = GCCFenceZoneSensor(fence, gallagher, entry)
            sensors.append(sensor)

        # print(inputs)

        async_add_entities(sensors)
    else:
        _LOGGER.info("Not using GCC fence zones (sensor)")


class GCCFenceZoneSensor(SensorEntity):
    """GCC REST binary sensor."""

    def __init__(self, gallagher_data, gallagher: GallagherRest, entry: ConfigEntry):
        self._gallagher = gallagher
        self._gallagher_id = gallagher_data["id"]

        self._native_value = None
        self._attr_native_unit_of_measurement = "V"
        self._attr_device_class = "voltage"
        # self._attr_state_class

        self._attr_name = "{} {}".format("GCC", gallagher_data["name"])
        self._attr_unique_id = "{}_{}_{}".format(
            "GCC", entry.entry_id, self._gallagher_id
        )
        self._extra_state_attributes = {
            "state": None,
            "is_tampered": None,
            "is_isolated": None,
            "is_shunted": None,
            "is_voltage_known": None,
            "is_locked_out": None,
            "is_service_mode": None,
            "gallagher_id": None,
            "name": None,
            "description": None,
            "division": None,
            "controller": None,
            "status_flags": None,
            "voltage": None,
        }

        self._attr_extra_state_attributes = self._extra_state_attributes

        gallagher.get_fence_zone(self._gallagher_id).register_callback(
            self.proccess_callback
        )

    @property
    def state(self):
        """Return the state of the device."""
        return self._native_value

    def proccess_callback(self, gcc_update):
        """Callback processor"""
        for attr in gcc_update.keys():
            if attr == "voltage":
                self._extra_state_attributes[attr] = gcc_update[attr]
                self._native_value = gcc_update[attr]

            self._extra_state_attributes[attr] = gcc_update[attr]
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Handle entity which will be added."""
        await self.async_base_added_to_hass()

    async def async_base_added_to_hass(self) -> None:
        """Handle entity which will be added."""
        self.proccess_callback(
            self._gallagher.get_fence_zone(self._gallagher_id).get_status()
        )

    async def async_get_last_state(self):
        """Returns item state"""
        return self._native_value
