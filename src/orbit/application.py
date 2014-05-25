# coding=utf-8

# Package orbit.application

"""
Diese Modul enthält die wichtigsten Klassen für die Entwicklung einer
ORBIT-Anwendung. Eine ORBIT-Anwendung wird von einem :py:class:`Core` verwaltet
und kann mehrere :py:class:`Job` Instanzen enthalten.
Ein :py:class:`Job` ist entweder ein :py:class:`Service` 
oder eine :py:class:`App`. 
Jeder :py:class:`Job` fasst eine Gruppe von :py:class:`Component` Instanzen zusammen.

Die TinkerForge-Bricklets werden durch :py:class:`DeviceManager` verwaltet
und den :py:class:`Job` und ihren :py:class:`Component` Instanzen zugeordnet.
:py:class:`Component` und :py:class:`Job` Instanzen
kommunizieren asynchron über das ORBIT-Nachrichtensystem welches durch
die Klasse :py:class:`Blackboard` implementiert wird.
"""

from datetime import datetime
from traceback import print_exc
from threading import Thread, Lock, Event
from collections import deque
from . import setup
from .index import MultiLevelReverseIndex
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
		self._application_history = []

		self._stopper = MultiListener('Core Stopper', self._core_stopper)
		self._stopper.activate(self._blackboard)

		self._stop_event = Event()
		self._stop_event.set()

		self.trace("core initialized")

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
			self.trace("core already started")
			return
		self.trace("starting ...")
		self._stop_event.clear()
		self._started = True
		self._blackboard.start()
		self._device_manager.start()

		self.for_each_job(
			lambda j: j.on_core_started())

		self.trace("... started")

		def activator(job):
			if job.background or job == self.default_application:
				job.active = True
		self.for_each_job(activator)

	def stop(self):
		if not self._started:
			self.trace("core already stopped")
			return

		def deactivator(job):
			job.active = False
		self.for_each_active_job(deactivator)

		self.trace("stopping ...")

		self.for_each_job(
			lambda j: j.on_core_stopped())

		self._device_manager.stop()
		self._blackboard.stop()
		self._started = False
		self.trace("... stopped")
		self._stop_event.set()

	def _core_stopper(self, *args):
		self.trace("core stopping, caused by event")
		Thread(target = self.stop).start()

	def add_stopper(self, slot):
		self._stopper.add_slot(slot)

	def remove_stopper(self, slot):
		self._stopper.remove_slot(slot)

	def wait_for_stop(self):
		if not self._started:
			return
		try:
			self._stop_event.wait()
		except KeyboardInterrupt:
			self.stop()

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
		if self._current_application == application:
			return
		# set job as current application
		self.trace("activating application '%s' ..." % application.name)
		if self._current_application:
			self._current_application.active = False
		self._current_application = application
		if self._current_application:
			self._current_application.active = True
			if application.in_history:
				self._application_history.append(application)
		self.trace("... activated application '%s'" % application.name)

	def clear_application_history(self):
		del(self._application_history[:])

	def deactivate(self, application):
		# if only the name is given: lookup job name
		if type(application) is str:
			if application in self._jobs:
				application = self._jobs[application]
			else:
				raise KeyError("job name not found")
		# deactivate and activate last application in history
		if len(self._application_history) > 0:
			next_app = self._application_history.pop()
			if next_app == application:
				if len(self._application_history) > 0:
					next_app = self._application_history[-1]
				else:
					next_app = self._default_application
			self.activate(next_app)
		elif self._default_application:
			self.activate(self._default_application)

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
			self.trace("connecting to %s:%d ..." % (host, port))
			connected = False
			while not connected:
				try:
					self._conn.connect(host, port)
					connected = True
				except TimeoutError:
					self.trace("... timeout, retry ...")
			self.trace("... connected")

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
						self.trace("Error during initialization of : %s" % err.description)
				except Exception as exc:
					self.trace("Exception caught during device initialization:\n%s" % exc)

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
						self.trace("Error during device finalization: %s" % err.description)
				except Exception as exc:
					self.trace("Exception caught during device finalization:\n%s" % exc)

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
		self._index = MultiLevelReverseIndex(('job', 'component', 'name'))
		self._lock = Lock()
		self._queue_event = Event()
		self._queue = deque()
		self._stopped = True
		self._worker = Thread(name = 'Orbit Blackboard Queue Worker', target = self._queue_worker)

	def trace(self, text):
		if self._core.configuration.event_tracing:
			_trace(text, 'Blackboard')

	def _locked(self, f, *nargs, **kargs):
		self._lock.acquire()
		result = f(*nargs, **kargs)
		self._lock.release()
		return result

	def job_group(self, group_name, *names):
		self._locked(
			self._index.add_group, 'job', group_name, names)

	def component_group(self, group_name, *names):
		self._locked(
			self._index.add_group, 'component', group_name, names)

	def name_group(self, group_name, *names):
		self._locked(
			self._index.add_group, 'name', group_name, names)

	def add_listener(self, listener):
		self._locked(
			self._index.add, listener)

	def remove_listener(self, listener):
		self._locked(
			self._index.remove, listener)

	def start(self):
		if not self._stopped:
			return
		self.trace("starting blackboard ...")
		self._stopped = False
		self._worker.start()

	def stop(self):
		if self._stopped:
			return
		self.trace("stopping blackboard ...")
		self._stopped = True
		self._queue_event.set()
		self._worker.join()

	def _queue_worker(self):
		self.trace("... blackboard started")
		while not self._stopped:
			# working the queue until it is empty
			while True:
				msg = self._locked(lambda: self._queue.popleft() if len(self._queue) > 0 else None)
				if msg:
					self._distribute(msg)
				else:
					break

			# wait for new events or stopping
			self._queue_event.wait()
			self._queue_event.clear()

		self.trace("... blackboard stopped")

	def _distribute(self, msg):
		listeners = self._index.lookup(msg)
		for l in listeners:
			self.trace("ROUTE %s, %s, %s => %s (%s, %s, %s)" \
				% (msg.job, msg.component, msg.name, l.receiver, l.job, l.component, l.name))
			try:
				l(msg)
			except Exception as exc:
				self.trace("Error while calling listener: %s" % exc)
				print_exc()

	def send(self, job, component, name, value):
		if not self._core.started:
			self.trace("DROPPED event before core started (%s, %s, %s)" \
				% (job, component, name))
			return

		msg = Blackboard.Message(job, component, name, value)
		self._locked(self._queue.append, msg)
		self._queue_event.set()

	class Message:

		def __init__(self, job, component, name, value):
			self.job = job
			self.component = component
			self.name = name
			self.value = value


