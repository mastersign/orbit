#!/usr/bin/python3

# Package orbit.application

from datetime import datetime
from . import setup
from .devices import known_device, get_device_identifier, device_name, device_instance
from tinkerforge.ip_connection import IPConnection, Error

def _trace(text, source):
	print(datetime.now().strftime("[%Y-%m-%d %H-%M-%S] ") + ("%s: %s" % (source, text)))

class Core:

	def __init__(self, config = setup.Configuration()):

		self.started = False
		self.configuration = config
		self.components = {}

		self.device_manager = DeviceManager(self)
		self.blackboard = Blackboard(self)

		self.trace("application core initialized")

	def trace(self, text):
		if self.configuration.core_tracing:
			_trace(text, 'Core')

	def start(self):
		if self.started:
			self.trace("application core allready started")
			return
		self.trace("starting application core")

		self.blackboard.initialize()
		self.started = True
		self.for_each_component(
			lambda c: c.on_core_started())
		self.device_manager.start()

		self.trace("application core started")

	def stop(self):
		if not self.started:
			self.trace("application core allready stopped")
			return
		self.trace("stopping application core")

		self.device_manager.stop()
		self.started = False
		self.for_each_component(
			lambda c: c.on_core_stopped())
			
		self.trace("application core stopped")

	def add_component(self, component):
		# store reference to component
		self.components[component.name] = component

	def for_each_component(self, f):
		for component in self.components.values():
			f(component)


class DeviceManager:

	def __init__(self, core):
		self._core = core
		self.connected = False
		self.devices = {}
		self._device_callbacks = {}

		# initialize IP connection
		self.conn = IPConnection()
		self.conn.set_auto_reconnect(True)
		self.conn.register_callback(IPConnection.CALLBACK_ENUMERATE, self._cb_enumerate)
		self.conn.register_callback(IPConnection.CALLBACK_CONNECTED, self._cb_connected)
		self.conn.register_callback(IPConnection.CALLBACK_DISCONNECTED, self._cb_disconnected)

	def trace(self, text):
		if self._core.configuration.device_tracing:
			_trace(text, 'DeviceManager')

	def start(self):
		if self.conn.get_connection_state() == IPConnection.CONNECTION_STATE_DISCONNECTED:
			host = self._core.configuration.host
			port = self._core.configuration.port
			self.trace("connecting to %s:%d" % (host, port))
			self.conn.connect(host, port)

	def stop(self):
		self._unbind_all_devices()
		if self.conn.get_connection_state() != IPConnection.CONNECTION_STATE_DISCONNECTED:
			self.trace("disconnecting")
			self.conn.disconnect()

	def _cb_enumerate(self, uid, connected_uid, position, hardware_version,
	                 firmware_version, device_identifier, enumeration_type):

		if enumeration_type == IPConnection.ENUMERATION_TYPE_AVAILABLE or \
		   enumeration_type == IPConnection.ENUMERATION_TYPE_CONNECTED:
			# initialize device configuration and bindings
			self.trace("device present [%s] %s" % (uid, device_name(device_identifier)))
			if known_device(device_identifier):
				# bind device and notify components
				self._bind_device(device_identifier, uid)
			else:
				self.trace("could not create a device binding for device identifier " + device_identifier)
		if enumeration_type == IPConnection.ENUMERATION_TYPE_DISCONNECTED:
			# recognize absence of device
			self.trace("device absent [%s]" % uid)
			# unbind device and notify components
			self._unbind_device(uid)

	def _cb_connected(self, reason):
		self.connected = True
		# recognize connection
		if reason == IPConnection.CONNECT_REASON_AUTO_RECONNECT:
			self.trace("connection established (auto reconnect)")
		else:
			self.trace("connection established")
		# notify components
		self._core.for_each_component(
			lambda c: c.on_connected())
		# enumerate devices
		self.conn.enumerate()

	def _cb_disconnected(self, reason):
		self.connected = False
		# recognize lost connection
		if reason == IPConnection.DISCONNECT_REASON_ERROR:
			self.trace("connection lost (error)")
		elif reason == IPConnection.DISCONNECT_REASON_SHUTDOWN:
			self.trace("connection lost (shutdown")
		else:
			self.trace("connection lost")
		# notify components
		self._core.for_each_component(
			lambda c: c.on_disconnected())

	def _bind_device(self, device_identifier, uid):
		self.trace("binding device [%s]" % uid)
		# create binding instance
		device = device_instance(device_identifier, uid, self.conn)
		# add passive identity attribute
		identity = device.get_identity()
		device.identity = identity
		# store reference to binding instance
		self.devices[uid] = device
		# register callbacks
		if uid in self._device_callbacks:
			callbacks = self._device_callbacks[uid]
			for event in callbacks:
				self.trace("binding dispatcher to [%s] (%s)" % (uid, event))
				mcc = callbacks[event]
				device.register_callback(event, mcc)
		# notify components
		self._core.for_each_component(
			lambda c: c.on_bind_device(device))

	def _unbind_device(self, uid):
		if uid in self.devices:
			self.trace("unbinding device [%s]" % uid)
			device = self.devices[uid]
			# notify components
			self._core.for_each_component(
				lambda c: c.on_unbind_device(device))
			# delete reference to binding interface
			del(self.devices[uid])

			# delete reference to multicast callbacks
			if uid in self._device_callbacks:
				del(self._device_callbacks[uid])
		else:
			self.trace("attempt to unbind not bound device [%s]" % uid)

	def _unbind_all_devices(self):
		for uid in list(self.devices.keys()):
			self._unbind_device(uid)

	def add_device_callback(self, uid, event, callback):
		if uid not in self._device_callbacks:
			self._device_callbacks[uid] = {}
		
		callbacks = self._device_callbacks[uid]
		
		if event not in callbacks:
			self.trace("creating dispatcher for [%s] (%s)" % (uid, event))
			mcc = MulticastCallback()
			callbacks[event] = mcc
			if uid in self.devices:
				device = self.devices[uid]
				self.trace("binding dispatcher to [%s] (%s)" % (uid, event))
				device.register_callback(event, mcc)
		
		mcc = callbacks[event]
		self.trace("adding callback to dispatcher for [%s] (%s)" % (uid, event))
		mcc.add_callback(callback)

	def remove_device_callback(self, uid, event, callback):
		if uid in self._device_callbacks:
			callbacks = self._device_callbacks[uid]
			if event in callbacks:
				mcc = callbacks[event]
				self.trace("removing callback from dispatcher for [%s] (%s)" % (uid, event))
				mcc.remove_callback(callback)


