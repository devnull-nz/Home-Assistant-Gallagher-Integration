import requests
import traceback
import logging

from threading import Thread

import time

from .ItemInput import ItemInput
from .ItemOutput import ItemOutput
from .ItemAlarmZone import ItemAlarmZone, AlarmZoneState
from .ItemDoor import ItemDoor, DoorStatusFlags
from .ItemAccessZone import (
    ItemAccessZone,
    AccessZoneState,
    AccessZoneSecureType,
)
from .ItemFenceZone import ItemFenceZone, FenceZoneCommands
from .CustomFormatter import CustomFormatter


from http.client import RemoteDisconnected
from urllib3.exceptions import MaxRetryError, ProtocolError, NewConnectionError
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class GallagherRest:
    def __init__(self, command_centre_host, api_key, ignore_insecure_warning=False):
        # Logging Setup
        self.log = logging.getLogger("GallagherRest")
        self.log.setLevel(logging.DEBUG)
        self.log.debug("Loading...")
        # create console handler with a higher log level
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        ch.setFormatter(CustomFormatter())
        self.log.addHandler(ch)

        self._run_thread = None

        if ignore_insecure_warning:
            from urllib3.exceptions import InsecureRequestWarning

            requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

        # Command Centre Data
        self._ccd_inputs = {}
        self._ccd_outputs = {}
        self._ccd_alarm_zones = {}
        self._ccd_alarms = {}
        self._ccd_access_zones = {}
        self._ccd_doors = {}
        self._ccd_fence_zones = {}
        self._ccd_macros = {}

        # Selected Items
        self._si_inputs = []
        self._si_outputs = []
        self._si_alarm_zones = []
        self._si_access_zones = []
        self._si_doors = []
        self._si_fence_zones = []
        self._si_macros = []

        self._ccd_available_features = {}

        self._run = False

        self.api_key = api_key
        host_addr = command_centre_host
        if not host_addr.endswith("/"):
            host_addr = command_centre_host + "/"

        self._command_centre_host = host_addr

        if self.check_connection(self._command_centre_host, api_key) == False:
            self.log.error("Unable to connect to Command Centre")
            # return False

        # return True

    def check_connection(self, command_centre_host, api_key):
        self.log.info(
            "Testing communications to Command Centre API - Host: {}".format(
                command_centre_host
            )
        )

        # Api base URL
        command_centre_host += "api"
        try:
            # try connecting
            test_req = requests.get(
                command_centre_host,
                verify=False,
                headers={"Authorization": "GGL-API-KEY " + api_key},
            )

            # if everything worked we should have a 200 status code
            if test_req.status_code != 200:
                self.log.warning("You are not authorized to interact with the API")
                return False

            # Check that we get the expected response from this version of the API
            try:
                returned_json = test_req.json()

                expected_keys = ["version", "features"]

                if not all(
                    expected_key in returned_json.keys()
                    for expected_key in expected_keys
                ):
                    # An item was missing
                    self.log.warning(
                        "Missing items in API response, is this a command centre API?"
                    )
                    return False

                return self.check_api_version_and_features(command_centre_host, api_key)

            except Exception:
                self.log.error(
                    "Error decoding response from API, is this a command centre API?"
                )
                return False

        # All the possible errors that could happen, and then some
        except (RemoteDisconnected, ProtocolError) as e:
            self.log.error("Invalid protocol used, are you using HTTPS?")
            return False
        except (MaxRetryError, NewConnectionError) as e:
            self.log.error(
                "Unable to connect to command centre api, have you entered the correct IP address?"
            )
            return False
        except (ConnectionError, ConnectionRefusedError) as e:
            self.log.error("Unable to connect to command centre api")
            return False
        except Exception as e:
            self.log.error(e)
            self.log.error(
                "An error occurred verifying the connection to command centre"
            )
            return False

    def check_api_version_and_features(self, command_centre_host, api_key):
        self.log.info("Checking API compatibility")
        test_req = requests.get(
            command_centre_host,
            verify=False,
            headers={"Authorization": "GGL-API-KEY " + api_key},
        )

        if test_req.status_code != 200:
            self.log.warning("None 200 response received")
            return False

        res_json = test_req.json()

        expected_version = "8.50"
        expected_features = [
            "accessZones",
            "alarms",
            "alarmZones",
            # "cardholders",
            # "cardTypes",
            # "competencies",
            "doors",
            # "elevators",
            "events",
            "fenceZones",
            "inputs",
            "items",
            # "lockerBanks",
            "macros",
            # "operatorGroups",
            "outputs"  # ,
            # "personalDataFields",
            # "roles",
            # "schedules",
            # "visits",
            # "receptions"
        ]

        try:
            if "version" not in res_json.keys():
                self.log.warning("Unable to determine Command Centre Version")
                return False

            if not res_json["version"].startswith(expected_version):
                self.log.warning(
                    "The version of Command Centre API is tested with this integration version, instablity may occur"
                )
                self.log.warning(
                    "Version Found: {} - Major Version Expected: {}".format(
                        res_json["version"], expected_version
                    )
                )
                #return False

            self.log.info("Command Centre Version: {}".format(res_json["version"]))

        except Exception as e:
            self.log.error("Unable to determine Command Centre Version")
            return False

        try:
            if "features" not in res_json.keys():
                self.log.warning("Unable to determine Command Centre features")
                return False

        except Exception as e:
            self.log.error("Unable to determine Command Centre features")
            return False

        for feature in expected_features:
            try:
                if feature in res_json["features"].keys():
                    self._ccd_available_features[feature] = res_json["features"][
                        feature
                    ]
                    self.log.debug("Feature Found: {}".format(feature))
                else:
                    self.log.debug("Feature not available: {}".format(feature))

            except Exception as e:
                self.log.error(
                    "An error occurred checking available features - {}".format(feature)
                )
                return False

        self.log.info(
            "Required Features Available: {}".format(len(self._ccd_available_features))
        )

        if len(self._ccd_available_features) == 0:
            self.log.warning("Command Centre has no required features available")
            return False

        # print(self._ccd_available_features)

        return True

    def set_item_inputs(self, item_list):
        if isinstance(item_list, list):
            self._si_inputs = item_list
            return True
        elif item_list is None:
            self._si_inputs = None
            return True
        return False

    def set_item_outputs(self, item_list):
        if isinstance(item_list, list):
            self._si_outputs = item_list
            return True
        elif item_list is None:
            self._si_outputs = None
            return True
        return False

    def set_item_alarm_zones(self, item_list):
        if isinstance(item_list, list):
            self._si_alarm_zones = item_list
            return True
        elif item_list is None:
            self._si_alarm_zones = None
            return True
        return False

    def set_item_access_zones(self, item_list):
        if isinstance(item_list, list):
            self._si_access_zones = item_list
            return True
        elif item_list is None:
            self._si_access_zones = None
            return True
        return False

    def set_item_doors(self, item_list):
        if isinstance(item_list, list):
            self._si_doors = item_list
            return True
        elif item_list is None:
            self._si_doors = None
            return True
        return False

    def set_item_fence_zones(self, item_list):
        if isinstance(item_list, list):
            self._si_fence_zones = item_list
            return True
        elif item_list is None:
            self._si_fence_zones = None
            return True
        return False

    def set_item_macros(self, item_list):
        if isinstance(item_list, list):
            self._si_macros = item_list
            return True
        elif item_list is None:
            self._si_macros = None
            return True
        return False

    def get_alarms(self):
        return self.__get_available_alarms()

    def get_available_inputs(self):
        return self.__get_available_feature("inputs")

    def get_available_outputs(self):
        return self.__get_available_feature("outputs")

    def __get_available_alarms(self):
        return self.__get_available_feature("alarms")

    def get_available_alarm_zones(self):
        return self.__get_available_feature("alarmZones")

    def get_available_access_zones(self):
        return self.__get_available_feature("accessZones")

    def get_available_doors(self):
        return self.__get_available_feature("doors")

    def get_available_fence_zones(self):
        return self.__get_available_feature("fenceZones")

    def get_available_macros(self):
        return self.__get_available_feature("macros")

    def __get_available_feature(self, feature):
        self.log.info("Checking available feature `{}`".format(feature))
        req = requests.get(
            self._command_centre_host + "api",
            verify=False,
            headers={"Authorization": "GGL-API-KEY " + self.api_key},
        )
        res_json = req.json()

        # Check that we can find the feature in the returned json
        # features -> <feature> -> <feature> -> href
        if "features" not in res_json:
            self.log.warning("`features` item not found in API root")
            return None
        if feature not in res_json["features"]:
            return None
        if feature not in res_json["features"][feature]:
            return None
        if "href" not in res_json["features"][feature][feature]:
            return None

        # Check if the feature is licensed
        try:
            license_req = requests.get(
                self._command_centre_host + "api",
                verify=False,
                headers={"Authorization": "GGL-API-KEY " + self.api_key},
            )
            if license_req.status_code != 200:
                self.log.error(
                    "{} is a non-licensed feature for this system. Please update you license file"
                )
                return None
        except Exception as e:
            self.log.error(e)
            return None

        href = res_json["features"][feature][feature]["href"]

        # To go this features endpoint
        req = requests.get(
            href, verify=False, headers={"Authorization": "GGL-API-KEY " + self.api_key}
        )
        res_json = req.json()

        if "results" not in res_json.keys():
            self.log.error("Unable to find results in API response")
            return None

        return res_json["results"]

    def get_input(self, item_id):
        try:
            item_id = str(item_id)
            if item_id in self._ccd_inputs.keys():
                return self._ccd_inputs[item_id]
        except Exception as e:
            return None
        return None

    def get_alarm_zone(self, item_id):
        try:
            item_id = str(item_id)
            if item_id in self._ccd_alarm_zones.keys():
                return self._ccd_alarm_zones[item_id]
        except Exception as e:
            return None
        return None

    def get_output(self, item_id):
        try:
            item_id = str(item_id)
            if item_id in self._ccd_outputs.keys():
                return self._ccd_outputs[item_id]
        except Exception as e:
            return None
        return None

    def get_door(self, item_id):
        try:
            item_id = str(item_id)
            if item_id in self._ccd_doors.keys():
                return self._ccd_doors[item_id]
        except Exception as e:
            return None
        return None

    def get_access_zone(self, item_id):
        try:
            item_id = str(item_id)
            if item_id in self._ccd_access_zones.keys():
                return self._ccd_access_zones[item_id]
        except Exception as e:
            return None
        return None

    def get_fence_zone(self, item_id):
        # print(self._ccd_fence_zones.keys())
        try:
            item_id = str(item_id)
            if item_id in self._ccd_fence_zones.keys():
                return self._ccd_fence_zones[item_id]
        except Exception as e:
            return None
        return None

    def __setup_item(self, item_name):
        setupable_items = [
            "inputs",
            "outputs",
            "alarmZones",
            "doors",
            "accessZones",
            "fenceZones",
        ]

        selected_items = {
            "inputs": self._si_inputs,
            "outputs": self._si_outputs,
            "alarmZones": self._si_alarm_zones,
            "doors": self._si_doors,
            "accessZones": self._si_access_zones,
            "fenceZones": self._si_fence_zones,
        }

        CCD = {
            "inputs": self._ccd_inputs,
            "outputs": self._ccd_outputs,
            "alarmZones": self._ccd_alarm_zones,
            "doors": self._ccd_doors,
            "accessZones": self._ccd_access_zones,
            "fenceZones": self._ccd_fence_zones,
        }

        objects = {
            "inputs": ItemInput,
            "outputs": ItemOutput,
            "alarmZones": ItemAlarmZone,
            "doors": ItemDoor,
            "accessZones": ItemAccessZone,
            "fenceZones": ItemFenceZone,
        }

        if item_name not in setupable_items:
            self.log.error(
                "Unable to setup {}, not able to be setup by the __setup_item function".format(
                    item_name
                )
            )
            return False

        # Setup items
        # print(self._ccd_available_features)

        if item_name not in self._ccd_available_features.keys():
            self.log.info(
                "`{}` not an available feature, the system will not collect data for this feature".format(
                    item_name
                )
            )
            return False

        if selected_items[item_name] is None:
            # Setup all inputs
            self.log.info("Loading all available {}".format(item_name))
            req = requests.get(
                "{}".format(self._ccd_available_features[item_name][item_name]["href"]),
                verify=False,
                headers={"Authorization": "GGL-API-KEY " + self.api_key},
            )

            if req.status_code != 200:
                self.log.warning(
                    "Unable to access {} data, no {} being loaded".format(
                        item_name, item_name
                    )
                )
                return False

            res_json = req.json()
            if "results" not in res_json:
                self.log.warning(
                    "Unable to decode API response, no {} being loaded".format(
                        item_name
                    )
                )
                return False

            selected_items[item_name] = []
            # Add all the newly found items to the selected inputs, so they can be added below
            for new_item in res_json["results"]:
                selected_items[item_name].append(new_item["id"])

        if selected_items[item_name] is not []:
            # setup inputs listed in self._si_inputs
            self.log.info("Loading Defined {}".format(item_name))
            for new_item_id in selected_items[item_name]:
                req = requests.get(
                    "{}/{}".format(
                        self._ccd_available_features[item_name][item_name]["href"],
                        new_item_id,
                    ),
                    verify=False,
                    headers={"Authorization": "GGL-API-KEY " + self.api_key},
                )

                if req.status_code is not 200:
                    self.log.warning(
                        "Unable to find {} {} in api, not loading {}".format(
                            item_name, new_item_id, item_name
                        )
                    )
                else:
                    res_json = req.json()

                    name = "CC_{}_{}".format(item_name, res_json["id"])
                    if "name" in res_json.keys():
                        name = res_json["name"]

                    description = None
                    if "description" in res_json.keys():
                        description = res_json["name"]

                    division = None
                    if "division" in res_json.keys():
                        division = res_json["division"]["id"]

                    controller = None
                    if "connectedController" in res_json.keys():
                        controller = res_json["connectedController"]["id"]

                    commands = []
                    if "commands" in res_json.keys():
                        commands = res_json["commands"]

                    CCD[item_name][res_json["id"]] = objects[item_name](
                        res_json["id"],
                        name,
                        description,
                        None,
                        division,
                        controller,
                        commands=commands,
                        api_key=self.api_key,
                    )

    def stop(self):
        self._run = False

    def start(self):
        # Reset Command Centre Data
        self._ccd_inputs = {}
        self._ccd_outputs = {}
        self._ccd_alarm_zones = {}
        self._ccd_alarms = {}
        self._ccd_access_zones = {}
        self._ccd_doors = {}
        self._ccd_fence_zones = {}
        self._ccd_macros = {}

        item_ids = []
        setup_methods = [
            {
                "method": self.__setup_item,
                "arg": "inputs",
                "reference": self._ccd_inputs,
            },
            {
                "method": self.__setup_item,
                "arg": "outputs",
                "reference": self._ccd_outputs,
            },
            {
                "method": self.__setup_item,
                "arg": "alarmZones",
                "reference": self._ccd_alarm_zones,
            },
            {"method": self.__setup_item, "arg": "doors", "reference": self._ccd_doors},
            {
                "method": self.__setup_item,
                "arg": "accessZones",
                "reference": self._ccd_access_zones,
            },
            {
                "method": self.__setup_item,
                "arg": "fenceZones",
                "reference": self._ccd_fence_zones,
            },
        ]

        for setup_method in setup_methods:
            try:
                setup_method["method"](setup_method["arg"])
                item_ids += setup_method["reference"]

            except Exception as e:
                self.log.error(traceback.format_exc())
                return False

        if len(item_ids) > 0:
            self._run_thread = Thread(target=self.__run, args=(item_ids,))
            self._run_thread.start()

            timeout = int(time.time()) + 5

            while self._run is not True and timeout < int(time.time()):
                time.sleep(0.001)

            return self._run

        else:
            self.log.info("No items to subscribe to, not initiating a subscription")

        return False

    def __run(self, item_ids):

        next_url = self.__first_subscription(item_ids)
        # self.log.info(next_url)
        exception_occurred = False
        self._run = True
        while self._run == True:
            try:
                if self._run is False:
                    print("Stopping!")
                    break
                    return None
                # self.log.info(next_url)

                update_res = requests.get(
                    next_url,
                    verify=False,
                    headers={"Authorization": self.api_key},
                    timeout=65,
                )
                if update_res.status_code != 200:
                    self.log.warning(
                        "Non 200 status code received, re subscribing to updates"
                    )
                    next_url = self.__first_subscription(item_ids)

                else:
                    update_json = update_res.json()
                    # print(update_json)
                    if "next" not in update_json.keys():
                        self.log.error("Next HREF not in subscription response")
                        raise Exception("Next not found in update response")

                    if "updates" in update_json.keys():
                        self.__handle_new_update(update_json["updates"])

                    next_url = update_json["next"]["href"]

                exception_occurred = False

            except requests.exceptions.ReadTimeout:
                self.log.info("API HTTP timed out")
                next_url = self.__first_subscription(item_ids)

            except Exception as e:
                exception_occurred = True
                self.log.error(traceback.format_exc())

            if exception_occurred:
                time.sleep(1)
                try:
                    next_url = self.__first_subscription(item_ids)
                    self.log.info("Exception occured in API loop")

                except Exception as e:
                    self.log.error(traceback.format_exc())

        return False

    def __first_subscription(self, item_ids):
        sub_req = requests.post(
            "{}api/items/updates".format(self._command_centre_host),
            verify=False,
            headers={"Authorization": self.api_key},
            json={"itemIds": item_ids},
        )
        if sub_req.status_code != 200:
            self.log.error("Non 200 status code when subscribing to updates")
            return ""
        else:
            res_json = sub_req.json()

            if "next" not in res_json.keys():
                self.log.error("Next HREF not in subscription response")
                return ""

            if "updates" in res_json.keys():
                self.__handle_new_update(res_json["updates"])

            return res_json["next"]["href"]

    def __handle_new_update(self, updates):
        # self.log.debug("Handling update")

        # print(updates)

        handlers = [
            self._ccd_inputs,
            self._ccd_outputs,
            self._ccd_alarm_zones,
            self._ccd_doors,
            self._ccd_access_zones,
            self._ccd_fence_zones,
        ]

        for update in updates:
            for handler in handlers:
                if update["id"] in handler.keys():
                    try:
                        handler[update["id"]].handle_update(update)
                    except Exception:
                        self.log.error(
                            "Error during handling item: {} handlers".format(
                                update["id"]
                            )
                        )
