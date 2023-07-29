import aiofiles
import aiohttp
import asyncio
import binascii
from distutils.version import StrictVersion
import json
import logging
import os.path
import requests
import struct
import voluptuous as vol

from .exceptions import ReceiverException, ReceiverConnectionException, ReceiverGroupException

from .features import DeviceFeature, ZoneFeature

from aiohttp import ClientSession
from homeassistant.const import (
    ATTR_FRIENDLY_NAME, __version__ as current_ha_version)
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.typing import ConfigType

_LOGGER = logging.getLogger(__name__)

DOMAIN = 'tasmota_receiver'
VERSION = '1.0.0'
MANIFEST_URL = (
    "https://raw.githubusercontent.com/"
    "jorgebeserra/tasmota_receiver/{}/"
    "custom_components/tasmota_receiver/manifest.json")
REMOTE_BASE_URL = (
    "https://raw.githubusercontent.com/"
    "jorgebeserra/tasmota_receiver/{}/"
    "custom_components/tasmota_receiver/")
COMPONENT_ABS_DIR = os.path.dirname(
    os.path.abspath(__file__))

CONF_CHECK_UPDATES = 'check_updates'
CONF_UPDATE_BRANCH = 'update_branch'

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Optional(CONF_CHECK_UPDATES, default=True): cv.boolean,
        vol.Optional(CONF_UPDATE_BRANCH, default='master'): vol.In(
            ['master', 'rc'])
    })
}, extra=vol.ALLOW_EXTRA)

async def async_setup(hass, config):
    """Set up the Tasmota-Receiver component."""
    conf = config.get(DOMAIN)

    if conf is None:
        return True

    check_updates = conf[CONF_CHECK_UPDATES]
    update_branch = conf[CONF_UPDATE_BRANCH]

    async def _check_updates(service):
        await _update(hass, update_branch)

    async def _update_component(service):
        await _update(hass, update_branch, True)

    hass.services.async_register(DOMAIN, 'check_updates', _check_updates)
    hass.services.async_register(DOMAIN, 'update_component', _update_component)

    if check_updates:
        await _update(hass, update_branch, False, False)

    return True

async def _update(hass, branch, do_update=False, notify_if_latest=True):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(MANIFEST_URL.format(branch)) as response:
                if response.status == 200:
                    
                    data = await response.json(content_type='text/plain')
                    min_ha_version = data['homeassistant']
                    last_version = data['updater']['version']
                    release_notes = data['updater']['releaseNotes']

                    if StrictVersion(last_version) <= StrictVersion(VERSION):
                        if notify_if_latest:
                            hass.components.persistent_notification.async_create(
                                "You're already using the latest version!", 
                                title='TasmotaReceiver')
                        return

                    if StrictVersion(current_ha_version) < StrictVersion(min_ha_version):
                        hass.components.persistent_notification.async_create(
                            "There is a new version of Tasmota Receiver integration, but it is **incompatible** "
                            "with your system. Please first update Home Assistant.", title='Tasmota-Receiver')
                        return

                    if do_update is False:
                        hass.components.persistent_notification.async_create(
                            "A new version of Tasmota Receiver integration is available ({}). "
                            "Call the ``tasmota_.update_component`` service to update "
                            "the integration. \n\n **Release notes:** \n{}"
                            .format(last_version, release_notes), title='Tasmota-Receiver')
                        return

                    # Begin update
                    files = data['updater']['files']
                    has_errors = False

                    for file in files:
                        try:
                            source = REMOTE_BASE_URL.format(branch) + file
                            dest = os.path.join(COMPONENT_ABS_DIR, file)
                            os.makedirs(os.path.dirname(dest), exist_ok=True)
                            await Helper.downloader(source, dest)
                        except Exception:
                            has_errors = True
                            _LOGGER.error("Error updating %s. Please update the file manually.", file)

                    if has_errors:
                        hass.components.persistent_notification.async_create(
                            "There was an error updating one or more files of Tasmota Receiver. "
                            "Please check the logs for more information.", title='Tasmota-Receiver')
                    else:
                        hass.components.persistent_notification.async_create(
                            "Successfully updated to {}. Please restart Home Assistant."
                            .format(last_version), title='Tasmota-Receiver')
    except Exception:
       _LOGGER.error("An error occurred while checking for updates.")

class Helper():
    @staticmethod
    async def downloader(source, dest):
        async with aiohttp.ClientSession() as session:
            async with session.get(source) as response:
                if response.status == 200:
                    async with aiofiles.open(dest, mode='wb') as f:
                        await f.write(await response.read())
                else:
                    raise Exception("File not found")