class Blackboard:

	def __init__(self, core):
		self._core = core
		self._event_listeners = {}
		self._event_groups = {}
		self._sender_groups = {}

	def trace(self, text):
		if self._core.configuration.event_tracing:
			_trace(text, 'Blackboard')

	def listen(self, event_listener):
		sender = event_listener.sender
		name = event_listener.name
		if sender in self._event_listeners:
			sender_listeners = self._event_listeners[sender]
		else:
			sender_listeners = {}
			self._event_listeners[sender] = sender_listeners
		if name in sender_listeners:
			name_listeners = sender_listeners[name]
		else:
			name_listeners = []
			sender_listeners[name] = name_listeners
		name_listeners.append(event_listener)

	def initialize(self):
		def build_group_lookup(names_by_group):
			groups_by_name = {}
			for group in names_by_group.keys():
				names = names_by_group[group]
				for name in names:
					if name not in groups_by_name:
						groups = []
						groups_by_name[name] = groups
					else:
						groups = groups_by_name[name]
					groups.append(group)
			return groups_by_name

		self.event_group_lookup = build_group_lookup(self._event_groups)
		self.sender_group_lookup = build_group_lookup(self._sender_groups)

	def send(self, sender, name, value):
		if not self._core.started:
			self.trace("DROPPED event before core started (%s, %s)" \
				% (sender, name))
			return

		event = (sender, name, value)

		def send_by_sender(lookup, s):
			if s in lookup:
				listeners_by_name = lookup[s]
				send_by_name(listeners_by_name, name)
				send_by_name(listeners_by_name, None)

			if s and s in self.sender_group_lookup:
				for g in self.sender_group_lookup[s]:
					send_by_sender(lookup, g)

		def send_by_name(lookup, n):
			if n in lookup:
				call_listeners(lookup[n])

			if n and n in self.event_group_lookup:
				for g in self.event_group_lookup[n]:
					send_by_name(lookup, g)

		def call_listeners(listeners):
			for l in listeners:
				self.trace("ROUTE %s, %s => %s (%s, %s)" \
					% (sender, name, l.component, l.sender, l.name))
				l(event)

		send_by_sender(self._event_listeners, sender)
		send_by_sender(self._event_listeners, None)

	def event_group(self, group_name, *names):
		self._event_groups[group_name] = names

	def sender_group(self, group_name, *names):
		self._sender_groups[group_name] = names


