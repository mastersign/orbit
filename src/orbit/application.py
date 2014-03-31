#!/usr/bin/python3

# Package orbit.application

from datetime import datetime
from . import setup
from .devices import known_device, get_device_identifier, device_name, device_instance
from tinkerforge.ip_connection import IPConnection

class Core:

	def __init__(self, conf = setup.Configuration(), tracing = False):

		self.started = False
		self.connected = False
		self.conf = conf
		self.tracing = tracing
		self.devices = {}
		self.components = {}
		self.event_listeners = {}
		self.event_group_lookup = {}

		# initialize IP connection
		self.conn = IPConnection()
		self.conn.set_auto_reconnect(True)
		self.conn.register_callback(IPConnection.CALLBACK_ENUMERATE, self.cb_enumerate)
		self.conn.register_callback(IPConnection.CALLBACK_CONNECTED, self.cb_connected)
		self.conn.register_callback(IPConnection.CALLBACK_DISCONNECTED, self.cb_disconnected)

		self.trace("application core initialized")

	def trace(self, text):
		if self.tracing:
			print(datetime.now().strftime("[%Y-%m-%d %H-%M-%S] ") + "Core: " + text)

	def start(self):
		if self.started:
			self.trace("application core allready started")
			return
		self.trace("starting application core")
		self.started = True
		for c in self.components.values():
			c.on_core_started()
		if self.conn.get_connection_state() == IPConnection.CONNECTION_STATE_DISCONNECTED:
			host = self.conf.host
			port = self.conf.port
			self.trace("connecting to " + host + ":" + str(port))
			self.conn.connect(host, port)
		self.trace("application core started")

	def stop(self):
		if not self.started:
			self.trace("application core allready stopped")
			return
		self.trace("stopping application core")
		self.unbind_all_devices()
		if self.conn.get_connection_state() != IPConnection.CONNECTION_STATE_DISCONNECTED:
			self.trace("disconnecting")
			self.conn.disconnect()
		self.started = False
		for c in self.components.values():
			c.on_core_stopped()
		self.trace("application core stopped")

	def cb_enumerate(self, uid, connected_uid, position, hardware_version,
	                 firmware_version, device_identifier, enumeration_type):

		if enumeration_type == IPConnection.ENUMERATION_TYPE_AVAILABLE or \
		   enumeration_type == IPConnection.ENUMERATION_TYPE_CONNECTED:
			# initialize device configuration and bindings
			self.trace("device present [" + uid + "] " + device_name(device_identifier))
			if known_device(device_identifier):
				# bind device and notify components
				self.bind_device(device_identifier, uid)
			else:
				self.trace("could not create a device binding for device identifier " + device_identifier)
		if enumeration_type == IPConnection.ENUMERATION_TYPE_DISCONNECTED:
			# recognize absence of device
			self.trace("device absent [" + uid + "]")
			# unbind device and notify components
			self.unbind_device(uid)

	def cb_connected(self, reason):
		self.connected = True
		# recognize connection
		if reason == IPConnection.CONNECT_REASON_AUTO_RECONNECT:
			self.trace("connection established (auto reconnect)")
		else:
			self.trace("connection established")
		# notify components
		for c in self.components.values():
			c.on_connected()
		# enumerate devices
		self.conn.enumerate()

	def cb_disconnected(self, reason):
		self.connected = False
		# recognize lost connection
		if reason == IPConnection.DISCONNECT_REASON_ERROR:
			self.trace("connection lost (error)")
		elif reason == IPConnection.DISCONNECT_REASON_SHUTDOWN:
			self.trace("connection lost (shutdown")
		else:
			self.trace("connection lost")
		# notify components
		for c in self.components.values():
			c.on_disconnected()

	def bind_device(self, device_identifier, uid):
		self.trace("binding device [" + uid + "]")
		# create binding instance
		device = device_instance(device_identifier, uid, self.conn)
		# store reference to binding instance
		self.devices[uid] = device
		# notify components
		for c in self.components.values():
			c.on_bind_device(device)

	def unbind_device(self, uid):
		if uid in self.devices:
			self.trace("unbinding device [" + uid + "]")
			device = self.devices[uid]
			# notify components
			for c in self.components.values():
				c.on_unbind_device(device)
			# delete reference to binding interface
			del(self.devices[uid])
		else:
			self.trace("attempt to unbind not bound device [" + uid + "]")

	def unbind_all_devices(self):
		for uid in list(self.devices.keys()):
			self.unbind_device(uid)

	def add_component(self, component):
		# store reference to component
		self.components[component.name] = component

	def listen(self, event_listener):
		sender = event_listener.sender
		name = event_listener.name
		if sender in self.event_listeners:
			sender_listeners = self.event_listeners[sender]
		else:
			sender_listeners = {}
			self.event_listeners[sender] = sender_listeners
		if name in sender_listeners:
			name_listeners = sender_listeners[name]
		else:
			name_listeners = []
			sender_listeners[name] = name_listeners
		name_listeners.append(event_listener)

	def send(self, sender, name, value):
		event = (sender, name, value)

		def send_by_sender(lookup, s):
			if s in lookup:
				listeners_by_name = lookup[s]
				send_by_name(listeners_by_name, name)
				send_by_name(listeners_by_name, None)

		def send_by_name(lookup, n):
			if n in lookup:
				call_listeners(lookup[n])

			if n and n in self.event_group_lookup:
				for g in self.event_group_lookup[n]:
					send_by_name(lookup, g)

		def call_listeners(listeners):
			for l in listeners:
				self.trace("EVENT ROUTE (%s, %s) => (%s, %s)" \
					% (sender, name, l.sender, l.name))
				l(event)

		send_by_sender(self.event_listeners, sender)
		send_by_sender(self.event_listeners, None)

	def event_group(self, group_name, *names):
		for name in names:
			if name not in self.event_group_lookup:
				groups = []
				self.event_group_lookup[name] = groups
			else:
				groups = self.event_group_lookup[name]
			groups.append(group_name)


