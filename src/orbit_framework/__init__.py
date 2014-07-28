# coding=utf-8

## ORBIT ist ein Python-Framework für TinkerForge-Anwendungen
## Copyright (C) 2014 Tobias Kiertscher <dev@mastersign.de>
##
## This program is free software: you can redistribute it and/or modify
## it under the terms of the GNU Lesser General Public License as 
## published by the Free Software Foundation, either version 3 
## of the License, or (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
## 
## You should have received a copy of the GNU (Lesser) General 
## Public License along with this program. 
## If not, see <http://www.gnu.org/licenses/>.

# Module orbit_framework

"""
Diese Modul enthält die wichtigsten Klassen für die Entwicklung einer
ORBIT-Anwendung. 
Eine ORBIT-Anwendung wird von einem :py:class:`Core` verwaltet
und kann mehrere :py:class:`Job`-Objekte enthalten.
Jeder :py:class:`Job` fasst eine Gruppe von :py:class:`Component`-Objekten zusammen.
Ein :py:class:`Job` ist entweder eine :py:class:`App` oder ein :py:class:`Service`.

Die TinkerForge-Bricklets werden durch den :py:class:`.devices.DeviceManager` verwaltet
und den :py:class:`Component`-Objekten über :py:class:`.devices.DeviceHandle`-Objekte zugeordnet.

:py:class:`Component`- und :py:class:`Job`-Objekte
kommunizieren asynchron über das ORBIT-Nachrichtensystem welches durch
die Klasse :py:class:`.messaging.MessageBus` implementiert wird.

:py:class:`Component`- und :py:class:`Job`-Objekte können jederzeit Nachrichten
senden. Diese Nachrichten werden in einer Warteschlange abgelegt und in einem 
dedizierten Nachrichten-Thread an die Empfänger versandt
(:py:meth:`Job.send`, :py:meth:`Component.send`).

Für den Empfang von Nachrichten werden :py:class:`.messaging.Listener`-Objekte verwendet.
Ein :py:class:`.messaging.Listener` bindet ein Empfangsmuster/-filter an ein Callback
(:py:class:`.messaging.Slot`, :py:meth:`Job.add_listener`, :py:meth:`Component.add_listener`).
Wird eine Nachricht über das Nachrichtensystem versandt, welches dem Empfangsmuster
entspricht, wird das Callback des Empfängers aufgerufen.

Das Modul enthält die folgenden Klassen:

- :py:class:`Core`
- :py:class:`Job`
- :py:class:`App`
- :py:class:`Service`
- :py:class:`Component`
"""

from sys import stdout
from datetime import datetime
from traceback import print_exc
from threading import Thread, Lock, Event
from . import setup
from .devices import DeviceManager
from .messaging import MessageBus, MultiListener

__all__ = ['setup', 'tools', 'index', 'messaging', 'devices']

def _trace(text, source):
	stamp = datetime.now().strftime('[%Y-%m-%d %H-%M-%S]')
	msg = '%s %s: %s\n' % (stamp, source, text)
	stdout.write(msg)
	stdout.flush()


