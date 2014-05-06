# Package orbit.application

from datetime import datetime
from . import setup
from .devices import known_device, get_device_identifier, device_name, device_instance
from tinkerforge.ip_connection import IPConnection, Error

def _trace(text, source):
	print(datetime.now().strftime("[%Y-%m-%d %H-%M-%S] ") + ("%s: %s" % (source, text)))

class Core:

	def __init__(self, config = setup.Configuration()):
		self._started = False
		self._configuration = config
		
		self._device_manager = DeviceManager(self)
		self._blackboard = Blackboard(self)

		self._jobs = {}
		self._default_application = None
		self._current_application = None

		self.trace("application core initialized")

	def trace(self, text):
		if self._configuration.core_tracing:
			_trace(text, 'Core')

	@property
	def started(self):
		return self._started

	@property
	def configuration(self):
		return self._configuration

	@property
	def device_manager(self):
	    return self._device_manager

	@property
	def blackboard(self):
		return self._blackboard

	@property
	def jobs(self):
		return self._jobs

	@property
	def default_application(self):
		return self._default_application
	@default_application.setter
	def default_application(self, application):
		self._default_application = application

	def start(self):
		if self._started:
			self.trace("application core allready started")
			return
		self.trace("starting ...")

		self._blackboard.initialize()
		self._started = True
		self._device_manager.start()
		self.for_each_job(
			lambda j: j.on_core_started())

		self.trace("... started")

		def activator(job):
			if job.background:
				job.active = True
		self.for_each_job(activator)

	def stop(self):
		if not self._started:
			self.trace("application core allready stopped")
			return

		def deactivator(job):
			job.active = False
		self.for_each_active_job(deactivator)

		self.trace("stopping ...")

		self._device_manager.stop()
		self._started = False
		self.for_each_job(
			lambda j: j.on_core_stopped())

		self.trace("... stopped")

	def install(self, job):
		if job.core:
			raise AttributeError("the given job is already associated with a core")
		if job.name in self._jobs:
			self.uninstall(self._jobs[job.name])
		self._jobs[job.name] = job
		job.on_install(self)
		self.trace("installed job '%s'" % job.name)
		if self._started and job.background:
			job.active = True

	def uninstall(self, job):
		if job.name not in self._jobs:
			raise AttributeError("the given job is not associated with this core")
		if job.active:
			job.active = False
		job.on_uninstall()
		del(self._jobs[job.name])
		self.trace("uninstalled job '%s'" % job.name)

	def for_each_job(self, f):
		for job in self._jobs.values():
			f(job)

	def for_each_active_job(self, f):
		for job in self._jobs.values():
			if job.active:
				f(job)

	def activate(self, application):
		# if only the name is given: lookup job name
		if type(application) is str:
			if application in self._jobs:
				application = self._jobs[application]
			else:
				raise KeyError("job name not found")
		# set job as current application
		self.trace("activating application '%s' ..." % application.name)
		if self._current_application:
			self._current_application.active = False
		self._current_application = application
		if self._current_application:
			self._current_application.active = True
		self.trace("... activated application '%s'" % application.name)


