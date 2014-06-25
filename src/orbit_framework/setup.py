#!/usr/bin/python3
# coding=utf-8

# Module orbit_framework.setup

# Hint: This module is runnable as a script 
#       to print the current configuration.

"""
Dieses Modul implementiert die Setup-Steuerung für ORBIT.

.. note::
	Dieses Modul kann auch als Skript ausgeführt werden, es gibt
	dann die aktuelle ORBIT-Konfiguration aus.

Dieses Modul enthält die folgenden Klassen:

- :py:class:`Configuration`
"""

import os, json

class Configuration:
	"""
	Diese Klasse verwaltet globale Konfigurationsparameter für ORBIT.
	Jeder Parameter ist mit einem Standardwert vorbelegt und kann
	in der Datei ``<Benutzerverzeichnis>/.orbit`` überschrieben werden.
	Dazu besitzt die Kasse die Methoden :py:meth:`load` and :py:meth:`save`.
	Die Methode :py:meth:`load` wird bereits automatisch beim Instanzieren aufgerufen.

	Die Klasse unterstützt die String-Darstellung mit :py:func:`str`.
	"""

	DEFAULT_HOST = "localhost"
	DEFAULT_PORT = 4223
	DEFAULT_CONNECTION_RETRY_TIME = 10
	DEFAULT_CORE_TRACING = True
	DEFAULT_DEVICE_TRACING = True
	DEFAULT_EVENT_TRACING = False
	DEFAULT_JOB_TRACING = True
	DEFAULT_COMPONENT_TRACING = False

	@property
	def host(self):
		"""Der Hostname für die Netzwerkverbindung zum Brick-Deamon oder Master-Brick. (*string*)"""
		return self._host
	@host.setter
	def host(self, value):
		self._host = value
	
	@property
	def port(self):
		"""Der Port für die Netzwerkverbindung zum Brick-Deamon oder Master-Brick. (*int*)"""
		return self._port
	@port.setter
	def port(self, value):
		self._port = value
	
	@property
	def connection_retry_time(self):
		"""Die Zeitspanne in Sekunden nachdem eine fehlgeschlagene IP-Verbindung wieder aufgebaut werden soll."""
		return self._connection_retry_time
	@connection_retry_time.setter
	def connection_retry_time(self, value):
		self._connection_retry_time = value
	

	@property
	def core_tracing(self):
		"""Aktiviert die Trace-Nachrichtenausgabe vom ORBIT-Kern. (*bool*)"""
		return self._core_tracing
	@core_tracing.setter
	def core_tracing(self, value):
		self._core_tracing = value
	
	@property
	def device_tracing(self):
		"""Aktiviert die Trace-Nachrichten des Gerätemanagers von ORBIT. (*bool*)"""
		return self._device_tracing
	@device_tracing.setter
	def device_tracing(self, value):
		self._device_tracing = value
	
	@property
	def event_tracing(self):
		"""Aktiviert die Trace-Nachrichten des Nachrichtenbusses von ORBIT. (*bool*)"""
		return self._event_tracing
	@event_tracing.setter
	def event_tracing(self, value):
		self._event_tracing = value

	@property
	def job_tracing(self):
		"""Aktiviert die Trace-Nachrichten auf Job-Ebene. (*bool*)"""
		return self._job_tracing
	@job_tracing.setter
	def job_tracing(self, value):
		self._job_tracing = value
	
	@property
	def component_tracing(self):
		"""Aktiviert die Trace-Nachrichten auf Component-Ebene. (*bool*)"""
		return self._component_tracing
	@component_tracing.setter
	def component_tracing(self, value):
		self._component_tracing = value
	

	def _configfile_path(self):
		return os.path.realpath(os.path.expanduser('~/.orbit'))

	def _write_configfile(self, data):
		with open(self._configfile_path(), 'w', encoding='utf-8') as f:
			f.write(json.dumps(data))

	def __init__(self):
		self._host = Configuration.DEFAULT_HOST
		self._port = Configuration.DEFAULT_PORT
		self._connection_retry_time = Configuration.DEFAULT_CONNECTION_RETRY_TIME
		self._core_tracing = Configuration.DEFAULT_CORE_TRACING
		self._device_tracing = Configuration.DEFAULT_DEVICE_TRACING
		self._event_tracing = Configuration.DEFAULT_EVENT_TRACING
		self._job_tracing = Configuration.DEFAULT_JOB_TRACING
		self._component_tracing = Configuration.DEFAULT_COMPONENT_TRACING

		self.load()

	def _to_data(self):
		return {
			'host': self._host,
			'port': self._port,
			'connection_retry_time': self._connection_retry_time,
			'core_tracing': self._core_tracing,
			'device_tracing': self._device_tracing,
			'event_tracing': self._event_tracing,
			'job_tracing': self._job_tracing,
			'component_tracing': self._component_tracing
		}

	def _from_data(self, data):
		if type(data) is dict:
			if 'host' in data:
				self.host = str(data['host'])
			if 'port' in data:
				self.port = int(data['port'])
			if 'connection_retry_time' in data:
				self._connection_retry_time = int(data['connection_retry_time'])
			if 'core_tracing' in data:
				self._core_tracing = bool(data['core_tracing'])
			if 'device_tracing' in data:
				self._device_tracing = bool(data['device_tracing'])
			if 'event_tracing' in data:
				self._event_tracing = bool(data['event_tracing'])
			if 'job_tracing' in data:
				self._job_tracing = bool(data['job_tracing'])
			if 'component_tracing' in data:
				self._component_tracing = bool(data['component_tracing'])

	def load(self):
		"""
		Diese Method lädt die überschrieben Parameterwerte aus der 
		benutzerspezifischen Konfigurationsdatei.
		""" 
		configfile = self._configfile_path()
		if not os.path.isfile(configfile):
			return
		with open(configfile, 'r', encoding='utf-8') as f:
			configdata = json.loads(f.read())
			self._from_data(configdata)

	def save(self):
		"""
		Speichert die Werte aller Parameter in die benutzerspezifische 
		Konfigurationsdatei.
		"""
		self._write_configfile(self._to_data())

	def __str__(self):
		return \
			'Orbit Setup\n' + \
			'-----------\n' + \
			'Host:              ' + str(self.host) + '\n' + \
			'Port:              ' + str(self.port) + '\n' + \
			'Retry Timer:       ' + str(self.connection_retry_time) + '\n' + \
			'Core Tracing:      ' + str(self.core_tracing) + '\n' + \
			'Device Tracing:    ' + str(self.device_tracing) + '\n' + \
			'Event Tracing:     ' + str(self.event_tracing) + '\n' + \
			'Job Tracing:       ' + str(self.job_tracing) + '\n' + \
			'Component Tracing: ' + str(self.component_tracing)


# script execution
if __name__ == '__main__':
	cc = Configuration()
	print(str(cc))