class Core(object):
	"""
	Diese Klasse repräsentiert den Kern einer ORBIT-Anwendung.

	**Parameter**

	``config`` (*optional*)
		Die Konfiguration für die ORBIT-Anwendung. 
		Eine Instanz der Klasse :py:class:`.setup.Configuration`.

	**Beschreibung**

	Diese Klasse ist verantwortlich für die Einrichtung des Nachrichtensystems
	und der Geräteverwaltung. Des Weiteren verwaltet sie alle Dienste
	und Apps, die in der ORBIT-Anwendung verwendet werden.

	Für die Einrichtung einer Anwendung wird zunächst eine Instanz von
	:py:class:`Core` erzeugt. Dabei kann optional
	eine benutzerdefinierte Konfiguration (:py:class:`.setup.Configuration`)
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
		self._message_bus = MessageBus(self)

		self._jobs = {}
		self._default_application = None
		self._current_application = None
		self._application_history = []

		self._stopper = MultiListener('Core Stopper', self._core_stopper)
		self._stopper.activate(self._message_bus)

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
	def _trace_function(self):
		return _trace

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
		Gibt die ORBIT-Anwendungskonfiguration zurück.
		(*schreibgeschützt*)

		*Siehe auch:*
		:py:class:`.setup.Configuration`
		"""
		return self._configuration

	@property
	def device_manager(self):
		"""
		Gibt den Gerätemanager zurück.
		(*schreibgeschützt*)

		*Siehe auch:*
		:py:class:`.devices.DeviceManager`
		"""
		return self._device_manager

	@property
	def message_bus(self):
		"""
		Gibt das Nachrichtensystem zurück.
		(*schreibgeschützt*)

		*Siehe auch:*
		:py:class:`.messaging.MessageBus`
		"""
		return self._message_bus

	@property
	def jobs(self):
		"""
		Gibt ein Dictionary mit allen installierten Jobs zurück.
		(*schreibgeschützt*)
		Der Schlüssel ist der Name des Jobs und der Wert ist der Job selbst.

		*Siehe auch:*
		:py:class:`Job`,
		:py:meth:`install`,
		:py:meth:`uninstall`
		"""
		return self._jobs

	@property
	def default_application(self):
		"""
		Gibt die Standard-App zurück oder legt sie fest.

		*Siehe auch:*
		:py:class:`App`
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
		self._message_bus.start()

		if not self._device_manager.start():
			self.message_bus.stop()
			self._is_started = False
			self._stop_event.set()
			return

		self.for_each_job(
			lambda j: j.on_core_started())

		self.trace("... started")

		def activator(job):
			if job.background:
				job.active = True
			elif job == self.default_application:
				self.activate(job)

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
		self._message_bus.stop()
		self._is_started = False
		self.trace("... stopped")
		self._stop_event.set()

	def _core_stopper(self, *args):
		self.trace("core stopping, caused by event")
		Thread(target = self.stop).start()

	def add_stopper(self, slot):
		"""
		Fügt einen :py:class:`.messaging.Slot` hinzu, der das Stoppen der ORBIT-Anwendung
		veranlassen soll.

		*Siehe auch:*
		:py:meth:`remove_stopper`
		"""
		self._stopper.add_slot(slot)

	def remove_stopper(self, slot):
		"""
		Entfernt einen :py:class:`.messaging.Slot`, der das Stoppen der ORBIT-Anwendung
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
			:py:class:`.messaging.Listener` aufgerufen werden, 
			da sie andernfalls das Nachrichtensystem der ORBIT-Anwendung blockiert.

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

		Ein Job kann immer nur in einer ORBIT-Anwendung installiert werden.
		Wird ein Job, der bereits in einer Anwendung installiert ist, 
		an :py:meth:`install` übergeben, geschieht nichts.

		*Siehe auch:*
		:py:meth:`uninstall`,
		:py:attr:`jobs`,
		:py:class:`App`,
		:py:class:`Service`
		"""
		if job.core:
			return
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

		Wird ein Job an :py:meth:`install` übergeben, 
		der nicht in dieser ORBIT-Anwendung installiert ist,
		geschieht nicht.

		*Siehe auch:*
		:py:meth:`install`,
		:py:attr:`jobs`
		"""
		if job.name not in self._jobs:
			return
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
			if application not in self._jobs.values():
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