class Component:

	def __init__(self, core, name, 
		tracing = None, event_tracing = None):
		self.core = core
		self.name = name
		self._tracing = tracing
		self._event_tracing = event_tracing
		self._device_handles = []
		self.core.add_component(self)

	def trace(self, text):
		if self._tracing != False and \
			(self._tracing or self.core.configuration.component_tracing):
			_trace(text, self.name)

	def event_trace(self, text):
		if self._event_tracing != False and \
			(self._event_tracing or self.core.configuration.event_tracing):
			_trace(text, self.name)

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
		for dh in self._device_handles:
			dh.on_bind_device(device)

	def on_unbind_device(self, device):
		for dh in self._device_handles:
			dh.on_unbind_device(device)

	def add_device_handle(self, device_handle):
		self._device_handles.append(device_handle)
		device_handle.register_component(self)

	def listen(self, event_listener):
		event_listener.component = self.name
		self.core.blackboard.listen(event_listener)

	def send(self, name, value = None):
		self.event_trace("EVENT %s: %s" % (name, str(value)))
		self.core.blackboard.send(self.name, name, value)


class MulticastCallback:

	def __init__(self):
		self._callbacks = []

	def add_callback(self, callback):
		self._callbacks.append(callback)

	def remove_callback(self, callback):
		self._callbacks.remove(callback)

	def __call__(self, *pargs, **nargs):
		for callback in self._callbacks:
			callback(*pargs, **nargs)


class DeviceHandle:

	def __init__(self, name, bind_callback, unbind_callback):
		self.name = name
		self._bind_callback = bind_callback
		self._unbind_callback = unbind_callback
		self.devices = []
		self._callbacks = {}
		self._component = None

	def register_component(self, component):
		self._component = component

	def on_bind_device(self, device):
		uid = device.identity[0]
		self._component.trace("binding device [%s] to handle %s" \
			% (uid, self.name))
		self.devices.append(device)
		dm = self._component.core.device_manager
		for event_code in self._callbacks:
			dm.add_device_callback(
					uid, event_code, self._callbacks[event_code])
		if self._bind_callback:
			self._bind_callback(device)

	def on_unbind_device(self, device):
		uid = device.identity[0]
		if device in self.devices:
			self._component.trace("unbinding device [%s] from handle %s" \
				% (uid, self.name))
			if self._unbind_callback:
				self._unbind_callback(device)
			dm = self._component.core.device_manager
			for event_code in self._callbacks:
				dm.remove_device_callback(
					uid, event_code, self._callbacks[event_code])
			self.devices.remove(device)

	def for_each_device(self, f):
		for d in self.devices:
			try:
				f(d)
			except Error as err:
				if err.value != -8: # connection lost
					print(err.description)

	def register_callback(self, event_code, callback):
		self.unregister_callback(event_code)
		self._callbacks[event_code] = callback
		dm = self._component.core.device_manager
		self.for_each_device(
			lambda device:
				dm.add_device_callback(
					device.identity[0], event_code, callback))

	def unregister_callback(self, event_code):
		if event_code in self._callbacks:
			callback = self._callbacks[event_code]
			dm = self._component.core.device_manager
			self.for_each_device(
				lambda device: 
					dm.remove_device_callback(
						device.identity[0], event_code, callback))
			del(self._callbacks[event_code])


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
		if device.identity[5] != self.device_identifier:
			return
		if self.uid == None:
			if self.auto_fix:
				self.uid = identity[0]
		elif device.identity[0] != self.uid:
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
		if not device.identity[5] == self.device_identifier:
			return
		super().on_bind_device(device)


class EventInfo:

	def __init__(self, sender = None, name = None, predicate = None, transform = None):
		self.sender = sender
		self.name = name
		self.predicate = predicate
		self.transform = transform
		self.component = None

	def create_listener(self, callback):
		return EventListener(callback, 
			sender = self.sender, 
			name = self.name, 
			predicate = self.predicate,
			transform = self.transform)

	def __str__(self):
		return "EventInfo(sender = %s, name = %s, predicate: %s, transform: %s, component = %s)" \
			% (self.sender, self.name,
			   self.transform != None, self.predicate != None, 
			   self.component)


class EventListener:

	def __init__(self, callback, sender = None, name = None, predicate = None, transform = None, component = None):
		self.callback = callback
		self.sender = sender
		self.name = name
		self.predicate = predicate
		self.transform = transform
		self.component = component

	def __call__(self, event):
		if self.predicate == None or self.predicate(event):
			self.callback(event[0], event[1], 
				self.transform(event[2]) if self.transform else event[2])

	def for_sender(callback, sender):
		return EventListener(callback, sender = sender)

	def for_name(callback, name):
		return EventListener(callback, name = name)

	def for_sender_and_name(callback, sender, name):
		return EventListener(callback, sender = sender, name = name)

	def __str__(self):
		return "EventListener(sender = %s, name = %s, predicate: %s, transform: %s, component = %s)" \
			% (self.sender, self.name,
			   self.transform != None, self.predicate != None, 
			   self.component)