class DeviceManager:

	def __init__(self, core):
		self._core = core
		self._connected = False
		self._devices = {}
		self._device_handles = []
		self._device_callbacks = {}
		self._device_initializers = {}
		self._device_finalizers = {}

		# initialize IP connection
		self._conn = IPConnection()
		self._conn.set_auto_reconnect(True)
		self._conn.register_callback(IPConnection.CALLBACK_ENUMERATE, self._cb_enumerate)
		self._conn.register_callback(IPConnection.CALLBACK_CONNECTED, self._cb_connected)
		self._conn.register_callback(IPConnection.CALLBACK_DISCONNECTED, self._cb_disconnected)

	def trace(self, text):
		if self._core.configuration.device_tracing:
			_trace(text, 'DeviceManager')

	@property
	def devices(self):
		return self._devices

	def start(self):
		if self._conn.get_connection_state() == IPConnection.CONNECTION_STATE_DISCONNECTED:
			host = self._core.configuration.host
			port = self._core.configuration.port
			self.trace("connecting to %s:%d" % (host, port))
			self._conn.connect(host, port)

	def stop(self):
		self._finalize_and_unbind_devices()
		if self._conn.get_connection_state() != IPConnection.CONNECTION_STATE_DISCONNECTED:
			self.trace("disconnecting")
			self._conn.disconnect()

	def _cb_enumerate(self, uid, connected_uid, position, hardware_version,
	                 firmware_version, device_identifier, enumeration_type):

		if enumeration_type == IPConnection.ENUMERATION_TYPE_AVAILABLE or \
		   enumeration_type == IPConnection.ENUMERATION_TYPE_CONNECTED:
			# initialize device configuration and bindings
			self.trace("device present '%s' [%s]" % (device_name(device_identifier), uid))
			if known_device(device_identifier):
				# bind device and notify components
				self._bind_device(device_identifier, uid)
			else:
				self.trace("could not create a device binding for device identifier " + device_identifier)
		if enumeration_type == IPConnection.ENUMERATION_TYPE_DISCONNECTED:
			# recognize absence of device
			self.trace("device absent '%s' [%s]" % (device_name(device_identifier), uid))
			# unbind device and notify components
			self._unbind_device(uid)

	def _cb_connected(self, reason):
		self._connected = True
		# recognize connection
		if reason == IPConnection.CONNECT_REASON_AUTO_RECONNECT:
			self.trace("connection established (auto reconnect)")
		else:
			self.trace("connection established")
		# enumerate devices
		self._conn.enumerate()

	def _cb_disconnected(self, reason):
		self._connected = False
		# recognize lost connection
		if reason == IPConnection.DISCONNECT_REASON_ERROR:
			self.trace("connection lost (error)")
		elif reason == IPConnection.DISCONNECT_REASON_SHUTDOWN:
			self.trace("connection lost (shutdown")
		else:
			self.trace("connection lost")

	def _bind_device(self, device_identifier, uid):
		self.trace("binding '%s' [%s]" % 
			(device_name(device_identifier), uid))
		# create binding instance
		device = device_instance(device_identifier, uid, self._conn)
		# add passive identity attribute
		identity = device.get_identity()
		device.identity = identity
		# initialize device
		self._initialize_device(device)
		# store reference to binding instance
		self.devices[uid] = device
		# register callbacks
		if uid in self._device_callbacks:
			callbacks = self._device_callbacks[uid]
			for event in callbacks:
				self.trace("binding dispatcher to '%s' [%s] (%s)" % 
					(device_name(device_identifier), uid, event))
				mcc = callbacks[event]
				device.register_callback(event, mcc)
		# notify device handles
		for device_handle in self._device_handles:
			device_handle.on_bind_device(device)

	def _unbind_device(self, uid):
		if uid in self._devices:
			device = self._devices[uid]
			self.trace("unbinding '%s' [%s]" % 
				(device_name(device.identity[5]), uid))
			# notify device handles
			for device_handle in self._device_handles:
				device_handle.on_unbind_device(device)
			# delete reference to binding interface
			del(self._devices[uid])

			# delete reference to multicast callbacks
			if uid in self._device_callbacks:
				del(self._device_callbacks[uid])
		else:
			self.trace("attempt to unbind not bound device [%s]" % uid)

	def _finalize_and_unbind_devices(self):
		for uid in list(self._devices.keys()):
			self._finalize_device(self._devices[uid])
			self._unbind_device(uid)

	def add_device_initializer(self, device_identifier, initializer):
		if device_identifier not in self._device_initializers:
			self._device_initializers[device_identifier] = []
		self._device_initializers[device_identifier].append(initializer)
		self.trace("added initializer for '%s'" % 
			(device_name(device_identifier)))

	def _initialize_device(self, device):
		device_identifier = device.identity[5]
		if device_identifier in self._device_initializers:
			self.trace("initializing '%s' [%s]" %
				(device_name(device.identity[5]), device.identity[0]))
			for initializer in self._device_initializers[device_identifier]:
				try:
					initializer(device)
				except Error as err:
					if err.value != -8: # connection lost
						print("Error during initialization of : %s" % err.description)
				except Exception as exc:
					print("Exception caught during device initialization:\n%s" % exc)

	def add_device_finalizer(self, device_identifier, finalizer):
		if device_identifier not in self._device_finalizers:
			self._device_finalizers[device_identifier] = []
		self._device_finalizers[device_identifier].append(finalizer)
		self.trace("added finalizer for '%s'" % 
			device_name(device_identifier))

	def _finalize_device(self, device):
		device_identifier = device.identity[5]
		if device_identifier in self._device_finalizers:
			self.trace("finalizing '%s' [%s]" %
				(device_name(device.identity[5]), device.identity[0]))
			for finalizer in self._device_finalizers[device_identifier]:
				try:
					finalizer(device)
				except Error as err:
					if err.value != -8: # connection lost
						print("Error during device finalization: %s" % err.description)
				except Exception as exc:
					print("Exception caught during device finalization:\n%s" % exc)

	def add_handle(self, device_handle):
		if device_handle in self._device_handles:
			return
		self._device_handles.append(device_handle)
		device_handle.on_add_handle(self)
		for device in self._devices.values():
			device_handle.on_bind_device(device)

	def remove_handle(self, device_handle):
		if device_handle not in self._device_handles:
			return
		for device in self._devices.values():
			device_handle.on_unbind_device(device)
		device_handle.on_remove_handle()
		self._device_handles.remove(device_handle)

	def add_device_callback(self, uid, event, callback):
		if uid not in self._device_callbacks:
			self._device_callbacks[uid] = {}
		
		callbacks = self._device_callbacks[uid]
		
		if event not in callbacks:
			self.trace("creating dispatcher for [%s] (%s)" % (uid, event))
			mcc = MulticastCallback()
			callbacks[event] = mcc
			if uid in self._devices:
				device = self._devices[uid]
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

	def add_listener(self, event_listener):
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

	def remove_listener(self, event_listener):
		sender = event_listener.sender
		name = event_listener.name
		if sender in self._event_listeners:
			sender_listeners = self._event_listeners[sender]
			if name in sender_listeners:
				name_listeners = sender_listeners[name]
				if event_listener in name_listeners:
					name_listeners.remove(event_listener)
				if len(name_listeners) == 0:
					del(sender_listeners[name])
			if len(self._event_listeners) == 0:
				del(self._event_listeners[sender])

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