class Job:

	def __init__(self, name, background):
		self._name = name
		self._core = None
		self._background = background
		self._components = {}
		self._active = False
		self._tracing = None
		self._event_tracing = None
		self._listeners = []

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
	def event_tracing(self):
		return self._event_tracing
	@event_tracing.setter
	def event_tracing(self, enabled):
		self._event_tracing = enabled

	def event_trace(self, name, value):
		if self._event_tracing == True or \
			(self._event_tracing != False and \
			 self._core.configuration.event_tracing):

			_trace("EVENT %s: %s" % (name, str(value)), "Job %s" % self._name)

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
			for listener in self._listeners:
				self._core.blackboard.add_listener(listener)
			self.on_activated()
			self.trace("... activated")
		else:
			self.trace("deactivating ...")
			for listener in self._listeners:
				self._core.blackboard.remove_listener(listener)
			self.on_deactivated()
			self.trace("... deactivated")

	def on_activated(self):
		def enabler(component):
			component.enabled = True
		self.for_each_component(lambda c: c.on_job_activated())
		self.for_each_component(enabler)

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

	def add_listener(self, listener):
		if listener in self._listeners:
			return
		listener.receiver = self.name
		self._listeners.append(listener)
		if self._active:
			self._core.blackboard.add_listener(listener)

	def remove_listener(self, listener):
		if listener not in self._listeners:
			return
		if self._active:
			self._core.blackboard.remove_listener(listener)
		self._listeners.remove(listener)

	def send(self, name, value = None):
		if not self._active:
			raise AttributeError("this job is not active")
		self.event_trace(name, value)
		self._core.blackboard.send(self.name, 'JOB', name, value)


