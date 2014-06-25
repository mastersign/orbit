# coding=utf-8

# Package orbit.components.remoteswitch

"""
Dieses Modul enthält Komponenten für die Steuerung mit einem
Remote-Switch-Bricklet.

Enthalten sind die folgenden Komponenten:

- :py:class:`RemoteSwitchComponent`
"""

from .. import Component
from ..devices import SingleDeviceHandle
from tinkerforge.bricklet_remote_switch import BrickletRemoteSwitch

RS = BrickletRemoteSwitch

class RemoteSwitchComponent(Component):
	"""
	Diese Komponente steuert eine Funksteckdose mit Hilfe
	des Remote-Switch-Bricklets	wenn Nachrichten über das Nachrichtensystem
	empfangen werden.
	
	**Parameter**

	``name``
		Der Name der Komponente.
	``group``
		Die Gruppennummer der Funksteckdose.
	``socket``
		Die ID der Funksteckdose.
	``on_slot``
		Ein Empfangsmuster welches die Funksteckdose einschalten soll.
	``on_off``
		Ein Emfpangsmuster welches die Funksteckdose ausschalten soll.
	``typ`` (*optional*)
		Der Typ der Funksteckdose.
		Mögliche Werte sind ``'A'``, ``'B'`` oder ``'C'``.
		Der Standardwert ist ``'A'``.
		Mehr Informationen zu Steckdosentypen sind in der `Remote-Switch-Dokumentation`_
		zu finden.
	``switch_uid`` (*optional*)
		Die UID des Remote-Switch-Bricklets oder ``None`` für den ersten
		der gefunden wird.
		Der Standardwert ist ``None``.
	
	**Beschreibung**

	Wenn eine Nachricht mit dem Empfangsmuster von ``on_slot`` eintrifft,
	wird der Einschaltbefehl an die angegebene Steckdose gesendet.
	Wenn eine Nachricht mit dem Empfangsmuster von ``off_slot`` eintrifft,
	wird der Ausschaltbefehl an die angegebene Steckdose gesendet.
	
	*Siehe auch:*
	`Remote-Switch-Dokumentation`_

	.. _Remote-Switch-Dokumentation: http://www.tinkerforge.com/de/doc/Hardware/Bricklets/Remote_Switch.html
	"""

	def __init__(self, name, 
		group, socket, on_slot, off_slot, typ = 'A', switch_uid = None, 
		**nargs):
	
		super().__init__(name, **nargs)

		self._group = group
		self._socket = socket
		self._typ = typ
		
		self.add_listener(on_slot.listener(self._process_on_event))
		self.add_listener(off_slot.listener(self._process_off_event))

		self._switch_handle = SingleDeviceHandle(
			'switch', RS.DEVICE_IDENTIFIER, uid = switch_uid)
		self.add_device_handle(self._switch_handle)

	def _process_on_event(self, *args):
		self._switch_handle.for_each_device(
			lambda device: self._switch(device, RS.SWITCH_TO_ON))

	def _process_off_event(self, *args):
		self._switch_handle.for_each_device(
			lambda device: self._switch(device, RS.SWITCH_TO_OFF))

	def _switch(self, device, state):
		if self._typ == 'A':
			device.switch_socket_a(self._group, self._socket, state)
		elif self._typ == 'B':
			device.switch_socket_b(self._group, self._socket, state)
		elif self._typ == 'C':
			device.switch_socket_c(self._group, self._socket, state)
		else:
			self.trace("invalid remote switch typ: '%s'" % self._typ)