class Job:

	def __init__(self, name, background):
		self._name = name
		self._core = None
		self._background = background
		self._components = {}
		self._active = False
		self._tracing = None

	@property
	def tracing(self):
	    return self._tracing
	@tracing.setter
	def tracing(self, value):
	    self._tracing = value
	
	def trace(self, text):
		if self._tracing == True or \
			(self._tracing != False and \
			 self._core and \
			 self._core.configuration.job_tracing):

			if self._background:
				_trace(text, "Service " + self._name)
			else:
				_trace(text, "App " + self._name)

	@property
	def name(self):
		return self._name

	@property
	def core(self):
	    return self._core

	def on_install(self, core):
		if self._core:
			raise AttributeError("the job is already associated with a core")
		self._core = core

	def on_uninstall(self):
		self._core = None

	@property
	def configuration(self):
		if self._core:
			return self._core.configuration
		else:
			return None

	@property
	def background(self):
	    return self._background

	@property
	def active(self):
		return self._active
	@active.setter
	def active(self, value):
		if self._active == value:
			return
		if self._core == None:
			raise AttributeError("the job is not installed in any core")
		if value and not self._core.started:
			raise AttributeError("the job can not be activated while the core is not started")
		self._active = value
		if self._active:
			self.trace("activating ...")
			self.on_activated()
			self.trace("... activated")
		else:
			self.trace("deactivating ...")
			self.on_deactivated()
			self.trace("... deactivated")

	def on_activated(self):
		def enabler(component):
			component.enabled = True
		self.for_each_component(enabler)
		self.for_each_component(lambda c: c.on_job_activated())

	def on_deactivated(self):
		def disabler(component):
			component.enabled = False
		self.for_each_component(disabler)
		self.for_each_component(lambda c: c.on_job_deactivated())

	@property
	def components(self):
		return self._components

	def add_component(self, component):
		if component.name in self._components:
			self.remove_component(self._components[component.name])
		self._components[component.name] = component
		component.on_add_component(self)
		self.trace("added component %s" % component.name)
		if self._active:
			component.enabled = True

	def remove_component(self, component):
		if component.name not in self._components:
			raise AttributeError("the given component is not associated with this job")
		if component.enabled:
			component.enabled = False
			component.on_remove_component()
		del(self._components[component.name])
		self.trace("removed component %s" % component.name)

	def for_each_component(self, f):
		for component in self._components.values():
			f(component)

	def on_core_started(self):
		self.for_each_component(
			lambda c: c.on_core_started())

	def on_core_stopped(self):
		self.for_each_component(
			lambda c: c.on_core_stopped())


class App(Job):

	def __init__(self, name):
		super().__init__(name, False)
		self._triggers = []

	def add_trigger(self, event_info):
		listener = event_info.create_listener(self.on_trigger)
		self._triggers.append(listener)

	def on_install(self, core):
		super().on_install(core)
		for trigger in self._triggers:
			self._core.blackboard.add_listener(trigger)

	def on_uninstall(self):
		for trigger in self._triggers:
			self._core.blackboard.remove_listener(trigger)
		super().on_uninstall()

	def on_trigger(self, sender, name, value):
		self.trace("activating app %s, caused by trigger" % self.name)
		self._core.activate(self)

