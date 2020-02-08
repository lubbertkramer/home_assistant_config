"""
@ Author      : Gerben Jongerius, Paul de Wit, Robin Harmsen
@ Date        : 04/29/2018, 11/01/2018, 04/29/2019
@ Description : Youless Sensor - Monitor power consumption. 
"""
VERSION = '2.0.1'

import json
import logging
from datetime import timedelta
from urllib.request import urlopen

import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant.const import CONF_MONITORED_VARIABLES
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle

DOMAIN = 'youless'
CONF_HOST = "host"

SENSOR_PREFIX = 'youless_'
_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_HOST): cv.string,
        vol.Optional(CONF_MONITORED_VARIABLES, default=['pwr', 'net']): vol.All(
            cv.ensure_list, vol.Length(min=1), [vol.In(['pwr', 'net', 'p1', 'p2', 'n1', 'n2', 'cs0', 'ps0', 'gas'])])
    })
}, extra=vol.ALLOW_EXTRA)

SENSOR_TYPES = {
    'pwr': ['Current Power usage', 'current_power_usage', 'W', 'mdi:flash', 'energy.png'],
    'net': ['Net Power usage', 'net_power_meter', 'kWh', 'mdi:gauge', 'electric-meter.png'],
    'p1': ['Power Meter Low', 'power_meter_low', 'kWh', 'mdi:gauge', 'energy.png'],
    'p2': ['Power Meter High', 'power_meter_high', 'kWh', 'mdi:gauge', 'energy.png'],
    'n1': ['Power Delivery Low', 'power_delivery_low', 'kWh', 'mdi:gauge', 'energy.png'],
    'n2': ['Power Delivery High', 'power_delivery_high', 'kWh', 'mdi:gauge', 'energy.png'],
    'cs0': ['Power Meter Extra', 'power_meter_extra', 'kWh', 'mdi:gauge', 'energy.png'],
    'ps0': ['Current Power usage Extra', 'current_power_usage_extra', 'W', 'mdi:flash', 'energy.png'],
    'gas': ['Gas consumption', 'gas_meter', 'm3', 'mdi:gas-cylinder', 'electric-meter.png']
}


def setup_platform(hass, config, add_devices, discovery_info=None):
    host = config.get(CONF_HOST)
    sensors = config.get(CONF_MONITORED_VARIABLES)
    data_bridge = YoulessDataBridge(host)

    devices = []
    for sensor in sensors:
        sensor_config = SENSOR_TYPES[sensor]
        devices.append(YoulessSensor(data_bridge, sensor_config[0], sensor, sensor_config[1], sensor_config[2], sensor_config[3], sensor_config[4]))

    add_devices(devices)


class YoulessDataBridge(object):

    def __init__(self, host):
        self._url = 'http://' + host + '/e'
        self._data = None

    def data(self):
        return self._data

    @Throttle(timedelta(seconds=1))
    def update(self):
        raw_res = urlopen(self._url)
        self._data = json.loads(raw_res.read().decode('utf-8'))[0]


class YoulessSensor(Entity):

    def __init__(self, data_bridge, name, prpt, sensor_id, uom, icon, image_uri):
        self._state = None
        self._name = name
        self._property = prpt
        self._icon = icon
        #self._image = image_uri
        self._uom = uom
        self._data_bridge = data_bridge
        self.entity_id = 'sensor.' + SENSOR_PREFIX + sensor_id
        self._raw = None

    @property
    def name(self):
        return self._name

    @property
    def icon(self):
        return self._icon

    #@property
    #def entity_picture(self):
    #    return '/local/youless/' + self._image

    @property
    def unit_of_measurement(self):
        return self._uom

    @property
    def state(self):
        return self._state

    @property
    def state_attributes(self):
        if self._raw is not None:
            return {
                'timestamp': self._raw['tm']
            }

    def update(self):
        self._data_bridge.update()
        self._raw = self._data_bridge.data()
        if self._raw is not None:
            self._state = self._raw[self._property]
