"""Support for Binary inputs from a command centre server."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from homeassistant.components.alarm_control_panel import (
    AlarmControlPanelEntity,
    AlarmControlPanelEntityFeature,
)
from homeassistant.const import (
    STATE_ALARM_ARMED_AWAY,
    STATE_ALARM_ARMED_HOME,
    STATE_ALARM_ARMED_NIGHT,
    STATE_ALARM_DISARMED,
    STATE_ALARM_ARMING,
    STATE_ALARM_TRIGGERED,
    STATE_ALARM_PENDING,
)

from .const import DOMAIN, CONF_API_REF, CONF_USE_ALARM_ZONES

from .gallagher.GallagherRest import GallagherRest
from .gallagher.ItemAlarmZone import AlarmZoneState, AlarmZoneFenceState

import logging

_LOGGER = logging.getLogger(__name__)

_STATES = {
    AlarmZoneState.UNKNOWN: None,
    AlarmZoneState.ARMED: STATE_ALARM_ARMED_AWAY,
    AlarmZoneState.DISARMED: STATE_ALARM_DISARMED,
    AlarmZoneState.USER_1: STATE_ALARM_ARMED_NIGHT,
    AlarmZoneState.USER_2: STATE_ALARM_ARMED_HOME,
    AlarmZoneState.EXIT_DELAY: STATE_ALARM_ARMING,
    AlarmZoneState.ENTRY_DELAY: STATE_ALARM_PENDING,
    AlarmZoneState.TRIGGERED: STATE_ALARM_TRIGGERED,
}

_STATES_FENCE = {
    AlarmZoneFenceState.UNKNOWN: None,
    AlarmZoneFenceState.LOW_FEEL: "low_feel",
    AlarmZoneFenceState.HIGH_VOLTAGE: "high_voltage",
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
):
    """Set up entry."""
    _LOGGER.info("Loading alarm zones")

    gallagher: GallagherRest = hass.data[DOMAIN][entry.entry_id][CONF_API_REF]

    if entry.data.get(CONF_USE_ALARM_ZONES) is True:
        _LOGGER.info("Using GCC alarm zones")
        alarm_panels: list[GCCAlarmControlPanel] = []

        zones = await hass.async_add_executor_job(gallagher.get_available_alarm_zones)

        for zone in zones:
            alarm_panel = GCCAlarmControlPanel(zone, gallagher, entry)
            alarm_panels.append(alarm_panel)

        async_add_entities(alarm_panels)
    else:
        _LOGGER.info("Not using GCC inputs, ceasing setup of alarm control panels")


class GCCAlarmControlPanel(AlarmControlPanelEntity):
    """GCC REST Control Panel."""

    def __init__(self, gallagher_data, gallagher: GallagherRest, entry: ConfigEntry):
        # print(gallagher_data)
        self._gallagher = gallagher
        self._gallagher_id = gallagher_data["id"]

        self._state = None

        self._attr_name = "{} {}".format("GCC", gallagher_data["name"])
        self._attr_unique_id = "{}_{}_{}".format(
            "GCC", entry.entry_id, self._gallagher_id
        )

        self._extra_state_attributes = {
            "status_flags": list(),
            "fence_state": None,
            "status_text": None,
        }
        self._attr_extra_state_attributes = self._extra_state_attributes

        self._attr_code_arm_required = False
        self._attr_supported_features = (
            AlarmControlPanelEntityFeature.ARM_HOME
            | AlarmControlPanelEntityFeature.ARM_AWAY
            | AlarmControlPanelEntityFeature.ARM_HOME
            | AlarmControlPanelEntityFeature.ARM_NIGHT
        )

        gallagher.get_alarm_zone(self._gallagher_id).register_callback(
            self.proccess_callback
        )

    @property
    def state(self):
        """Return the state of the device."""
        return self._state

    @property
    def code_format(self):
        """We dont support using codes to change alarm states"""
        return None

    def alarm_disarm(self, code: str | None = None) -> None:
        """Send disarm command."""
        self._gallagher.get_alarm_zone(self._gallagher_id).disarm()

    def alarm_arm_home(self, code: str | None = None) -> None:
        """Send arm user_1_mode/home command."""
        self._gallagher.get_alarm_zone(self._gallagher_id).user_1_mode()

    def alarm_arm_away(self, code: str | None = None) -> None:
        """Send arm away command."""
        self._gallagher.get_alarm_zone(self._gallagher_id).arm()

    def alarm_arm_night(self, code: str | None = None) -> None:
        """Send arm user_2_mode/night command."""
        self._gallagher.get_alarm_zone(self._gallagher_id).user_2_mode()

    def proccess_callback(self, gcc_update):
        """Callback processor"""
        # self._is_on = gcc_update["state"]

        self._state = _STATES[gcc_update["state"]]
        self._extra_state_attributes["fence_state"] = _STATES_FENCE[
            gcc_update["fence_state"]
        ]
        self._extra_state_attributes["status_text"] = gcc_update["status_text"]
        self._extra_state_attributes["status_flags"] = gcc_update["status_flags"]

        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Handle entity which will be added."""
        await self.async_base_added_to_hass()

    async def async_base_added_to_hass(self) -> None:
        """Handle entity which will be added."""
        self.proccess_callback(
            self._gallagher.get_alarm_zone(self._gallagher_id).get_status()
        )

    async def async_get_last_state(self):
        """Returns state of alarm panel"""
        return self._state
