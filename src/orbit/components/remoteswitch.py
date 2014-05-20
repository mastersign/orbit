# Package orbit.components.remoteswitch

from ..application import Component, SingleDeviceHandle
from tinkerforge.bricklet_remote_switch import BrickletRemoteSwitch

RS = BrickletRemoteSwitch

class RemoteSwitchComponent(Component):

	def __init__(self, name, group, socket, on_slot, off_slot, typ = 'A', switch_uid = None, **nargs):
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
