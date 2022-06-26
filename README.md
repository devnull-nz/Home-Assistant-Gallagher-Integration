# Home-Assistant-Gallagher-Integration
This custom component for [Home Assistant](https://www.home-assistant.io) allows integration with a Gallagher Command Centre server

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

# Supported Functions
* Monitor & open door
* Monitor & override alarm zone (user 1 & 2 modes not supported)
* Monitor & override access zone (Free & Secure (No PIN) modes only)
* Monitor & override output state
* Monitor input state
* Monitor fence zone voltage


# Installation Instructions
## Prerequisites
Installation of this integration can be done either manually, or with [HACS](https://hacs.xyz/).
<br>This guide will provide instructions on installation using HACS.
<br>Follow the instructions, available on the HACS website [https://hacs.xyz/](https://hacs.xyz/) to install and configure HACS.

<br>For security purproses, this guide requries that your Home Assistant installation uses a static IP address. Please follow the appropiate guide for your Home Assistant deployment method. 
<br>

## Installation
Once HACS is installed, open it by clicking the icon in the sidebar.
<br>Once loaded, click on the `Integrations` menu, this will open the HACS integration selection menu.
<br>Click the settings icon in the top right hand corner of the page, and select the `Custom Repositories` option.
<br>In the text box labed `Repository`, copy and paste the following:
<br> `https://github.com/devnull-nz/Home-Assistant-Gallagher-Integration`
<br> select the category as `Integration`, then click add.
<br><br>The integration should now appear in the custom repositories list.
<br>Click on the integration in the list, and then at the bottom of the page, select `Download This Repository With HACS`.
When prompted, confirm this by clicking on the `DOWNLOAD` option.
<br>You will now need to restart Home Assitant, do this by going to the Settings menu -> System, and pressing the restart button in the top right corner.
<br>Home Assistant will now restart, and the integration will be available to configure. 


## Configuration
Once installed, you will need to configure the integration.
<br>Configuration is done in two sections, Command Centre config, and Home Assistant config.

<br><br>

### Command Centre Configuration
Start by opening the Command Centre configuration client.
<br> Go to the File -> Server Properties -> Web Services menu, and enable the REST API and `REST Client with no client certificate` options. Make a note of the `Server Base Port`, and save these changes by clicking `Apply`.
<br>Next, create a new cardholder, and name it something memorible such as `Home Assistant REST`. provide it access to the appropiate access groups, and save these changes by clicking `Apply`.
<br><b>Note: It is recommended to create a access group solely for Home Assistant</b>
<br><br>
Next create a new operator group, again name this somehting memorible.
<br>Allocate the cardholder you just created as an operator, and assign operator privleges, and save these changes by clicking `Apply`
<br><b>Note: Assign only the minimum required operator privledges necessary for you intended use</b>
<br><br>
Next, Go to the Configure -> Services and Workstations menu, and add a new REST Client. Name it something memorible.
<br> Click on the `API Key` menu, and make a note of the API Key.
Allocate the cardholder you created as the REST Client Operator.
<br>On the `IP Filtering` tab, enable IP filtering, and enter you Home Assistant server IP address
<br>Finally, save these changes by clicking `Apply`
<br>Command Centre is now configured.
<br>

<br><br>

### Home Assistant Configuration
In Home Assistant, go to the Settings -> Devices & Services -> Integrations menu.
<br>Click the `Add Integration` button on the lower right side of the screen.
<br>Search for, and click on the `Gallagher Command Centre` option, this will open the configuration menu.
<br>Type the URL of your Command Centre REST API, and your API KEY, select the options you wish to use, and click submit.
<br>Note: the URL will be in the following format<br> `https://<command centre ip>:<rest api port>/`

<br><br>

# Data Type / Platform Entites
The items imported from Command Centre are avaialble in Home Assistant using a plaform entity most appropiate for their function.
<br>The key data point of each item will be the value of the entity, and all other data points will be avialble as attributes

* Alarm Zone
<br>Displayed as an alarm control panel, the alarm zone state is available as the entity value (Disarmed = disarmed, Armed Away = Armed). User modes 1 & 2 are not supported. Only the status text, and associated fence zone state are available as attributes.

* Access Zone
<br> Displayed as a lock sensor, the access zone state is available as the entity value (locked=Secure No Pin/unlocked=FREE). The zone count (if enabled) is  available as an attribute

* Door
<br> Displayed as a cover entity, the door state is available as the entity value (open/closed). Tampered, secure, etc are available as attributes

* Fence Zone
<br> Displayed as a numerical sensor, the fence voltage is available as the entity value. Shunted, locked out, etc are available as attributes

* Input
<br> Displayed as a binary sensor

* Output
<br> Displayed as a switch


<br><br>


# FAQ
* <b>Does this integration require additional Command Centre Licenses?</b>
<br>Yes, this integration requires the RESTStatus and RESTOverrides feature to be enabled in your Command Centre License file.
* <b>Can I select the items to import?</b>
<br>The current version of the integration automatically finds, and imports all items of each selected group. There is currently no way to limit which items to import. If your installation has more then 1,000 of any item type, only the first 1,000  will be imported into Home Assistant.

<br>