class App(Job):

	def __init__(self, name, in_history = False, 
		activator = None, deactivator = None):
		super().__init__(name, False)
		self._activators = MultiListener("%s Activator" % name, self._process_activator)
		self._deactivators = MultiListener("%s Deactivator" % name, self._process_deactivator)
		self._in_history = in_history

		if activator:
			if type(activator) is list or type(activator) is tuple:
				for a in activator:
					self.add_activator(a)
			else:
				self.add_activator(activator)

		if deactivator:
			if type(deactivator) is list or type(deactivator) is tuple:
				for d in deactivator:
					self.add_deactivator(d)
			else:
				self.add_deactivator(deactivator)

	@property
	def in_history(self):
	    return self._in_history

	def _process_activator(self, *args):
		self.trace("activating app %s, caused by event" % self.name)
		self._core.activate(self)

	def _process_deactivator(self, *args):
		self.trace("deactivating app %s, caused by event" % self.name)
		self._core.deactivate(self)

	def add_activator(self, slot):
		self._activators.add_slot(slot)

	def remove_activator(self, slot):
		self._activators.remove_slot(slot)

	def add_deactivator(self, slot):
		self._deactivators.add_slot(slot)

	def remove_deactivator(self, slot):
		self._deactivators.remove_slot(slot)
	
	def on_install(self, core):
		super().on_install(core)
		self._activators.activate(self._core.blackboard)
		self._deactivators.activate(self._core.blackboard)

	def on_uninstall(self):
		self._deactivators.deactivate(self._core.blackboard)
		self._activators.deactivate(self._core.blackboard)
		super().on_uninstall()

	def activate(self):
		if not self.core:
			raise AttributeError("the job is not associated with a core")
		if self.active:
			raise AttributeError("the job is already activated")
		self.core.activate(self)

	def deactivate(self):
		if not self.core:
			raise AttributeError("the job is not associated with a core")
		if not self.active:
			raise AttributeError("the job is not activated")
		self.core.deactivate(self)


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
		self._listeners = []

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
			self.trace("enabling ...")
			for listener in self._listeners:
				listener.receiver = "%s, %s" % (self._job.name, self.name)
				self._job._core.blackboard.add_listener(listener)
			for device_handle in self._device_handles:
				self._job._core.device_manager.add_handle(device_handle)
			self.on_enabled()
			self.trace("... enabled")
		else:
			self.trace("disabling ...")
			self.on_disabled()
			for listener in self._listeners:
				self._job._core.blackboard.remove_listener(listener)
			for device_handle in self._device_handles:
				self._job._core.device_manager.remove_handle(device_handle)
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

	def add_listener(self, listener):
		if listener in self._listeners:
			return
		self._listeners.append(listener)
		if self._enabled:
			listener.receiver = "%s, %s" % (self._job.name, self.name)
			self._job._core.blackboard.add_listener(listener)

	def remove_listener(self, listener):
		if listener not in self._listeners:
			return
		if self._enabled:
			self._job._core.blackboard.remove_listener(listener)
		self._listeners.remove(listener)

	def send(self, name, value = None):
		if not self._enabled:
			raise AttributeError("this component is not enabled")
		self.event_trace(name, value)
		self._job._core.blackboard.send(self._job.name, self.name, name, value)


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


class Slot:

	def __init__(self, job, component, name, predicate = None, transformation = None):
		self._job = job
		self._component = component
		self._name = name
		self._predicate = predicate
		self._transformation = transformation

	@property
	def job(self):
		return self._job

	@property
	def component(self):
		return self._component

	@property
	def name(self):
		return self._name

	@property
	def predicate(self):
		return self._predicate

	@property
	def transformation(self):
		return self._transformation

	def for_job(job):
		return Slot(job, None, None)

	def for_component(job, component):
		return Slot(job, component, None)

	def for_name(name):
		return Slot(None, None, name)

	def listener(self, callback):
		return Listener(callback, self)

	def __str__(self):
		return "Slot(job = %s, component = %s, name = %s, predicate: %s, transformation: %s)" \
			% (self._job, self._component, self._name,
			   self._transform != None, self._predicate != None)


class Listener:

	def __init__(self, callback, slot):
		self._callback = callback
		self._slot = slot
		self._receiver = None

	def __call__(self, msg):
		if self._slot.predicate == None or \
			self._slot.predicate(msg.job, msg.component, msg.name, msg.value):
			self._callback(msg.job, msg.component, msg.name,
				self._slot.transformation(msg.value) if self._slot.transformation else msg.value)

	@property
	def job(self):
		return self._slot.job

	@property
	def component(self):
		return self._slot.component

	@property
	def name(self):
		return self._slot.name

	@property
	def receiver(self):
	    return self._receiver
	@receiver.setter
	def receiver(self, value):
	    self._receiver = value

	def __str__(self):
		return "Listener(job = %s, component = %s, name = %s, predicate: %s, transform: %s, receiver = %s)" \
			% (self._slot.job, self._slot.component, self._slot.name,
			   self._slot.transformation != None, self._slot.predicate != None, 
			   self._receiver)


class MultiListener:

	def __init__(self, name, callback):
		self._callback = callback
		self._listeners = {}
		self._blackboards = []
		self._name = name

	@property
	def name(self):
	    return self._name

	@property
	def slots(self):
		return self._listeners.keys()

	@property
	def listeners(self):
		return self._listeners.values()

	def add_slot(self, slot):
		listener = slot.listener(self._callback)
		listener.receiver = self.name
		self._listeners[slot] = listener
		for blackboard in self._blackboards:
			blackboard.add_listener(listener)

	def remove_slot(self, slot):
		listener = self._listeners[slot]
		del(self._listeners[slot])
		for blackboard in self._blackboards:
			blackboard.remove_listener(listener)

	def activate(self, blackboard):
		for listener in self._listeners.values():
			blackboard.add_listener(listener)
		self._blackboards.append(blackboard)

	def deactivate(self, blackboard):
		for listener in self._listeners.values():
			blackboard.remove_listener(listener)
		self._blackboards.remove(blackboard)