class Service(Job):

	def __init__(self, name):
		super().__init__(name, True)


class Component:

	def __init__(self, name):
		self._job = None
		self._name = name
		self._enabled = False
		self._tracing = None
		self._event_tracing = None
		self._device_handles = []
		self._event_listeners = []

	@property
	def tracing(self):
		return self._tracing
	@tracing.setter
	def tracing(self, enabled):
		self._tracing = enabled

	def trace(self, text):
		if self._tracing == True or \
			(self._tracing != False and \
			 self._job and \
			 self._job._core.configuration.component_tracing):

			_trace(text, "Component %s %s" % 
				(self._job.name if self._job else "NO_JOB", self._name))

	@property
	def event_tracing(self):
		return self._event_tracing
	@event_tracing.setter
	def event_tracing(self, enabled):
		self._event_tracing = enabled

	def event_trace(self, name, value):
		if self._event_tracing == True or \
			(self._event_tracing != False and \
			 self._job and \
			 self._job._core.configuration.event_tracing):

			_trace("EVENT %s: %s" % (name, str(value)), "Component %s %s" % 
				(self._job.name if self._job else "NO_JOB", self._name))

	@property
	def name(self):
		return self._name

	@property
	def job(self):
		return self._job

	def on_add_component(self, job):
		if self._job:
			raise AttributeError("the component is already associated with a job")
		self._job = job

	def on_remove_component(self):
		self._job = None

	@property
	def enabled(self):
		return self._enabled
	@enabled.setter
	def enabled(self, value):
		if self._enabled == value:
			return
		if self._job == None:
			raise AttributeError("the component is not associated with any job")
		if value and not self._job.active:
			raise AttributeError("the component can not be enabled while the job is not active")
		self._enabled = value
		if self._enabled:
			self.on_enabled()
			self.trace("enabling ...")
			for event_listener in self._event_listeners:
				self._job._core.blackboard.add_listener(event_listener)
			for device_handle in self._device_handles:
				self._job._core.device_manager.add_handle(device_handle)
			self.trace("... enabled")
		else:
			self.trace("disabling ...")
			for event_listener in self._event_listeners:
				self._job._core.blackboard.remove_listener(event_listener)
			for device_handle in self._device_handles:
				self._job._core.device_manager.remove_handle(device_handle)
			self.on_disabled()
			self.trace("... disabled")

	def on_core_started(self):
		# can be overriden in sub classes
		pass

	def on_core_stopped(self):
		# can be overriden in sub classes
		pass

	def on_job_activated(self):
		# can be overriden in sub classes
		pass

	def on_job_deactivated(self):
		# can be overriden in sub classes
		pass

	def on_enabled(self):
		# can be overriden in sub classes
		pass

	def on_disabled(self):
		# can be overriden in sub classes
		pass

	def add_device_handle(self, device_handle):
		if device_handle in self._device_handles:
			return
		self._device_handles.append(device_handle)
		if self._enabled:
			self._job._core.device_manager.add_handle(device_handle)

	def remove_device_handle(self, device_handle):
		if device_handle not in self._device_handles:
			return
		if self._enabled:
			self._job._core.device_manager.remove_handle(device_handle)
		device_handle.on_remove_device_handle()
		self._device_handles.remove(device_handle)

	def add_event_listener(self, event_listener):
		if event_listener in self._event_listeners:
			return
		event_listener.component = self.name
		self._event_listeners.append(event_listener)
		if self._enabled:
			self._job._core.blackboard.add_listener(event_listener)

	def remove_event_listener(self, event_listener):
		if event_listener not in self._event_listeners:
			return
		if self._enabled:
			self._job._core.blackboard.remove_listener(event_listener)
		self._event_listeners.remove(event_listener)

	def send(self, name, value = None):
		if not self._enabled:
			raise AttributeError("this component is not enabled")
		self.event_trace(name, value)
		self._job._core.blackboard.send(self.name, name, value)


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
		self._name = name
		self._bind_callback = bind_callback
		self._unbind_callback = unbind_callback
		self._devices = []
		self._callbacks = {}
		self._device_manager = None

	@property
	def name(self):
	    return self._name

	@property
	def devices(self):
	    return self._devices

	def on_add_handle(self, device_manager):
		self._device_manager = device_manager

	def on_remove_handle(self):
		self._device_manager = None

	def on_bind_device(self, device):
		self._device_manager.trace("binding '%s' [%s] to handle '%s'" \
			% (device_name(device.identity[5]), device.identity[0], self.name))

		self.devices.append(device)

		for event_code in self._callbacks:
			self._install_callback(
				device, event_code, self._callbacks[event_code])

		if self._bind_callback:
			self._bind_callback(device)

	def on_unbind_device(self, device):
		if device not in self.devices:
			return

		self._device_manager.trace("unbinding '%s' [%s] from handle '%s'" \
			% (device_name(device.identity[5]), device.identity[0], self.name))

		if self._unbind_callback:
			self._unbind_callback(device)
		
		for event_code in self._callbacks:
			self._uninstall_callback(
				device, event_code)

		self.devices.remove(device)

	def for_each_device(self, f):
		for d in self.devices:
			try:
				f(d)
			except Error as err:
				if err.value != -8: # connection lost
					print(err.description)

	def _install_callback(self, device, event_code, callback):
		self._device_manager.add_device_callback(
			device.identity[0], event_code, callback)

	def _uninstall_callback(self, device, event_code):
		callback = self._callbacks[event_code]
		self._device_manager.remove_device_callback(
			device.identity[0], event_code, callback)

	def register_callback(self, event_code, callback):
		self.unregister_callback(event_code)
		self._callbacks[event_code] = callback
		if self._device_manager:
			self.for_each_device(
				lambda device: self._install_callback(
					device, event_code, callback))

	def unregister_callback(self, event_code):
		if event_code not in self._callbacks:
			return
		if self._device_manager:
			self.for_each_device(
				lambda device: self._uninstall_callback(
					device, event_code))
		del(self._callbacks[event_code])