class Component:

	def __init__(self, core, name, tracing = False):
		self.name = name
		self.tracing = tracing
		self.device_handles = []
		self.core = core
		self.core.add_component(self)

	def trace(self, text):
		if self.tracing or self.core.tracing:
			print("%s %s: %s" % (datetime.now().strftime("[%Y-%m-%d %H-%M-%S]"), self.name, text))

	def on_core_started(self):
		# can be overriden in sub classes
		pass

	def on_core_stopped(self):
		# can be overriden in sub classes
		pass

	def on_connected(self):
		# can be overridden in sub classes
		pass

	def on_disconnected(self):
		# can be overridden in sub classes
		pass

	def on_bind_device(self, device):
		for dh in self.device_handles:
			dh.on_bind_device(device)

	def on_unbind_device(self, device):
		for dh in self.device_handles:
			dh.on_unbind_device(device)

	def add_device_handle(self, device_handle):
		self.device_handles.append(device_handle)
		device_handle.register_component(self)

	def listen(self, event_listener):
		self.core.listen(event_listener)

	def send(self, name, value):
		self.trace("EVENT %s: %s" % (name, str(value)))
		self.core.send(self.name, name, value)


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
		self.component.trace("binding device [%s] to handle %s" \
			% (device.get_identity()[0], self.name))
		self.devices.append(device)
		if self.bind_callback:
			self.bind_callback(device)

	def on_unbind_device(self, device):
		if device in self.devices:
			self.component.trace("unbinding device [%s] from handle %s" \
				% (device.get_identity()[0], self.name))
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


class EventInfo:

	def __init__(self, sender = None, name = None, predicate = None):
		self.sender = sender
		self.name = name
		self.predicate = predicate

	def create_listener(self, callback):
		return EventListener(callback, 
			sender = self.sender, 
			name = self.name, 
			predicate = self.predicate)

	def __str__(self):
		return "EventInfo(sender = %s, name = %s, predicate: %s)" \
			% (self.sender, self.name, self.predicate != None)


class EventListener:

	def __init__(self, callback, sender = None, name = None, predicate = None):
		self.callback = callback
		self.sender = sender
		self.name = name
		self.predicate = predicate

	def __call__(self, event):
		if self.predicate == None or self.predicate(event):
			self.callback(*event)

	def for_sender(callback, sender):
		return EventListener(callback, sender = sender)

	def for_name(callback, name):
		return EventListener(callback, name = name)

	def for_sender_and_name(callback, sender, name):
		return EventListener(callback, sender = sender, name = name)

	def __str__(self):
		return "EventListener(sender = %s, name = %s, predicate: %s)" \
			% (self.sender, self.name, self.predicate != None)