class Job(object):
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
				self._core.message_bus.add_listener(listener)
			self.on_activated()
			self.trace("... activated")
		else:
			self.trace("deactivating ...")
			for listener in self._listeners:
				self._core.message_bus.remove_listener(listener)
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
		:py:meth:`remove_component`,
		:py:class:`Component`
		"""
		return self._components

	def add_component(self, component):
		"""
		Fügt dem Job eine Komponente hinzu.

		*Siehe auch:*
		:py:meth:`remove_component`,
		:py:attr:`components`,
		:py:class:`Component`
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

		Als Empfänger wird üblicherweise ein :py:class:`.messaging.Listener`-Objekt übergeben.

		*Siehe auch:*
		:py:class:`.messaging.Listener`,
		:py:meth:`.messaging.MessageBus.add_listener`,
		:py:meth:`remove_listener`,
		:py:meth:`send`
		"""
		if listener in self._listeners:
			return
		listener.receiver = self.name
		self._listeners.append(listener)
		if self._active:
			self._core.message_bus.add_listener(listener)

	def remove_listener(self, listener):
		"""
		Meldet einen Nachrichtenempfänger vom Nachrichtensystem ab.

		.. note::
			Es muss das selbe Empfängerobjekt übergeben werden,
			wie an :py:meth:`add_listener` übergeben wurde.

		*Siehe auch:*
		:py:meth:`.messaging.MessageBus.remove_listener`,
		:py:meth:`add_listener`,
		:py:meth:`send`
		"""
		if listener not in self._listeners:
			return
		if self._active:
			self._core.message_bus.remove_listener(listener)
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
		:py:meth:`.messaging.MessageBus.send`
		"""
		if not self._active:
			raise AttributeError("this job is not active")
		self.event_trace(name, value)
		self._core.message_bus.send(self.name, 'JOB', name, value)


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
	:py:meth:`Job.add_component`,
	:py:meth:`Core.install`
	"""

	def __init__(self, name):
		super(Service, self).__init__(name, True)


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
		Ein einzelner :py:class:`.messaging.Slot`, eine Sequenz von Slot-Objekten oder ``None``.
		(*Siehe auch:* :py:meth:`add_activator`)
	``deactivator`` (*optional*)
		Slots für die Deaktivierung der App.
		Ein einzelner :py:class:`.messaging.Slot`, eine Sequenz von Slot-Objekten oder ``None``.
		(*Siehe auch:* :py:meth:`add_deactivator`)
	
	**Beschreibung**

	Diese Klasse erbt von :py:class:`Job` und implementiert damit eine Aufgabe 
	durch die Kombination von verschiedenen Komponenten.
	Diese Klasse kann direkt instanziert werden oder es kann eine Klasse
	abgeleitet werden.

	*Siehe auch:*
	:py:class:`Job`,
	:py:meth:`Job.add_component`,
	:py:meth:`Core.install`
	"""

	def __init__(self, name, in_history = False, 
		activator = None, deactivator = None):
		super(App, self).__init__(name, False)
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
		Fügt einen :py:class:`.messaging.Slot` für die Aktivierung der App hinzu.

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
		Entfernt einen :py:class:`.messaging.Slot` für die Aktivierung der App.

		.. note::
			Es muss die selbe Referenz übergeben werden, wie an
			:py:meth:`add_activator` übergeben wurde.

		*Siehe auch:*
		:py:meth:`add_activator`
		"""
		self._activators.remove_slot(slot)

	def add_deactivator(self, slot):
		"""
		Fügt einen :py:class:`.messaging.Slot` für die Deaktivierung der App hinzu.

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
		Entfernt einen :py:class:`.messaging.Slot` für die Deaktivierung der App.

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
		super(App, self).on_install(core)
		self._activators.activate(self._core.message_bus)
		self._deactivators.activate(self._core.message_bus)

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
		self._deactivators.deactivate(self._core.message_bus)
		self._activators.deactivate(self._core.message_bus)
		super(App, self).on_uninstall()

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
		:py:meth:`Core.deactivate`
		"""
		if not self.core:
			raise AttributeError("the job is not associated with a core")
		if not self.active:
			raise AttributeError("the job is not activated")
		self.core.deactivate(self)


class Component(object):
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
				self._job._core.message_bus.add_listener(listener)
			for device_handle in self._device_handles:
				self._job._core.device_manager.add_handle(device_handle)
			self.on_enabled()
			self.trace("... enabled")
		else:
			self.trace("disabling ...")
			self.on_disabled()
			for listener in self._listeners:
				self._job._core.message_bus.remove_listener(listener)
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

		Als Parameter wird ein :py:class:`.devices.SingleDeviceHandle` oder 
		ein :py:class:`.devices.MultiDeviceHandle` übergeben.

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

		Als Parameter wird ein :py:class:`.devices.SingleDeviceHandle` oder 
		ein :py:class:`.devices.MultiDeviceHandle` übergeben.

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

		Als Empfänger wird üblicherweise ein :py:class:`.messaging.Listener`-Objekt übergeben.

		*Siehe auch:*
		:py:class:`.messaging.Listener`,
		:py:meth:`.messaging.MessageBus.add_listener`,
		:py:meth:`remove_listener`,
		:py:meth:`send`
		"""
		if listener in self._listeners:
			return
		self._listeners.append(listener)
		if self._enabled:
			listener.receiver = "%s, %s" % (self._job.name, self.name)
			self._job._core.message_bus.add_listener(listener)

	def remove_listener(self, listener):
		"""
		Meldet einen Nachrichtenempfänger vom Nachrichtensystem ab.

		.. note::
			Es muss das selbe Empfängerobjekt übergeben werden,
			wie an :py:meth:`add_listener` übergeben wurde.

		*Siehe auch:*
		:py:meth:`.messaging.MessageBus.remove_listener`,
		:py:meth:`add_listener`,
		:py:meth:`send`
		"""
		if listener not in self._listeners:
			return
		if self._enabled:
			self._job._core.message_bus.remove_listener(listener)
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
		:py:meth:`.messaging.MessageBus.send`
		"""
		if not self._enabled:
			raise AttributeError("this component is not enabled")
		self.event_trace(name, value)
		self._job._core.message_bus.send(self._job.name, self.name, name, value)