class SingleDeviceHandle(DeviceHandle):

	def __init__(self, name, device_name_or_id, bind_callback = None, unbind_callback = None, uid = None, auto_fix = False):
		super().__init__(name, bind_callback, unbind_callback)
		self._device_identifier = get_device_identifier(device_name_or_id)
		self._uid = uid
		self._auto_fix = auto_fix
		self._device = None

	@property
	def device(self):
	    return self._device

	def on_bind_device(self, device):
		if len(self.devices) > 0:
			return
		if device.identity[5] != self._device_identifier:
			return
		if self._uid == None:
			if self._auto_fix:
				self._uid = identity[0]
		elif device.identity[0] != self._uid:
			return
		self._device = device
		super().on_bind_device(device)

	def on_unbind_device(self, device):
		super().on_unbind_device(device)
		if self._device == device:
			self._device = None


class MultiDeviceHandle(DeviceHandle):

	def __init__(self, name, device_name_or_id, bind_callback = None, unbind_callback = None):
		super().__init__(name, bind_callback, unbind_callback)
		self._device_identifier = get_device_identifier(device_name_or_id)

	def on_bind_device(self, device):
		if not device.identity[5] == self._device_identifier:
			return
		super().on_bind_device(device)


class EventInfo:

	def __init__(self, sender = None, name = None, predicate = None, transform = None):
		self._sender = sender
		self._name = name
		self._predicate = predicate
		self._transform = transform

	@property
	def sender(self):
		return self._sender

	@property
	def name(self):
		return self._name

	def create_listener(self, callback):
		return EventListener(callback, 
			sender = self._sender, 
			name = self._name, 
			predicate = self._predicate,
			transform = self._transform)

	def __str__(self):
		return "EventInfo(sender = %s, name = %s, predicate: %s, transform: %s)" \
			% (self._sender, self._name,
			   self._transform != None, self._predicate != None)


class EventListener:

	def __init__(self, callback, sender = None, name = None, predicate = None, transform = None, component = None):
		self._callback = callback
		self._sender = sender
		self._name = name
		self._predicate = predicate
		self._transform = transform
		self._component = component

	def __call__(self, event):
		if self._predicate == None or self._predicate(event):
			self._callback(event[0], event[1], 
				self._transform(event[2]) if self._transform else event[2])

	@property
	def sender(self):
	    return self._sender

	@property
	def name(self):
	    return self._name

	@property
	def component(self):
		return self._component
	@component.setter
	def component(self, component):
		self._component = component

	def for_sender(callback, sender):
		return EventListener(callback, sender = sender)

	def for_name(callback, name):
		return EventListener(callback, name = name)

	def for_sender_and_name(callback, sender, name):
		return EventListener(callback, sender = sender, name = name)

	def __str__(self):
		return "EventListener(sender = %s, name = %s, predicate: %s, transform: %s, component = %s)" \
			% (self._sender, self._name,
			   self._transform != None, self._predicate != None, 
			   self._component)
