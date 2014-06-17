# coding=utf-8

# Package orbit.application

"""
Diese Modul enthält die wichtigsten Klassen für die Entwicklung einer
ORBIT-Anwendung. 
Eine ORBIT-Anwendung wird von einem :py:class:`Core` verwaltet
und kann mehrere :py:class:`Job`-Objekte enthalten.
Jeder :py:class:`Job` fasst eine Gruppe von :py:class`Component`-Objekten zusammen.
Ein :py:class:`Job` ist entweder eine :py:class:`App` oder ein :py:class:`Service`.

.. image:: figures/architecture-overview.png

Die TinkerForge-Bricklets werden durch den :py:class:`DeviceManager` verwaltet
und den :py:class:`Component`-Objekten über :py:class:`DeviceHandle`-Objekte zugeordnet.

.. image:: figures/devicemanager-overview.png

:py:class:`Component`- und :py:class:`Job`-Objekte
kommunizieren asynchron über das ORBIT-Nachrichtensystem welches durch
die Klasse :py:class:`Blackboard` implementiert wird.

.. image:: figures/blackboard-overview.png

:py:class:`Component`- und :py:class:`Job`-Objekte können jederzeit Nachrichten
senden. Diese Nachrichten werden in einer Warteschlange abgelegt und in einem 
dedizierten Nachrichten-Thread an die Empfänger versandt
(:py:meth:`Job.send`, :py:meth:`Component.send`).

Für den Empfang von Nachrichten werden :py:class:`Listener`-Objekte verwendet.
Ein :py:class:`Listener` bindet ein Empfangsmuster/-filter an ein Callback
(:py:meth:`Job.listen`, :py:meth:`Component.listen`).
Wird eine Nachricht über das Nachrichtensystem versandt, welches dem Muster
eines :py:class:`Listener`-Objekts entspricht, wird das Callback des Empfängers aufgerufen.
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
	"""
	Diese Klasse repräsentiert den Kern einer ORBIT-Anwendung.

	**Parameter**

	``config`` (*optional*)
		Die Konfiguration für die ORBIT-Anwendung. 
		Eine Instanz der Klasse :py:class:`setup.Configuration`.

	**Beschreibung**

	Diese Klasse ist verantwortlich für die Einrichtung des Nachrichtensystems
	und der Geräteverwaltung. Des Weiteren verwaltet sie alle Dienste
	und Apps, die in der ORBIT-Anwendung verwendet werden.

	Für die Einrichtung einer Anwendung wird zunächst eine Instanz von
	:py:class:`Core` erzeugt. Dabei kann optional
	eine benutzerdefinierte Konfiguration (:py:class:`..setup.Configuration`)
	an den Konstruktor übergeben werden. 
	Anschließend werden durch den mehrfachen Aufruf von
	:py:meth:`install` Jobs hinzugefügt. Jobs können 
	Dienste (:py:class:`Service`) oder Apps (:py:class:`App`) sein.
	Über die Eigenschaft :py:attr:`default_application` kann eine App
	als Standard-App festgelegt werden.

	Um die ORBIT-Anwendung zu starten wird die Methode :py:meth:`start`
	aufgerufen. Um die ORBIT-Anwendung zu beenden, kann entweder direkt
	die Methode :py:meth:`stop` aufgerufen werden, oder es werden
	vor dem Start der Anwendung ein oder mehrere Slots
	(Ereignisempfänger für das ORBIT-Nachrichtensystem) hinzugefügt,
	welche die Anwendung stoppen sollen.
	"""

	def __init__(self, config = setup.Configuration()):
		self._is_started = False
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
		"""
		Schreibt eine Nachverfolgungsmeldung mit dem Ursprung ``Core``
		auf die Konsole.
		"""
		if self._configuration.core_tracing:
			_trace(text, 'Core')

	@property
	def is_started(self):
		"""
		Gibt an ob die ORBIT-Anwendung gestartet wurde oder nicht.
		(*schreibgeschützt*)
		Ist ``True`` wenn die Anwendung läuft, sonst ``False``.

		*Siehe auch:*
		:py:meth:`start`,
		:py:meth:`stop`
		"""
		return self._is_started

	@property
	def configuration(self):
		"""
		Gibt die ORBIT-Anwendungskonfiguration (:py:class:`..setup.Configuration`) zurück.
		(*schreibgeschützt*)
		"""
		return self._configuration

	@property
	def device_manager(self):
		"""
		Gibt den Gerätemanager (:py:class:`DeviceManager`) zurück.
		(*schreibgeschützt*)
		"""
		return self._device_manager

	@property
	def blackboard(self):
		"""
		Gibt das Nachrichtensystem (:py:class:`Blackboard`) zurück.
		(*schreibgeschützt*)
		"""
		return self._blackboard

	@property
	def jobs(self):
		"""
		Gibt ein Dictionary mit allen installierten Jobs zurück.
		(*schreibgeschützt*)
		Der Schlüssel ist der Name des Jobs und der Wert ist der Job selbst.

		*Siehe auch:*
		:py:meth:`install`,
		:py:meth:`uninstall`
		"""
		return self._jobs

	@property
	def default_application(self):
		"""
		Gibt die Standard-App zurück oder legt sie fest.
		"""
		return self._default_application
	@default_application.setter
	def default_application(self, application):
		self._default_application = application

	def start(self):
		"""
		Startet die ORBIT-Anwendung.

		Beim Start wird das Nachrichtensystem gestartet und damit
		die Weiterleitung von Ereignissen zwischen den Jobs und
		Komponenten aktiviert. Des Weiteren wird der Gerätemanager
		gestartet, der die Verbindung zum TinkerForge-Server aufbaut
		und die angeschlossenen Bricks und Bricklets ermittelt.

		Ist die Infrastruktur des Kerns erfolgreich gestartet,
		werden zunächst alle Dienste, und zum Schluss die Standard-App
		aktiviert.

		.. note::
			Wird diese Methode aufgerufen, wenn die ORBIT-Anwendung
			bereits gestartet wurde, wird lediglich eine Meldung
			auf der Konsole ausgegeben.

		*Siehe auch:*
		:py:meth:`stop`,
		:py:attr:`is_started`
		"""
		if self._is_started:
			self.trace("core already started")
			return
		self.trace("starting ...")
		self._stop_event.clear()
		self._is_started = True
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
		"""
		Stoppt die ORBIT-Anwendung.

		Beim Stoppen werden zunächst alle Jobs (Dienste und Apps)
		deaktiviert. Anschließend wird der Gerätemanager
		beendet und dabei die Verbindung zum TinkerForge-Server getrennt.
		Zum Schluss wird das Nachrichtensystem beendet und die Weiterleitung
		von Ereignissen gestoppt.

		.. note::
			Wird diese Methode aufgerufen, wenn die ORBIT-Anwendung
			nicht gestartet ist, wird lediglich eine Meldung auf der Konsole
			ausgegeben.

		*Siehe auch:*
		:py:meth:`start`,
		:py:attr:`is_started`
		"""
		if not self._is_started:
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
		self._is_started = False
		self.trace("... stopped")
		self._stop_event.set()

	def _core_stopper(self, *args):
		self.trace("core stopping, caused by event")
		Thread(target = self.stop).start()

	def add_stopper(self, slot):
		"""
		Fügt einen :py:class:`Slot` hinzu, der das Stoppen der ORBIT-Anwendung
		veranlassen soll.

		*Siehe auch:*
		:py:meth:`remove_stopper`
		"""
		self._stopper.add_slot(slot)

	def remove_stopper(self, slot):
		"""
		Entfernt einen :py:class:`Slot`, der das Stoppen der ORBIT-Anwendung
		veranlassen sollte.

		*Siehe auch:*
		:py:meth:`add_stopper`
		"""
		self._stopper.remove_slot(slot)

	def wait_for_stop(self):
		"""
		Blockiert solange den Aufrufer, bis die ORBIT-Anwendung beendet wurde.

		Der Grund für das Beenden kann ein direkter Aufruf von :py:meth:`stop`
		oder das Abfangen eines Ereignisses von einem der Stopper-Slots sein.

		Zusätzlich wird das Unterbrechungssignal (SIGINT z.B. Strg+C) abgefangen.
		Tritt das Unterbrechungssignal auf, wird die ORBIT-Anwendung durch den Aufruf
		von :py:meth:`stop` gestoppt und die Methode kehrt zum Aufrufer zurück.

		.. note::
			Die Methode kehrt erst dann zum Aufrufer zurück, 

			* wenn alle Jobs deaktiviert wurden,
			* der Gerätemanager alle Bricks und Bricklets freigegeben und die Verbindung
			  zum TinkerForge-Server beendet hat
			* und das Nachrichtensystem alle ausstehenden Ereignisse weitergeleitet hat
			  und beendet wurde.

		.. warning::
			Diese Methode darf nicht direkt oder indirekt durch einen 
			:py:class:`Slot` oder :py:class:`Listener`
			aufgerufen werden, da sie andernfalls das Nachrichtensystem der ORBIT-Anwendung
			blockiert.

		*Siehe auch:*
		:py:meth:`stop`,
		:py:meth:`add_stopper`, 
		:py:meth:`remove_stopper`
		"""
		if not self._is_started:
			return
		try:
			self._stop_event.wait()
		except KeyboardInterrupt:
			self.stop()

	def install(self, job):
		"""
		Fügt der ORBIT-Anwendung einen Job (:py:class:`Job`) hinzu.
		Ein Job kann ein Dienst (:py:class:`Service`) oder eine 
		App (:py:class:`App`) sein.
		Jobs können vor oder nach dem Starten der ORBIT-Anwendung 
		hinzugefügt werden.

		Wird ein Job mehrfach hinzugefügt, wird eine Ausnahme vom Typ 
		:py:exc:`AttributeError` ausgelöst.

		*Siehe auch:*
		:py:meth:`uninstall`,
		:py:attr:`jobs`
		"""
		if job.core:
			raise AttributeError("the given job is already associated with a core")
		if job.name in self._jobs:
			self.uninstall(self._jobs[job.name])
		self._jobs[job.name] = job
		job.on_install(self)
		self.trace("installed job '%s'" % job.name)
		if self._is_started and job.background:
			job.active = True

	def uninstall(self, job):
		"""
		Entfernt einen Job aus der ORBIT-Anwendung.
		Ist der Job zur Zeit aktiv, wird er deaktiviert bevor
		er aus der Anwendung entfernt wird.

		Wird ein Job übergeben, der nicht installiert ist,
		wird eine Ausnahme vom Typ :py:exc:`AttributeError` ausgelöst.

		*Siehe auch:*
		:py:meth:`install`,
		:py:attr:`jobs`
		"""
		if job.name not in self._jobs:
			raise AttributeError("the given job is not associated with this core")
		if job.active:
			job.active = False
		job.on_uninstall()
		del(self._jobs[job.name])
		self.trace("uninstalled job '%s'" % job.name)

	def for_each_job(self, f):
		"""
		Führt eine Funktion für jeden installierten Job aus.

		*Siehe auch:*
		:py:attr:`jobs`,
		:py:meth:`install`,
		:py:meth:`uninstall`
		"""
		for job in self._jobs.values():
			f(job)

	def for_each_active_job(self, f):
		"""
		Führt eine Funktion für jeden aktiven Job aus.

		*Siehe auch:*
		:py:meth:`activate`,
		:py:meth:`deactivate`
		"""
		for job in self._jobs.values():
			if job.active:
				f(job)

	def activate(self, application):
		"""
		Aktiviert eine App. Die App kann direkt übergeben
		oder durch ihren Namen identifiziert werden.

		Zu jedem Zeitpunkt ist immer nur eine App aktiv.
		Ist bereits eine andere App aktiv, wird diese deaktiviert,
		bevor die übergebene App aktiviert wird.

		Ist die Eigenschaft :py:attr:`App.in_history` der bereits aktiven App 
		gleich ``True``, wird die App vor dem Deaktivieren in der
		App-History vermerkt.

		Wird der Name einer App übergeben, die nicht in der ORBIT-Anwendung
		installiert ist, wird eine :py:exc:`KeyError` ausgelöst.

		*Siehe auch:*
		:py:meth:`deactivate`,
		:py:meth:`clear_application_history`,
		:py:meth:`for_each_active_job`,
		:py:attr:`Job.active`
		"""
		# if only the name is given: lookup job name
		if type(application) is str:
			if application in self._jobs:
				application = self._jobs[application]
			else:
				raise KeyError("job name not found")
		else:
			if application not in self._jobs.values:
				raise 
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
		"""
		Leert die App-History.

		Das hat zur Folge, dass nach dem Deaktivieren 
		der zur Zeit aktiven App die Standard-App oder gar keine
		aktiviert wird.

		*Siehe auch:*
		:py:meth:`activate`,
		:py:meth:`deactivate`
		"""
		del(self._application_history[:])

	def deactivate(self, application):
		"""
		Deaktiviert eine App. Die App App kann direkt übergeben
		oder durch ihren Namen identifiziert werden.

		Nach dem Deaktivieren der App wird geprüft, ob in der App-History
		eine App vermerkt ist, welche vorher aktiv war. Ist dies der
		Fall wird jene App automatisch aktiviert.

		Ist die App-History leer, wird geprüft ob eine Standard-App
		registriert ist (:py:attr:`default_application`) und ggf. diese aktiviert.

		*Siehe auch:*
		:py:meth:`activate`,
		:py:meth:`clear_application_history`,
		:py:attr:`Job.active`
		"""
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
	"""
	Diese Klasse implementiert den Gerätemanager einer ORBIT-Anwendung.

	**Parameter**

	``core``
		Ein Verweis auf den Anwendungskern der ORBIT-Anwendung.
		Eine Instanz der Klasse :py:class:`Core`.

	**Beschreibung**

	Der Gerätemanager baut eine Verbindung zu einem TinkerForge-Server auf,
	ermittelt die angeschlossenen Bricks und Bricklets und stellt
	den Komponenten in den Jobs die jeweils geforderten Geräte zur Verfügung.

	Dabei behält der Gerätemanager die Kontrolle über den Gerätezugriff.
	Das bedeutet, dass der Gerätemanager die Autorität hat, einer Komponente
	ein Gerät zur Verügung zu stellen, aber auch wieder zu entziehen.

	Eine Komponente bekommt ein von ihm angefordertes Gerät i.d.R. dann zugewiesen,
	wenn die Komponente aktiv und das Gerät verfügbar ist. Wird die Verbindung
	zum TinkerForge-Server unterbrochen oder verliert der TinkerForge-Server
	die Verbindung zum Master-Brick (USB-Kabel herausgezogen), entzieht
	der Gerätemanager der Komponente automatisch das Gerät, so dass eine 
	Komponente i.d.R. keine Verbindungsprobleme behandeln muss.

	Umgesetzt wird dieses Konzept mit Hilfe der Klassen :py:class:`SingleDeviceHandle`
	und :py:class:`MultiDeviceHandle`.
	"""

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
		"""
		Schreibt eine Nachverfolgungsmeldung mit dem Ursprung ``DeviceManager``
		auf die Konsole.
		"""
		if self._core.configuration.device_tracing:
			_trace(text, 'DeviceManager')

	@property
	def devices(self):
		"""
		Ein Dictionary mit allen zur Zeit verfügbaren Geräten.
		Die UID des Geräts ist der Schlüssel und der Wert ist eine Instanz
		der TinkerForge-Geräte-Klasse 
		(wie z.B. ``tinkerforge.bricklet_lcd_20x4.BrickletLCD20x4``).
		"""
		return self._devices

	def start(self):
		"""
		Startet den Gerätemanager und baut eine Verbindung zu einem TinkerForge-Server auf.
		Die Verbindungdaten für den Server werden der ORBIT-Konfiguration entnommen.

		Siehe auch: :py:meth:`stop`
		"""
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
		"""
		Trennt die Verbindung zum TinkerForge-Server und beendet den Gerätemanager.

		Vor dem Trennen der Verbindung wird die Zuordnung zwischen den Geräten
		und den Komponenten aufgehoben.

		Siehe auch: :py:meth:`start`
		"""
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
		"""
		Richtet eine Initialisierungsfunktion für einen Brick- oder Bricklet-Typ ein.

		**Parameter**

		``device_identifier``
			Die Geräte-ID der TinkerForge-API. 
			Z.B. ``tinkerforge.bricklet_lcd_20x4.BrickletLCD20x4.DEVICE_IDENTIFIER``
		``initializer``
			Eine Funktion, welche als Parameter eine Instanz der TinkerForge-Geräteklasse
			entgegennimmt.

		**Beschreibung**

		Sobald der Gerätemanager ein neues Gerät entdeckt, 
		zu dem er bisher keine Verbindung aufgebaut hatte, 
		ruft er alle Initialisierungsfunktionen für die entsprechende
		Geräte-ID auf.

		*Siehe auch:*
		:py:meth:`add_device_finalizer`
		"""
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
		"""
		Richtet eine Abschlussfunktion für einen Brick- oder Bricklet-Typ ein.

		**Parameter**

		``device_identifier``
			Die Geräte-ID der TinkerForge-API. 
			Z.B. ``tinkerforge.bricklet_lcd_20x4.BrickletLCD20x4.DEVICE_IDENTIFIER``
		``finalizer``
			Eine Funktion, welche als Parameter eine Instanz der TinkerForge-Geräteklasse
			entgegennimmt.

		**Beschreibung**

		Sobald der Gerätemanager die Verbindung zu einem Gerät selbstständig
		aufgibt (d.h. die Verbindung nicht durch eine Störung unterbrochen wurde),
		ruft er alle Abschlussfunktionen für die entsprechende
		Geräte-ID auf.

		*Siehe auch:*
		:py:meth:`add_device_initializer`
		"""
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
		"""
		Richtet eine Geräteanforderung (Geräte-Handle) ein.

		Eine Geräteanforderung ist eine Instanz einer Sub-Klasse
		von :py:class:`DeviceHandle`. Das kann entweder eine Instanz von
		:py:class:`SingleDeviceHandle` oder von :py:class:`MultiDeviceHandle` sein.

		Das übergebene Geräte-Handle wird über alle neu entdeckten Geräte
		mit einem Aufruf von :py:meth:`DeviceHandle.on_bind_device` benachrichtigt.
		Je nach Konfiguration nimmt das Handle das neue Gerät an oder ignoriert es.
		Verliert der Gerätemanager die Verbindung zu einem Gerät, wird das
		Geräte-Handle ebenfalls mit einem Aufruf von
		:py:meth:`DeviceHandle.on_unbind_device` benachrichtigt.

		*Siehe auch:*
		:py:meth:`remove_handle`
		"""
		if device_handle in self._device_handles:
			return
		self._device_handles.append(device_handle)
		device_handle.on_add_handle(self)
		for device in self._devices.values():
			device_handle.on_bind_device(device)

	def remove_handle(self, device_handle):
		"""
		Entfernt eine Geräteanforderung (Geräte-Handle).

		Eine Geräteanforderung ist eine Instanz einer Sub-Klasse
		von :py:class:`DeviceHandle`. Das kann entweder eine Instanz von
		:py:class:`SingleDeviceHandle` oder von :py:class:`MultiDeviceHandle` sein.

		*Siehe auch:*
		:py:meth:`add_handle`
		"""
		if device_handle not in self._device_handles:
			return
		for device in self._devices.values():
			device_handle.on_unbind_device(device)
		device_handle.on_remove_handle()
		self._device_handles.remove(device_handle)

	def add_device_callback(self, uid, event, callback):
		"""
		Richtet eine Callback-Funktion für ein Ereignis
		eines Bricks oder eines Bricklets ein.

		**Parameter**

		``uid``
			Die UID des Gerätes für das ein Ereignis abgefangen werden soll.
		``event``
			Die ID für das abzufangene Ereignis.
			Z.B. ``tinkerforge.bricklet_lcd_20x4.BrickletLCD20x4.CALLBACK_BUTTON_PRESSED``
		``callback``
			Eine Callback-Funktion die bei Auftreten des Ereignisses aufgerufen werden soll.

		**Beschreibung**

		Da jedes Ereignis andere Ereignisparameter besitzt,
		muss die richtige Signatur für die Callbackfunktion der TinkerForge-Dokumentation
		entnommen werden. Die Ereignisparameter werden in der API-Dokumentation
		für jeden Brick und jedes Bricklet im Abschnitt *Callbacks* beschrieben.

		.. note:: Der Gerätemanager stellt einen zentralen
			Mechanismus für die Registrierung von Callbacks
			für Geräteereignisse zur Verfügung, weil die 
			TinkerForge-Geräteklassen nur ein Callback per Ereignis
			zulassen. Der Gerätemanager hingegen unterstützt beliebig viele 
			Callbacks für ein Ereignis eines Gerätes.

		*Siehe auch:*
		:py:meth:`remove_device_callback`
		"""
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
		"""
		Entfernt eine Callback-Funktion von einem Ereignis
		eines Bricks oder eines Bricklets.

		**Parameter**

		``uid``
			Die UID des Gerätes für das ein Callback aufgehoben werden soll.
		``event``
			Die ID für das Ereignis.
			Z.B. ``tinkerforge.bricklet_lcd_20x4.BrickletLCD20x4.CALLBACK_BUTTON_PRESSED``
		``callback``
			Die registrierte Callback-Funktion die entfernt werde soll.

		**Beschreibung**

		Für die Aufhebung des Callbacks muss die gleiche Funktionsreferenz übergeben werden
		wie bei der Einrichtung des Callback.

		*Siehe auch:*
		:py:meth:`add_device_callback`
		"""
		if uid in self._device_callbacks:
			callbacks = self._device_callbacks[uid]
			if event in callbacks:
				mcc = callbacks[event]
				self.trace("removing callback from dispatcher for [%s] (%s)" % (uid, event))
				mcc.remove_callback(callback)


class Blackboard:
	"""
	Diese Klasse implementiert das ORBIT-Nachrichtensystem.

	**Parameter**

	``core``
		Ein Verweis auf den Anwendungskern der ORBIT-Anwendung.
		Eine Instanz der Klasse :py:class:`Core`.

	**Beschreibung**

	Das Nachrichtensystem ist nach dem Blackboard-Entwurfsmuster
	entwickelt. Nachrichten werden von einem Absender an das Nachrichtensystem
	übergeben, ohne dass der Absender weiß, wer die Nachricht empfangen wird
	(:py:meth:`send`).

	Empfänger können sich mit einem Empfangsmuster (:py:class:`Slot`) 
	bei dem Nachrichtensystem registrieren (:py:meth:`add_listener`)
	und bekommen alle Nachrichten zugestellt, die ihrem Empfangsmuster entsprechen.

	Das Zustellen der Nachrichten (der Aufruf der Empfänger-Callbacks) 
	erfolgt in einem dedizierten Thread. Das hat den Vorteil, dass das Versenden
	einer Nachricht ein asynchroner Vorgang ist, der den Absender nicht blockiert.

	Jede Nachricht ist einem Ereignis zugeordnet. Dieses Ereignis ist
	durch einen Job, eine Komponente und einen Ereignisnamen definiert.
	Der Absender eines Ereignisses gibt beim Versenden einer Nachricht
	den Namen des Ereignisses an.

	Um das Erzeugen von Empfangsmustern (:py:class:`Slot`) zu vereinfachen,
	können Jobs, Komponenten und Ereignisnamen zu Gruppen zusammengefasst werden
	(:py:meth:`job_group`, :py:meth:`component_group`, :py:meth:`name_group`).
	"""

	def __init__(self, core):
		self._core = core
		self._index = MultiLevelReverseIndex(('job', 'component', 'name'))
		self._lock = Lock()
		self._queue_event = Event()
		self._queue = deque()
		self._stopped = True
		self._immediate_stop = False
		self._worker = Thread(name = 'Orbit Blackboard Queue Worker', target = self._queue_worker)

	def trace(self, text):
		"""
		Schreibt eine Nachverfolgungsmeldung mit dem Ursprung ``Blackboard``
		auf die Konsole.
		"""
		if self._core.configuration.event_tracing:
			_trace(text, 'Blackboard')

	def _locked(self, f, *nargs, **kargs):
		self._lock.acquire()
		result = f(*nargs, **kargs)
		self._lock.release()
		return result

	def job_group(self, group_name, *names):
		"""
		Richtet eine Absendergruppe auf Job-Ebene ein.

		**Parameter**

		``group_name``
			Der Name der Gruppe.
		``names`` (*var args*)
			Die Namen der Jobs, welche in der Gruppe zusammengefasst werden sollen.

		**Beschreibung**

		Durch eine Absendergruppe auf Job-Ebene kann ein Slot
		anstelle eines spezifischen Jobnamens einen Gruppennamen 
		im Empfangsmuster angeben.

		*Siehe auch:*
		:py:class:`Slot`,
		:py:class:`Listener`,
		:py:meth:`add_listener`,
		:py:meth:`remove_listener`,
		:py:meth:`Job.listen`,
		:py:meth:`Component.listen`
		"""
		self._locked(
			self._index.add_group, 'job', group_name, names)

	def component_group(self, group_name, *names):
		"""
		Richtet eine Absendergruppe auf Komponentenebene ein.

		**Parameter**

		``group_name``
			Der Name der Gruppe.
		``names`` (*var args*)
			Die Namen der Komponenten, welche in der Gruppe zusammengefasst werden sollen.

		**Beschreibung**

		Durch eine Absendergruppe auf Komponentenebene kann ein Slot
		anstelle eines spezifischen Komponentennamens einen Gruppennamen 
		im Empfangsmuster angeben.

		*Siehe auch:*
		:py:class:`Slot`,
		:py:class:`Listener`,
		:py:meth:`add_listener`,
		:py:meth:`remove_listener`,
		:py:meth:`Job.listen`,
		:py:meth:`Component.listen`
		"""
		self._locked(
			self._index.add_group, 'component', group_name, names)

	def name_group(self, group_name, *names):
		"""
		Richtet eine Absendergruppe auf Ereignisebene ein.

		**Parameter**

		``group_name``
			Der Name der Gruppe.
		``names`` (*var args*)
			Die Namen der Ereignisse, welche in der Gruppe zusammengefasst werden sollen.

		**Beschreibung**

		Durch eine Absendergruppe auf Ereignisebene kann ein Slot
		anstelle eines spezifischen Ereignisnamens einen Gruppennamen 
		im Empfangsmuster angeben.

		*Siehe auch:*
		:py:class:`Slot`,
		:py:class:`Listener`,
		:py:meth:`add_listener`,
		:py:meth:`remove_listener`,
		:py:meth:`Job.listen`,
		:py:meth:`Component.listen`
		"""
		self._locked(
			self._index.add_group, 'name', group_name, names)

	def add_listener(self, listener):
		"""
		Registriert einen Empfänger mit einem Empfangsmuster im Nachrichtensystem.
		
		Das Empfangsmuster besteht aus den drei Attributen 
		``job``, ``component`` und ``name``.
		Diese Attribute können jeweils einen Namen, einen Gruppennamen oder ``None`` enthalten.
		Sie werden benutzt, um zu entscheiden, ob eine Nachricht 
		an den Empfänger übergeben wird oder nicht. 

		Üblichweise wird als Empfänger ein :py:class:`Listener`-Objekt verwendet,
		welches mit einem :py:class:`Slot`-Objekt und einem Callback initialisiert wurde.

		| Die Nachricht 
			*M*: job = ``"A"``, component = ``"1"``, name = ``"a"``, value = ...
		| wird an alle Empfänger mit dem Empfangsmuster
		| |lpb| job = ``"A"``, component = ``"1"``, name = ``"a"`` |rpb|
			übergeben.

		| Existiert eine Ereignisnamengruppe mit dem Namen ``"x"`` und den Ereignisnamen
			``"a"``, ``b"``, ``"c"``, wird die Nachricht *M* auch an alle Empfänger
			mit dem Empfangsmuster
		| |lpb| job = ``"A"``, component = ``"1"``, name = ``"x"`` |rpb|
			übergeben.

		| Hat ein Attribut den Wert ``None``, wird es ignoriert. 
			Das bedeutet, die Nachricht *M* wird auch an alle Empfänger mit dem Empfangsmuster
		| |lpb|  job = ``"A"``, component = ``"1"``, name = ``None`` |rpb|
			übergeben.

		Der Empfänger muss den Aufruf als Funktion unterstützen. 
		Er wird für die Übergabe der Nachricht mit den folgenden vier Parametern aufgerufen:

		``job``
			Der Name des versendenden Jobs
		``component``
			Der Name der versendenden Komponente
		``name``
			Der Name des Ereignisses
		``value``
			Der Nachrichteninhalt

		Die Parameter werden in der dargestellten Reihenfolge als Positionsparameter übergeben.

		.. |lpb| unicode:: U+2329
		.. |rpb| unicode:: U+232A

		*Siehe auch:*
		:py:class:`Slot`,
		:py:class:`Listener`,
		:py:meth:`remove_listener`,
		:py:meth:`send`
		"""
		self._locked(
			self._index.add, listener)

	def remove_listener(self, listener):
		"""
		Entfernt einen Empfänger und sein Empfangsmuster aus dem Nachrichtensystem.

		.. note::
			Es muss das gleiche Objekt übergeben werden, wie an :py:meth:`add_listener`
			übergeben wurde.

		*Siehe auch:*
		:py:meth:`add_listener`
		"""
		self._locked(
			self._index.remove, listener)

	def start(self):
		"""
		Startet das Nachrichtensystem.

		Zur Weiterleitung der Nachrichten wird ein dedizierter Thread gestartet.

		*Siehe auch:*
		:py:meth:`stop`
		"""
		if not self._stopped:
			return
		self.trace("starting blackboard ...")
		self._stopped = False
		self._immediate_stop = False
		self._worker.start()

	def stop(self, immediate = False):
		"""
		Beendet das Nachrichtensystem.

		**Parameter**

		``immediate`` (*optional*)
			``True`` wenn wartende Nachrichten nicht mehr abgearbeitet
			werden sollen, ``False`` wenn erst alle wartenden Nachrichten
			abgearbeitet werden sollen.

		Blockiert solange bis der dedizierte Thread für die Nachrichtenverteilung
		beendet wurde und kehrt erst anschließend zum Aufrufer zurück.

		*Siehe auch:*
		:py:meth:`start`
		"""
		if self._stopped:
			return
		self.trace("stopping blackboard ...")
		self._stopped = True
		self._immediate_stop = immediate
		self._queue_event.set()
		self._worker.join()

	def _queue_worker(self):
		self.trace("... blackboard started")
		while not self._stopped:
			# working the queue until it is empty
			while not self._immediate_stop:
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
		"""
		Sendet eine Nachricht über das Nachrichtensystem.

		**Parameter**

		``job``
			Der versendende Job
		``component``
			Die versendende Komponente
		``name``
			Der Ereignisname
		``value``
			Der Inhalt der Nachricht

		**Beschreibung**

		Die Nachricht wird in die Warteschlange eingestellt.
		Der Aufruf kehrt sofort wieder zum Aufrufer zurück.

		*Siehe auch:*
		:py:meth:`add_listener`
		"""
		if not self._core.is_started:
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
	"""
	Dies ist die Basisklasse für Aufgaben in einer ORBIT-Anwendung.

	**Parameter**

	``name``
		Der Name der Aufgabe. 
		Der Name muss innerhalb der ORBIT-Anwendung eindeutig sein.
	``background``
		``True`` wenn die Aufgabe als Hintergrunddienst laufen soll,
		sonst ``False```.

	**Beschreibung**

	Ein Job wird durch die Zusammenstellung von Komponenten implementiert.
	Wird ein Job aktiviert, werden alle seine Komponenten aktiviert. 
	Wird ein Job deaktiviert, werden alle seine Komponenten deaktiviert.
	Ein aktiver Job kann Nachrichten über das Nachrichtensystem austauschen.
	Ein inaktiver Job kann keine Nachrichten senden oder empfangen.

	.. note::
		Die :py:class:`Job`-Klasse sollte nicht direkt verwendet werden.
		Statt dessen sollten die abgeleiteten Klassen :py:class:`Service`
		und :py:class:`App` verwendet werden.

	*Siehe auch:*
	:py:meth:`add_component`,
	:py:meth:`remove_component`
	"""

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
		"""
		Legt fest, ob Nachverfolgungsmeldungen für diesen Job 
		auf der Konsole ausgegeben werden sollen.

		Mögliche Werte sind ``True`` oder ``False``.

		*Siehe auch:*
		:py:meth:`trace`
		"""
		return self._tracing
	@tracing.setter
	def tracing(self, value):
		self._tracing = value
	
	def trace(self, text):
		"""
		Schreibt eine Nachverfolgungsmeldung mit dem Ursprung ``Service <Name>``
		oder ``App <Name>`` auf die Konsole.
		"""
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
		"""
		Legt fest, ob über das Nachrichtensystem versendete
		Nachrichten auf der Konsole protokolliert werden sollen.

		Mögliche Werte sind ``True`` oder ``False``.

		*Siehe auch:*
		:py:meth:`send`
		"""
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
		"""
		Gibt den Namen des Jobs zurück.
		"""
		return self._name

	@property
	def core(self):
		"""
		Gibt eine Referenz auf den Anwendungskern zurück.
		Wenn der Job nicht installiert ist, wird ``None`` zurück gegeben.

		*Siehe auch:*
		:py:class:`Core`,
		:py:meth:`Core.install`
		"""
		return self._core

	def on_install(self, core):
		"""
		Wird aufgerufen, wenn der Job installiert wird.

		**Parameter**

		``core``
			Eine Referenz auf den Anwendungskern.

		.. note::
			Kann von abgeleiteten Klassen überschrieben werden.
			Eine überschreibende Methode muss jedoch die Implementierung
			der Elternklasse aufrufen.

		*Siehe auch:*
		:py:meth:`Core.install`
		"""
		if self._core:
			raise AttributeError("the job is already associated with a core")
		self._core = core

	def on_uninstall(self):
		"""
		Wird aufgerufen, wenn der Job deinstalliert wird.

		.. note::
			Kann von abgeleiteten Klassen überschrieben werden.
			Eine überschreibende Methode muss jedoch die Implementierung
			der Elternklasse aufrufen.

		*Siehe auch:*
		:py:meth:`Core.uninstall`
		"""
		self._core = None

	@property
	def configuration(self):
		"""
		Gibt die Anwendungskonfiguration zurück.
		Wenn der Job nicht installiert ist, wird ``None`` zurück gegeben.
		"""
		if self._core:
			return self._core.configuration
		else:
			return None

	@property
	def background(self):
		"""
		Legt fest, ob der Job als Hintergrunddienst
		ausgeführt wird oder als Vordergrund-App.

		Mögliche Werte sind ``True`` für Hintergrunddienst 
		oder ``False`` für Vordergrund-App.
		"""
		return self._background

	@property
	def active(self):
		"""
		Gibt einen Wert zurück oder legt ihn fest, der angibt, ob der Job aktiv ist.

		.. note::
			Dieses Attribut sollte nicht direkt gesetzt werden.
			Statt dessen sollte :py:meth:`Core.activate` und 
			:py:meth:`Core.deactivate` verwendet werden.

		*Siehe auch:*
		:py:meth:`Core.activate`,
		:py:meth:`Core.deactivate`,
		:py:meth:`on_activated`,
		:py:meth:`on_deactivated`
		"""
		return self._active
	@active.setter
	def active(self, value):
		if self._active == value:
			return
		if self._core == None:
			raise AttributeError("the job is not installed in any core")
		if value and not self._core.is_started:
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
		"""
		Wird aufgerufen, wenn der Job aktiviert wird.

		.. note::
			Kann von abgeleiteten Klassen überschrieben werden.
			Eine überschreibende Methode muss jedoch die Implementierung
			der Elternklasse aufrufen.

		*Siehe auch:*
		:py:attr:`active`,
		:py:meth:`Core.activate`
		"""
		def enabler(component):
			component.enabled = True
		self.for_each_component(lambda c: c.on_job_activated())
		self.for_each_component(enabler)

	def on_deactivated(self):
		"""
		Wird aufgerufen, wenn der Job deaktiviert wird.

		.. note::
			Kann von abgeleiteten Klassen überschrieben werden.
			Eine überschreibende Methode muss jedoch die Implementierung
			der Elternklasse aufrufen.

		*Siehe auch:*
		:py:attr:`active`,
		:py:meth:`Core.deactivate`
		"""
		def disabler(component):
			component.enabled = False
		self.for_each_component(disabler)
		self.for_each_component(lambda c: c.on_job_deactivated())

	@property
	def components(self):
		"""
		Gibt ein Dictionary mit allen Komponenten des Jobs zurück.
		Die Namen der Komponenten werden als Schlüssel verwendet.
		Die Komponenten selbst sind die Werte.

		*Siehe auch:*
		:py:meth:`add_component`,
		:py:meth:`remove_component`
		"""
		return self._components

	def add_component(self, component):
		"""
		Fügt dem Job eine Komponente hinzu.

		*Siehe auch:*
		:py:meth:`remove_component`,
		:py:attr:`components`
		"""
		if component.name in self._components:
			self.remove_component(self._components[component.name])
		self._components[component.name] = component
		component.on_add_component(self)
		self.trace("added component %s" % component.name)
		if self._active:
			component.enabled = True

	def remove_component(self, component):
		"""
		Entfernt eine Komponente aus dem Job.

		*Siehe auch:*
		:py:meth:`add_component`,
		:py:attr:`components`
		"""
		if component.name not in self._components:
			raise AttributeError("the given component is not associated with this job")
		if component.enabled:
			component.enabled = False
			component.on_remove_component()
		del(self._components[component.name])
		self.trace("removed component %s" % component.name)

	def for_each_component(self, f):
		"""
		Führt die übergebene Funktion für jede Komponente des Jobs aus.

		*Siehe auch:*
		:py:attr:`components`
		"""
		for component in self._components.values():
			f(component)

	def on_core_started(self):
		"""
		Wird aufgerufen, wenn der Anwendungskern gestartet wurde.
		
		.. note::
			Kann von abgeleiteten Klassen überschrieben werden.
			Eine überschreibende Methode muss jedoch die Implementierung
			der Elternklasse aufrufen.

		*Siehe auch:*
		:py:meth:`Core.start`
		"""
		self.for_each_component(
			lambda c: c.on_core_started())

	def on_core_stopped(self):
		"""
		Wird aufgerufen, wenn der Anwendungskern gestoppt wird.
		
		.. note::
			Kann von abgeleiteten Klassen überschrieben werden.
			Eine überschreibende Methode muss jedoch die Implementierung
			der Elternklasse aufrufen.

		*Siehe auch:*
		:py:meth:`Core.stop`
		"""
		self.for_each_component(
			lambda c: c.on_core_stopped())

	def add_listener(self, listener):
		"""
		Richtet einen Nachrichtenempfänger für das Nachrichtensystem ein.

		Als Empfänger wird üblicherweise ein :py:class:`Listener`-Objekt übergeben.

		*Siehe auch:*
		:py:class:`Listener`,
		:py:meth:`Blackboard.add_listener`,
		:py:meth:`remove_listener`,
		:py:meth:`send`
		"""
		if listener in self._listeners:
			return
		listener.receiver = self.name
		self._listeners.append(listener)
		if self._active:
			self._core.blackboard.add_listener(listener)

	def remove_listener(self, listener):
		"""
		Meldet einen Nachrichtenempfänger vom Nachrichtensystem ab.

		.. note::
			Es muss das selbe Empfängerobjekt übergeben werden,
			wie an :py:meth:`add_listener` übergeben wurde.

		*Siehe auch:*
		:py:meth:`Blackboard.remove_listener`,
		:py:meth:`add_listener`,
		:py:meth:`send`
		"""
		if listener not in self._listeners:
			return
		if self._active:
			self._core.blackboard.remove_listener(listener)
		self._listeners.remove(listener)

	def send(self, name, value = None):
		"""
		Versendet eine Nachricht über das Nachrichtensystem.

		**Parameter**

		``name``
			Der Ereignisname für die Nachricht.
		``value`` (*optional*)
			Der Inhalt der Nachricht. Das kann ein beliebiges Objekt sein.

		**Beschreibung**

		Die Methode übergibt die Nachricht an das Nachrichtensystem und kehrt
		sofort zum Aufrufer zurück. 
		Die Nachricht wird asynchron an die Empfänger übermittelt. 
		Als Absender-Job wird der Name dieses Jobs eingetragen. 
		Als Absenderkomponente wird ``JOB`` eingetragen.

		*Siehe auch:*
		:py:meth:`add_listener`,
		:py:meth:`remove_listener`,
		:py:meth:`Blackboard.send`
		"""
		if not self._active:
			raise AttributeError("this job is not active")
		self.event_trace(name, value)
		self._core.blackboard.send(self.name, 'JOB', name, value)


class App(Job):
	"""
	Diese Klasse implementiert eine Vordergrundaufgabe in einer ORBIT-Anwendung.

	**Parameter**

	``name``
		Der Name der Aufgabe. Der Name muss innerhalb der ORBIT-Anwendung eindeutig sein.
	``in_history`` (*optional*)
		Gibt an, ob diese App in der App-History berücksichtigt werden soll.
		(*Siehe auch:* :py:meth:`Core.activate`, :py:meth:`Core.deactivate`)
		Mögliche Werte sind ``True`` wenn die App in der App-History 
		vermerkt werden soll, sonst ``False``.
	``activator`` (*optional*)
		Slots für die Aktivierung der App.
		Ein einzelner :py:class:`Slot`, eine Sequenz von Slot-Objekten oder ``None``.
		(*Siehe auch:* :py:meth:`add_activator`)
	``deactivator`` (*optional*)
		Slots für die Deaktivierung der App.
		Ein einzelner :py:class:`Slot`, eine Sequenz von Slot-Objekten oder ``None``.
		(*Siehe auch:* :py:meth:`add_deactivator`)
	
	**Beschreibung**

	Diese Klasse erbt von :py:class:`Job` und implementiert damit eine Aufgabe 
	durch die Kombination von verschiedenen Komponenten.
	Diese Klasse kann direkt instanziert werden oder es kann eine Klasse
	abgeleitet werden.

	*Siehe auch:*
	:py:class:`Job`,
	:py:meth:`add_component`,
	:py:meth:`Core.install`
	"""

	def __init__(self, name, in_history = False, 
		activator = None, deactivator = None):
		super().__init__(name, False)
		self._activators = MultiListener("%s Activator" % name, self._process_activator)
		self._deactivators = MultiListener("%s Deactivator" % name, self._process_deactivator)
		self._in_history = in_history

		if activator:
			try:
				for a in activator:
					self.add_activator(a)
			except TypeError:
				self.add_activator(activator)

		if deactivator:
			try:
				for d in deactivator:
					self.add_deactivator(d)
			except TypeError:
				self.add_deactivator(deactivator)

	@property
	def in_history(self):
		"""
		Gibt einen Wert zurück, der angibt, ob diese App in der App-History
		vermerkt wird oder nicht.

		Mögliche Werte sind ``True`` oder ``False``.

		*Siehe auch:*
		:py:meth:`Core.activate`,
		:py:meth:`Core.deactivate`
		"""
		return self._in_history

	def _process_activator(self, *args):
		self.trace("activating app %s, caused by event" % self.name)
		self._core.activate(self)

	def _process_deactivator(self, *args):
		self.trace("deactivating app %s, caused by event" % self.name)
		self._core.deactivate(self)

	def add_activator(self, slot):
		"""
		Fügt einen :py:class:`Slot` für die Aktivierung der App hinzu.

		Sobald eine Nachricht über das Nachrichtensystem gesendet
		wird, welche dem Empfangsmuster des übergebenen Slots entspricht,
		wird die App aktiviert.

		*Siehe auch:*
		:py:meth:`remove_activator`,
		:py:meth:`add_deactivator`
		"""
		self._activators.add_slot(slot)

	def remove_activator(self, slot):
		"""
		Entfernt einen :py:class:`Slot` für die Aktivierung der App.

		.. note::
			Es muss die selbe Referenz übergeben werden, wie an
			:py:meth:`add_activator` übergeben wurde.

		*Siehe auch:*
		:py:meth:`add_activator`
		"""
		self._activators.remove_slot(slot)

	def add_deactivator(self, slot):
		"""
		Fügt einen :py:class:`Slot` für die Deaktivierung der App hinzu.

		Sobald eine Nachricht über das Nachrichtensystem gesendet
		wird, welche dem Empfangsmuster des übergebenen Slots entspricht,
		wird die App deaktiviert.

		*Siehe auch:*
		:py:meth:`remove_deactivator`,
		:py:meth:`add_activator`
		"""
		self._deactivators.add_slot(slot)

	def remove_deactivator(self, slot):
		"""
		Entfernt einen :py:class:`Slot` für die Deaktivierung der App.

		.. note::
			Es muss die selbe Referenz übergeben werden, wie an
			:py:meth:`add_deactivator` übergeben wurde.

		*Siehe auch:*
		:py:meth:`add_deactivator`
		"""
		self._deactivators.remove_slot(slot)
	
	def on_install(self, core):
		"""
		Wird aufgerufen, wenn die App installiert wird.

		.. note::
			Kann von abgeleiteten Klassen überschrieben werden.
			Eine überschreibende Methode muss jedoch die Implementierung
			der Elternklasse aufrufen.

		*Siehe auch:*
		:py:meth:`Core.install`,
		:py:meth:`Job.on_install`
		"""
		super().on_install(core)
		self._activators.activate(self._core.blackboard)
		self._deactivators.activate(self._core.blackboard)

	def on_uninstall(self):
		"""
		Wird aufgerufen, wenn die App deinstalliert wird.

		.. note::
			Kann von abgeleiteten Klassen überschrieben werden.
			Eine überschreibende Methode muss jedoch die Implementierung
			der Elternklasse aufrufen.

		*Siehe auch:*
		:py:meth:`Core.uninstall`,
		:py:meth:`Job.on_uninstall`
		"""
		self._deactivators.deactivate(self._core.blackboard)
		self._activators.deactivate(self._core.blackboard)
		super().on_uninstall()

	def activate(self):
		"""
		Aktiviert die App.

		*Siehe auch:*
		:py:meth:`Core.activate`
		"""
		if not self.core:
			raise AttributeError("the job is not associated with a core")
		if self.active:
			raise AttributeError("the job is already activated")
		self.core.activate(self)

	def deactivate(self):
		"""
		Deaktiviert die App.

		*Siehe auch:*
		:py:meth:`Core:deactivate`
		"""
		if not self.core:
			raise AttributeError("the job is not associated with a core")
		if not self.active:
			raise AttributeError("the job is not activated")
		self.core.deactivate(self)


class Service(Job):
	"""
	Diese Klasse implementiert eine Hintergrundaufgabe in einer ORBIT-Anwendung.

	**Parameter**

	``name``
		Der Name der Aufgabe. Der Name muss innerhalb der ORBIT-Anwendung eindeutig sein.

	**Beschreibung**

	Hintergrundaufgaben werden üblicherweise direkt mit dem Starten der ORBIT-Anwendung
	aktiviert und erst mit dem Beenden der Anwendung wieder deaktiviert.

	Diese Klasse erbt von :py:class:`Job` und implementiert damit eine Aufgabe 
	durch die Kombination von verschiedenen Komponenten.
	Diese Klasse kann direkt instanziert werden oder es kann eine Klasse
	abgeleitet werden.

	*Siehe auch:*
	:py:class:`Job`,
	:py:meth:`add_component`,
	:py:meth:`Core.install`
	"""

	def __init__(self, name):
		super().__init__(name, True)


class Component:
	"""
	Diese Klasse implementiert eine Komponente als Baustein für eine Aufgabe.

	**Parameter**

	``name``
		Der Name der Komponente. Der Name muss innerhalb der Aufgabe eindeutig sein.

	**Beschreibung**

	Komponenten sind der typische Weg, in einer ORBIT-Anwendung, mit einem
	TinkerForge-Brick(let) zu kommunizieren.
	Eine Komponente wird implementiert, indem eine Klasse von 
	:py:class:`Component` abgeleitet wird und im Konstruktur 
	durch den Aufruf von :py:meth:`add_device_handle`
	Geräteanforderungen eingerichtet werden.

	Komponenten können über das Nachrichtensystem kommunizieren.
	Dazu können mit dem Aufruf von :py:meth:`add_listener`
	Empfänger eingerichtet und mit dem Aufruf von :py:meth:`send`
	Nachrichten versandt werden.

	*Siehe auch:*
	:py:meth:`Job.add_component`,
	:py:meth:`add_device_handle`,
	:py:meth:`add_listener`,
	:py:meth:`send`
	"""

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
		"""
		Legt fest, ob Nachverfolgungsmeldungen für diese Komponente
		auf der Konsole ausgegeben werden sollen.

		Mögliche Werte sind ``True`` oder ``False``.

		*Siehe auch:*
		:py:meth:`trace`
		"""
		return self._tracing
	@tracing.setter
	def tracing(self, enabled):
		self._tracing = enabled

	def trace(self, text):
		"""
		Schreibt eine Nachverfolgungsmeldung mit dem Ursprung 
		``Component <Job> <Name>`` auf die Konsole.
		"""
		if self._tracing == True or \
			(self._tracing != False and \
			 self._job and \
			 self._job._core.configuration.component_tracing):

			_trace(text, "Component %s %s" % 
				(self._job.name if self._job else "NO_JOB", self._name))

	@property
	def event_tracing(self):
		"""
		Legt fest, ob über das Nachrichtensystem versendete
		Nachrichten auf der Konsole protokolliert werden sollen.

		Mögliche Werte sind ``True`` oder ``False``.

		*Siehe auch:*
		:py:meth:`send`
		"""
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
		"""
		Gibt den Namen der Komponente zurück.
		"""
		return self._name

	@property
	def job(self):
		"""
		Gibt den Eltern-Job oder ``None`` zurück.

		*Siehe auch:*
		:py:meth:`Job.add_component`
		"""
		return self._job

	def on_add_component(self, job):
		"""
		Wird aufgerufen, wenn die Komponente einem Job hinzugefügt wird.

		**Parameter**

		``job``
			Eine Referenz auf den Job.

		.. note::
			Kann von abgeleiteten Klassen überschrieben werden.
			Eine überschreibende Methode muss jedoch die Implementierung
			der Elternklasse aufrufen.

		*Siehe auch:*
		:py:meth:`Job.add_component`
		"""
		if self._job:
			raise AttributeError("the component is already associated with a job")
		self._job = job

	def on_remove_component(self):
		"""
		Wird aufgerufen, wenn die Komponente aus einem Job entfernt wird.

		.. note::
			Kann von abgeleiteten Klassen überschrieben werden.
			Eine überschreibende Methode muss jedoch die Implementierung
			der Elternklasse aufrufen.

		*Siehe auch:*
		:py:meth:`Job.remove_component`
		"""
		self._job = None

	@property
	def enabled(self):
		"""
		Gibt an oder legt fest, ob die Komponente aktiv ist.

		Mögliche Werte sind ``True`` wenn die Komponente aktiv ist
		und ``False`` wenn die Komponente nicht aktiv ist.

		Alle Komponenten eines Jobs werden beim Aktivieren des Jobs
		automatisch aktiviert und mit dem Deaktivieren des Jobs
		automatisch deaktiviert. Das manuelle Setzen dieses Attributs
		ist i.d.R. nicht notwendig.

		Eine aktive Komponente bekommt Geräte (Bricks und Bricklets) zugeordnet
		und kann Nachrichten empfangen und senden.
		Eine inaktive Komponente bekommt keine Geräte zugeordnet und
		erhält auch keine Nachrichten vom Nachrichtensystem zugestellt.
		"""
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
		"""
		Wird aufgerufen, wenn der Anwendungskern gestartet wurde.
		
		.. note::
			Kann von abgeleiteten Klassen überschrieben werden.

		*Siehe auch:*
		:py:meth:`Core.start`
		"""
		# can be overriden in sub classes
		pass

	def on_core_stopped(self):
		"""
		Wird aufgerufen, wenn der Anwendungskern gestoppt wird.
		
		.. note::
			Kann von abgeleiteten Klassen überschrieben werden.

		*Siehe auch:*
		:py:meth:`Core.stop`
		"""
		# can be overriden in sub classes
		pass

	def on_job_activated(self):
		"""
		Wird aufgerufen, wenn der Eltern-Job der Komponente aktiviert wird.

		.. note::
			Kann von abgeleiteten Klassen überschrieben werden.

		*Siehe auch:*
		:py:attr:`Job.active`,
		:py:meth:`Core.activate`
		"""
		# can be overriden in sub classes
		pass

	def on_job_deactivated(self):
		"""
		Wird aufgerufen, wenn der Eltern-Job der Komponente deaktiviert wird.

		.. note::
			Kann von abgeleiteten Klassen überschrieben werden.

		*Siehe auch:*
		:py:attr:`Job.active`,
		:py:meth:`Core.deactivate`
		"""
		# can be overriden in sub classes
		pass

	def on_enabled(self):
		"""
		Wird aufgerufen, wenn die Komponente aktiviert wird.

		.. note::
			Kann von abgeleiteten Klassen überschrieben werden.

		*Siehe auch:*
		:py:attr:`enabled`
		"""
		# can be overriden in sub classes
		pass

	def on_disabled(self):
		"""
		Wird aufgerufen, wenn die Komponente deaktiviert wird.

		.. note::
			Kann von abgeleiteten Klassen überschrieben werden.

		*Siehe auch:*
		:py:attr:`enabled`
		"""
		# can be overriden in sub classes
		pass

	def add_device_handle(self, device_handle):
		"""
		Richtet eine Geräteanforderung ein.

		Als Parameter wird ein :py:class:`SingleDeviceHandle` oder 
		ein :py:class:`MultiDeviceHandle` übergeben.

		*Siehe auch:*
		:py:meth:`remove_device_handle`
		"""
		if device_handle in self._device_handles:
			return
		self._device_handles.append(device_handle)
		if self._enabled:
			self._job._core.device_manager.add_handle(device_handle)

	def remove_device_handle(self, device_handle):
		"""
		Entfernt eine Geräteanforderung.

		Als Parameter wird ein :py:class:`SingleDeviceHandle` oder 
		ein :py:class:`MultiDeviceHandle` übergeben.

		.. note::
			Es muss die selbe Referenz übergeben werden, wie an
			:py:meth:`add_device_handle` übergeben wurde.

		*Siehe auch:*
		:py:meth:`add_device_handle`
		"""
		if device_handle not in self._device_handles:
			return
		if self._enabled:
			self._job._core.device_manager.remove_handle(device_handle)
		device_handle.on_remove_device_handle()
		self._device_handles.remove(device_handle)

	def add_listener(self, listener):
		"""
		Richtet einen Nachrichtenempfänger für das Nachrichtensystem ein.

		Als Empfänger wird üblicherweise ein :py:class:`Listener`-Objekt übergeben.

		*Siehe auch:*
		:py:class:`Listener`,
		:py:meth:`Blackboard.add_listener`,
		:py:meth:`remove_listener`,
		:py:meth:`send`
		"""
		if listener in self._listeners:
			return
		self._listeners.append(listener)
		if self._enabled:
			listener.receiver = "%s, %s" % (self._job.name, self.name)
			self._job._core.blackboard.add_listener(listener)

	def remove_listener(self, listener):
		"""
		Meldet einen Nachrichtenempfänger vom Nachrichtensystem ab.

		.. note::
			Es muss das selbe Empfängerobjekt übergeben werden,
			wie an :py:meth:`add_listener` übergeben wurde.

		*Siehe auch:*
		:py:meth:`Blackboard.remove_listener`,
		:py:meth:`add_listener`,
		:py:meth:`send`
		"""
		if listener not in self._listeners:
			return
		if self._enabled:
			self._job._core.blackboard.remove_listener(listener)
		self._listeners.remove(listener)

	def send(self, name, value = None):
		"""
		Versendet eine Nachricht über das Nachrichtensystem.

		**Parameter**

		``name``
			Der Ereignisname für die Nachricht.
		``value`` (*optional*)
			Der Inhalt der Nachricht. Das kann ein beliebiges Objekt sein.

		**Beschreibung**

		Die Methode übergibt die Nachricht an das Nachrichtensystem und kehrt
		sofort zum Aufrufer zurück. 
		Die Nachricht wird asynchron an die Empfänger übermittelt. 
		Als Absender-Job wird der Name des Eltern-Jobs dieser Komponente eingetragen. 
		Als Absenderkomponente wird der Name dieser Komponente eingetragen.

		*Siehe auch:*
		:py:meth:`add_listener`,
		:py:meth:`remove_listener`,
		:py:meth:`Blackboard.send`
		"""
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
