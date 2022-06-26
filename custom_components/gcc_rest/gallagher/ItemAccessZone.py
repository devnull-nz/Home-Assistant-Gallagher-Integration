import logging
from .CustomFormatter import CustomFormatter
import requests
from enum import Enum
from strenum import StrEnum


class ItemAccessZone:
    def __init__(
        self,
        item_id,
        name="UNKNOWN",
        description="UNKNOWN",
        state=None,
        division=None,
        controller=None,
        status_flags=[],
        status_text=None,
        commands={},
        api_key="",
        zone_count=0,
    ):
        self.log = logging.getLogger("{0}-{1}".format(self.__class__.__name__, item_id))
        self.log.setLevel(logging.INFO)
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        ch.setFormatter(CustomFormatter())
        self.log.addHandler(ch)

        self.log.info("Loading new {0} id:{1}".format(self.__class__.__name__, item_id))

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

        self._zone_count = zone_count

        self._callbacks = []

    def get_status(self):
        """Returns status of item as dict"""
        return {
            "state": self._state,
            "gallagher_id": self._item_id,
            "name": self._name,
            "description": self._description,
            "division": self._division,
            "controller": self._controller,
            "status_flags": self._status_flags,
            "zone_count": self._zone_count,
        }

    def get_item_id(self):
        """returns item id"""
        return self._item_id

    def get_name(self):
        """returns items gallagher name"""
        return self._name

    def get_description(self):
        """returns items gallagher description"""
        return self._description

    def get_state(self):
        """returns state"""
        return self._state

    def get_division(self):
        """returns division"""
        return self._division

    def get_controller(self):
        """returns controller id"""
        return self._controller

    def get_status_flags(self):
        """returns status flags as a list"""
        return self._status_flags

    def get_status_text(self):
        """returns status text"""
        return self._status_text

    def get_commands(self):
        """returns commands as dict"""
        return self._commands

    def get_command(self, command_name):
        if command_name in self._commands.keys():
            return self._commands[command_name]
        return None

    def set_command(self, command_name, command_url):
        self._commands[command_name] = command_url
        return True

    def get_zone_count(self):
        return self._zone_count

    def handle_update(self, update):
        self.log.debug("Handling update")
        # print(update)
        if "statusText" in update:
            self._status_text = update["statusText"]
            if "Zone count:" in self._status_text:
                self._zone_count = int(self._status_text.split("Zone count:")[1])
                # print("Zone Count: {}".format(self._zone_count))

        # print(update)

        if "statusFlags" in update:
            flags = update["statusFlags"]
            self._status_flags = flags

            # States
            unknown_flags = [
                "controllerOffline",
                "notPolled",
                "unconfigured",
                "unknown",
            ]
            if any(x in unknown_flags for x in flags):
                self._state = None
            elif "free" in flags:
                self._state = AccessZoneState.FREE
            elif "secure" in flags:
                self._state = AccessZoneState.SECURE
            elif "dualAuth" in flags:
                self._state = AccessZoneState.DUAL_AUTHENTICATION
            elif "codeOrCard" in flags:
                self._state = AccessZoneState.CODE_OR_CARD

            # print(self)

        for callback in self._callbacks:
            callback(self.get_status())

    def __str__(self):
        return "{} ID:{}, State:{}, Status Text:{}, Zone Count: {}".format(
            self.__class__.__name__,
            self._item_id,
            self._state,
            self._status_text,
            self._zone_count,
        )

    def __do_command(self, command):
        # self.log.info("Doing command {} ".format(command))
        try:
            if command not in self._commands.keys():
                self.log.error(
                    "`{0}` command not in items command list".format(command)
                )
                return False

            if "href" not in self._commands[command].keys():
                self.log.error(
                    "href not is command instructions for command `{0}`".format(command)
                )

            self.log.debug(self._commands[command]["href"])
            try:
                req = requests.post(
                    self._commands[command]["href"],
                    verify=False,
                    headers={"Authorization": self._api_key},
                )
                if req.status_code != 204:
                    self.log.error(
                        "Received status code {0} for command {1} - Command was not successful".format(
                            req.status_code, command
                        )
                    )
                    # self.log.error(req.)
                    return False
            except Exception as e:
                self.log.error("Error during command `{0}`".format(command))
                return False
            return True

        except Exception as e:
            self.log.error(
                "Unable to do command `{0}` due to expection".format(command)
            )
            self.log.error(e)
            return False

    def set_secure(self, secure_type):
        try:
            secure_type = str(secure_type)
        except Exception:
            return False

        allowed_commands = [
            "free",
            "freePin",
            "secure",
            "securePin",
            "codeOnly",
            "codeOnlyPin",
            "dualAuth",
            "lockDown",
            "cancelLockDown",
            "forgiveAntiPassback",
            "cancel",
        ]

        if secure_type not in allowed_commands:
            self.log.error(
                "{0} not a command available via set_secure() method".format(
                    secure_type
                )
            )
            return False
        return self.__do_command(secure_type)

    def register_callback(self, function):
        self.log.debug("Adding callback function {0}".format(function.__name__))
        self._callbacks.append(function)


class AccessZoneState(Enum):
    """States of an Access Zone"""

    UNKNOWN = None
    SECURE = 1
    DUAL_AUTHENTICATION = 2
    CODE_OR_CARD = 3
    FREE = 4


class AccessZoneSecureType(StrEnum):
    """Types of Secure states for an Access Zone"""

    FREE = "free"
    FREE_PIN = "freePin"
    SECURE = "secure"
    SECURE_PIN = "securePin"
    CODE_ONLY = "codeOnly"
    CODE_ONLY_PIN = "codeOnlyPin"
    DUAL_AUTH = "dualAuth"
    LOCK_DOWN = "lockDown"
    CANCEL_LOCK_DOWN = "cancelLockDown"
    FORGIVE_ANTI_PASSBACK = "forgiveAntiPassback"
    CANCEL_OVERRIDE = "cancel"
