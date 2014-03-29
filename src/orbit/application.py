#!/usr/bin/python3

# Package orbit.application

from datetime import datetime
from . import setup
from .devices import known_device, get_device_identifier, device_name, device_instance
from tinkerforge.ip_connection import IPConnection

class Core:

	def __init__(self, conf = setup.Configuration(), debug = False):

		self.started = False
		self.connected = False
		self.conf = conf
		self.debug = debug
		self.devices = {}
		self.components = {}

		# initialize IP connection
		self.conn = IPConnection()
		self.conn.set_auto_reconnect(True)
		self.conn.register_callback(IPConnection.CALLBACK_ENUMERATE, self.cb_enumerate)
		self.conn.register_callback(IPConnection.CALLBACK_CONNECTED, self.cb_connected)
		self.conn.register_callback(IPConnection.CALLBACK_DISCONNECTED, self.cb_disconnected)

		self.msg("application core initialized")

	def msg(self, text):
		if self.debug:
			print(datetime.now().strftime("[%Y-%m-%d %H-%M-%S] ") + "Core: " + text)

	def start(self):
		if self.started:
			self.msg("application core allready started")
			return
		self.msg("starting application core")
		self.started = True
		if self.conn.get_connection_state() == IPConnection.CONNECTION_STATE_DISCONNECTED:
			host = self.conf.host
			port = self.conf.port
			self.msg("connecting to " + host + ":" + str(port))
			self.conn.connect(host, port)
		self.msg("application core started")

	def stop(self):
		if not self.started:
			self.msg("application core allready stopped")
			return
		self.msg("stopping application core")
		self.started = False
		self.unbind_all_devices()
		if self.conn.get_connection_state() != IPConnection.CONNECTION_STATE_DISCONNECTED:
			self.msg("disconnecting")
			self.conn.disconnect()
		self.msg("application core stopped")

	def cb_enumerate(self, uid, connected_uid, position, hardware_version,
	                 firmware_version, device_identifier, enumeration_type):

		if enumeration_type == IPConnection.ENUMERATION_TYPE_AVAILABLE or \
		   enumeration_type == IPConnection.ENUMERATION_TYPE_CONNECTED:
			# initialize device configuration and bindings
			self.msg("device present [" + uid + "] " + device_name(device_identifier))
			if known_device(device_identifier):
				# bind device and notify components
				self.bind_device(device_identifier, uid)
			else:
				self.msg("could not create a device binding for device identifier " + device_identifier)
		if enumeration_type == IPConnection.ENUMERATION_TYPE_DISCONNECTED:
			# recognize absence of device
			self.msg("device absent [" + uid + "]")
			# unbind device and notify components
			self.unbind_device(uid)

	def cb_connected(self, reason):
		self.connected = True
		# recognize connection
		if reason == IPConnection.CONNECT_REASON_AUTO_RECONNECT:
			self.msg("connection established (auto reconnect)")
		else:
			self.msg("connection established")
		# notify components
		self.for_all_components(lambda c: c.on_connected())
		# enumerate devices
		self.conn.enumerate()

	def cb_disconnected(self, reason):
		self.connected = False
		# recognize lost connection
		if reason == IPConnection.DISCONNECT_REASON_ERROR:
			self.msg("connection lost (error)")
		elif reason == IPConnection.DISCONNECT_REASON_SHUTDOWN:
			self.msg("connection lost (shutdown")
		else:
			self.msg("connection lost")
		# notify components
		self.for_all_components(lambda c: c.on_disconnected())

	def bind_device(self, device_identifier, uid):
		self.msg("binding device [" + uid + "]")
		# create binding instance
		device = device_instance(device_identifier, uid, self.conn)
		# store reference to binding instance
		self.devices[uid] = device
		# notify components
		self.for_all_components(lambda c: c.on_bind_device(device))

	def unbind_device(self, uid):
		if uid in self.devices:
			self.msg("unbinding device [" + uid + "]")
			device = self.devices[uid]
			# notify components
			self.for_all_components(lambda c: c.on_unbind_device(device))
			# delete reference to binding interface
			del(self.devices[uid])
		else:
			self.msg("attempt to unbind not bound device [" + uid + "]")

	def unbind_all_devices(self):
		for uid in list(self.devices.keys()):
			self.unbind_device(uid)

	def add_component(self, component):
		# store reference to component
		self.components[component.name] = component
		# submit reference to the core
		component.register_core(self)

	def add_components(self, *components):
		for c in components:
			self.add_component(c)

	def for_all_components(self, f):
		for c in self.components.values():
			f(c)


class Component:

	def __init__(self, name, debug = False):
		self.name = name
		self.debug = debug
		self.device_handles = []

	def msg(self, text):
		if self.debug or (self.core and self.core.debug):
			print(datetime.now().strftime("[%Y-%m-%d %H-%M-%S] ") + self.name + ": " + text)

	def register_core(self, core):
		self.core = core
		self.msg("component registered at application core")

	def add_device_handle(self, device_handle):
		self.device_handles.append(device_handle)
		device_handle.register_component(self)

	def for_all_device_handles(self, f):
		for dh in self.device_handles:
			f(dh)

	def on_connected(self):
		# can be overridden in sub classes
		pass

	def on_disconnected(self):
		# can be overridden in sub classes
		pass

	def on_bind_device(self, device):
		self.for_all_device_handles(lambda dh: dh.on_bind_device(device))		

	def on_unbind_device(self, device):
		self.for_all_device_handles(lambda dh: dh.on_unbind_device(device))


class DeviceHandle:

	def __init__(self, name, bind_callback, unbind_callback):
		self.name = name
		self.bind_callback = bind_callback
		self.unbind_callback = unbind_callback
		self.devices = []

	def register_component(self, component):
		self.component = component

	def for_all_devices(self, f):
		for d in self.devices:
			f(d)

	def on_bind_device(self, device):
		self.component.msg("binding device [%s] to handle %s" % (device.get_identity()[0], self.name))
		self.devices.append(device)
		if self.bind_callback:
			self.bind_callback(device)

	def on_unbind_device(self, device):
		if device in self.devices:
			self.component.msg("unbinding device [%s] from handle %s" % (device.get_identity()[0], self.name))
			if self.unbind_callback:
				self.unbind_callback(device)
			self.devices.remove(device)


class SingleDeviceHandle(DeviceHandle):

	def __init__(self, name, device_name_or_id, bind_callback = None, unbind_callback = None, uid = None, auto_fix = False):
		super().__init__(name, bind_callback, unbind_callback)
		self.device_identifier = get_device_identifier(device_name_or_id)
		self.uid = uid
		self.auto_fix = auto_fix
		self.device = None

	def on_bind_device(self, device):
		if len(self.devices) > 0:
			return
		identity = device.get_identity()
		if identity[5] != self.device_identifier:
			return
		if self.uid == None:
			if self.auto_fix:
				self.uid = identity[0]
		elif identity[0] != self.uid:
			return
		self.device = device
		super().on_bind_device(device)

	def on_unbind_device(self, device):
		super().on_unbind_device(device)
		if self.device == device:
			self.device = None


class MultiDeviceHandle(DeviceHandle):

	def __init__(self, name, device_name_or_id, bind_callback = None, unbind_callback = None):
		super().__init__(name, bind_callback, unbind_callback)
		self.device_identifier = get_device_identifier(device_name_or_id)

	def on_bind_device(self, device):
		identity = device.get_identity()
		if not identity[5] == self.device_identifier:
			return
		super().on_bind_device(device)
