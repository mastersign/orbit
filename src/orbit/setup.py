#!/usr/bin/python3

# Package orbit.setup

import os, json

class Configuration:

	DEFAULT_HOST = "localhost"
	DEFAULT_PORT = 4223
	DEFAULT_CORE_TRACING = True
	DEFAULT_DEVICE_TRACING = False
	DEFAULT_EVENT_TRACING = False
	DEFAULT_COMPONENT_TRACING = True

	@property
	def host(self):
	    return self._host
	@host.setter
	def host(self, value):
	    self._host = value
	
	@property
	def port(self):
	    return self._port
	@port.setter
	def port(self, value):
	    self._port = value
	
	@property
	def core_tracing(self):
	    return self._core_tracing
	@core_tracing.setter
	def core_tracing(self, value):
	    self._core_tracing = value
	
	@property
	def device_tracing(self):
	    return self._device_tracing
	@device_tracing.setter
	def device_tracing(self, value):
	    self._device_tracing = value
	
	@property
	def event_tracing(self):
	    return self._event_tracing
	@event_tracing.setter
	def event_tracing(self, value):
	    self._event_tracing = value

	@property
	def component_tracing(self):
	    return self._component_tracing
	@component_tracing.setter
	def component_tracing(self, value):
	    self._component_tracing = value
	

	def _configfile_path(self):
		return os.path.realpath(os.path.expanduser('~/.tink'))

	def _write_configfile(self, data):
		with open(self._configfile_path(), 'w', encoding='utf-8') as f:
			f.write(json.dumps(data))

	def __init__(self):
		self._host = Configuration.DEFAULT_HOST
		self._port = Configuration.DEFAULT_PORT
		self._core_tracing = Configuration.DEFAULT_CORE_TRACING
		self._device_tracing = Configuration.DEFAULT_DEVICE_TRACING
		self._event_tracing = Configuration.DEFAULT_EVENT_TRACING
		self._component_tracing = Configuration.DEFAULT_COMPONENT_TRACING

		self.load()

	def _to_data(self):
		return {
			'host': self._host,
			'port': self._port,
			'core_tracing': self._core_tracing,
			'device_tracing': self._device_tracing,
			'event_tracing': self._event_tracing,
			'component_tracing': self._component_tracing
		}

	def _from_data(self, data):
		if type(data) is dict:
			if 'host' in data:
				self.host = str(data['host'])
			if 'port' in data:
				self.port = int(data['port'])
			if 'core_tracing' in data:
				self._core_tracing = bool(data['core_tracing'])
			if 'device_tracing' in data:
				self._device_tracing = bool(data['device_tracing'])
			if 'event_tracing' in data:
				self._event_tracing = bool(data['event_tracing'])
			if 'component_tracing' in data:
				self._component_tracing = bool(data['component_tracing'])

	def load(self):
		configfile = self._configfile_path()
		if not os.path.isfile(configfile):
			return
		with open(configfile, 'r', encoding='utf-8') as f:
			configdata = json.loads(f.read())
			self._from_data(configdata)

	def save(self):
		self._write_configfile(self._to_data())


# script execution
if __name__ == '__main__':
	cc = ConnConfig()
	print('Orbit Setup:\n'
		+ 'Host           = ' + str(cc.host()) + '\n'
		+ 'Port           = ' + str(cc.port()) + '\n'
		+ 'Core Tracing   = ' + str(cc.core_tracing()) + '\n'
		+ 'Device Tracing = ' + str(cc.device_tracing()) + '\n'
		+ 'Event Tracing  = ' + str(cc.event_tracing()))
