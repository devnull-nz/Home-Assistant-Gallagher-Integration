import logging
from .CustomFormatter import CustomFormatter
from enum import Enum
import requests


class ItemOutput:
    def __init__(
        self,
        item_id,
        name="UNKNOWN",
        description="UNKNOWN",
        state=None,
        division=None,
        controller=None,
        status_flags=list(),
        status_text=None,
        commands=dict(),
        api_key="",
    ):
        self.log = logging.getLogger("{}-{}".format(self.__class__.__name__, item_id))
        self.log.setLevel(logging.INFO)
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        ch.setFormatter(CustomFormatter())
        self.log.addHandler(ch)

        # self.log.info("Loading new {} id:{}".format(self.__class__.__name__, item_id))

        self._item_id = item_id
        self._name = name
        self._description = description
        self._state = state
        self._division = division
        self._controller = controller
        self._status_flags = status_flags
        self._status_text = status_text
        self._commands = commands
        self._api_key = api_key

        self._callbacks = []

    def get_item_id(self):
        return self._item_id

    def set_name(self, new_name):
        self._name = new_name
        return True

    def get_name(self):
        return self._name

    def set_description(self, new_description):
        self._description = new_description
        return True

    def get_description(self):
        return self._description

    def set_state(self, new_state):
        if new_state is True or new_state is False or new_state is None:
            self._state = new_state
            return True
        return False

    def get_state(self):
        return self._state

    def set_division(self, new_division):
        self._division = new_division
        return True

    def get_division(self):
        return self._division

    def set_controller(self, new_controller):
        self._controller = new_controller
        return True

    def get_controller(self):
        return self._controller

    def get_status_flags(self):
        return self._status_flags

    def set_new_status_flag(self, new_flag):
        if new_flag not in self._status_flags:
            self._status_flags.append(new_flag)
        return True

    def remove_status_flag(self, flag_to_remove):
        self._status_flags.remove(flag_to_remove)
        return True

    def clear_status_flags(self):
        self._status_flags = []
        return True

    def set_status_text(self, new_text):
        self._status_text = new_text

    def get_status_text(self):
        return self._status_text

    def get_commands(self):
        return self._commands

    def get_command(self, command_name):
        if command_name in self._commands.keys():
            return self._commands[command_name]
        return None

    def set_command(self, command_name, command_url):
        self._commands[command_name] = command_url
        return True

    def handle_update(self, update):
        self.log.debug("Handling update")
        # print(update)
        if "statusText" in update:
            self._status_text = update["statusText"]

        if "statusFlags" in update:
            flags = update["statusFlags"]

            # States
            unknown_flags = [
                "controllerOffline",
                "notPolled",
                "unconfigured",
                "unknown",
            ]
            if any(x in unknown_flags for x in flags):
                self._state = None
            elif "open" in flags:
                self._state = False
            elif "closed" in flags:
                self._state = True
        for callback in self._callbacks:
            callback(self.get_status())
            # print(self)

    def __str__(self):
        return "{} ID:{}, State:{}, Status Text:{}".format(
            self.__class__.__name__, self._item_id, self._state, self._status_text
        )

    def on(self):
        return self.__do_command("on")

    def off(self):
        return self.__do_command("off")

    def cancel_override(self):
        return self.__do_command("cancel")

    def __do_command(self, command):
        # self.log.info("Doing command".format(command))
        try:
            if command not in self._commands.keys():
                self.log.error("`{}` command not in items command list".format(command))
                return False

            if "href" not in self._commands[command].keys():
                self.log.error(
                    "href not is command instructions for command `{}`".format(command)
                )

            self.log.debug(self._commands[command]["href"])
            try:
                req = requests.post(
                    self._commands[command]["href"],
                    verify=False,
                    headers={"Authorization": self._api_key},
                )
                if req.status_code is not 204:
                    self.log.error(
                        "Received status code {} for command {} - Command was not successful".format(
                            req.status_code, command
                        )
                    )
                    # self.log.error(req.)
                    return False
            except Exception:
                self.log.error("Error during command `{}`".format(command))
                return False
            return True

        except Exception as e:
            self.log.error("Unable to do command `{}` due to expection".format(command))
            self.log.error(e)
            return False

    def get_status(self):
        return {
            "state": self._state,
            "gallagher_id": self._item_id,
            "name": self._name,
            "description": self._description,
            "division": self._division,
            "controller": self._controller,
            "status_flags": self._status_flags,
        }

    def register_callback(self, function):
        self.log.debug("Adding callback function {}".format(function.__name__))
        self._callbacks.append(function)


class AlarmZoneState(Enum):
    UNKNOWN = 0
    ARMED = 1
    DISARMED = 2
    EXIT_DELAY = 3
    ENTRY_DELAY = 4
    TRIGGERED = 5
