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

# Module orbit_framework.messaging

"""
Dieses Modul implementiert das Nachrichtensystem von ORBIT.

Das Modul umfasst die folgenden Klassen:

- :py:class:`MessageBus`
- :py:class:`Slot`
- :py:class:`Listener`
- :py:class:`MultiListener`
"""

from collections import deque
from threading import Thread, Lock, Event
from .index import MultiLevelReverseIndex


class MessageBus(object):
	"""
	Diese Klasse implementiert das ORBIT-Nachrichtensystem.

	**Parameter**

	``core``
		Ein Verweis auf den Anwendungskern der ORBIT-Anwendung.
		Eine Instanz der Klasse :py:class:`Core`.

	**Beschreibung**

	Das Nachrichtensystem funktioniert nach dem Broadcast-Prinzip.
	Nachrichten werden von einem Absender an das Nachrichtensystem
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
		self._worker = Thread(name = 'Orbit MessageBus Queue Worker', target = self._queue_worker)

	def trace(self, text):
		"""
		Schreibt eine Nachverfolgungsmeldung mit dem Ursprung ``MessageBus``
		auf die Konsole.
		"""
		if self._core.configuration.event_tracing:
			self._core._trace_function(text, 'MessageBus')

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
			*M*: job = ``'A'``, component = ``'1'``, name = ``'a'``, value = ...
		| wird an alle Empfänger mit dem Empfangsmuster
		| |lpb| job = ``'A'``, component = ``'1'``, name = ``'a'`` |rpb|
			übergeben.

		| Existiert eine Ereignisnamengruppe mit dem Namen ``'x'`` und den Ereignisnamen
			``'a'``, ``b'``, ``'c'``, wird die Nachricht *M* auch an alle Empfänger
			mit dem Empfangsmuster
		| |lpb| job = ``'A'``, component = ``'1'``, name = ``'x'`` |rpb|
			übergeben.

		| Hat ein Attribut den Wert ``None``, wird es ignoriert. 
			Das bedeutet, die Nachricht *M* wird auch an alle Empfänger mit dem Empfangsmuster
		| |lpb|  job = ``'A'``, component = ``'1'``, name = ``None`` |rpb|
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
		self.trace("starting message bus ...")
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
		self.trace("stopping message bus ...")
		self._stopped = True
		self._immediate_stop = immediate
		self._queue_event.set()
		self._worker.join()

	def _queue_worker(self):
		self.trace("... message bus started")
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

		self.trace("... message bus stopped")

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

		msg = MessageBus.Message(job, component, name, value)
		self._locked(self._queue.append, msg)
		self._queue_event.set()

	class Message(object):
		"""
		Diese Klasse repräsentiert eine Nachricht im Nachrichtensystem.
		Sie wird nur intern verwendet.
		"""

		def __init__(self, job, component, name, value):
			self.job = job
			self.component = component
			self.name = name
			self.value = value


class Slot(object):
	"""
	Diese Klasse repräsentiert ein Empfangsmuster für das Nachrichtensystem.

	**Parameter**

	``job``
		Der Name des versendenen Jobs ein Gruppenname oder ``None``.
	``component``
		Der Name der versendenen Komponente, ``'JOB'``, 
		ein Gruppenname oder ``None``.
	``name``
		Der Ereignisname, ein Gruppenname oder ``None``.
	``predicate`` (*optional*)
		Ein Prädikat als zusätzlicher Filter für Nachrichten.
		Eine Funktion mit der Signatur
		``(job, component, name, value)``, 
		welche die Nachricht entgegennimmt und ``True`` oder ``False``
		zurückgibt.
	``transformation`` (*optional*)
		Eine Funktion, welche den Inhalt der Nachricht entgegennimmt und
		einen umgewandelten Inhalt zurückkgibt.

	**Beschreibung**

	Das Empfangsmuster wird verwendet, um ein Callback für den Nachrichtenempfang
	im Nachrichtensystem zu registrieren. Das Empfangsmuster kann durch einen
	Aufruf der Methode :py:meth:`listener` mit einem Callback zu einem
	Empfänger verknüpft	werden.

	Für die Erzeugung von :py:class:`Slot`-Instanzen gibt es einige statische
	Factory-Methoden: 
	:py:meth:`for_job`, :py:meth:`for_component` und :py:meth:`for_name`.

	*Siehe auch:*
	:py:meth:`listener`,
	:py:class:`Listener`
	"""

	def __init__(self, job, component, name, predicate = None, transformation = None):
		self._job = job
		self._component = component
		self._name = name
		self._predicate = predicate
		self._transformation = transformation

	@property
	def job(self):
		"""
		Gibt den Namen des versendenden Jobs, einen Gruppennamen 
		oder ``None`` zurück.
		"""
		return self._job

	@property
	def component(self):
		"""
		Gibt den Namen der versendenden Komponente, ``'JOB'``, 
		einen Gruppennamen oder ``None`` zurück.
		"""
		return self._component

	@property
	def name(self):
		"""
		Gibt den Ereignisnamen, einen Gruppenname oder ``None`` zurück.
		"""
		return self._name

	@property
	def predicate(self):
		"""
		Gibt das Filterprädikat oder ``None`` zurück.
		"""
		return self._predicate

	@property
	def transformation(self):
		"""
		Gibt die Transformationsfunktion für den Nachrichteninhalt
		oder ``None`` zurück.
		"""
		return self._transformation

	def for_job(job):
		"""
		Erzeugt ein Empfangsmuster, welches auf alle Nachrichten von einem
		Job passt.
		Es kann auch ein Gruppenname übergegen werden.
		"""
		return Slot(job, None, None)

	def for_component(job, component):
		"""
		Erzeugt ein Empfangsmuster, welches auf die Nachrichten
		aller Komponenten mit dem übergegebenen Namen passt.
		Es kann auch ein Gruppenname übergegen werden.
		"""
		return Slot(job, component, None)

	def for_name(name):
		"""
		Erzeugt ein Empfangsmuster, welches auf alle Nachrichten
		für das übergebene Ereignis passt.
		Es kann auch ein Gruppenname übergegen werden.
		"""
		return Slot(None, None, name)

	def listener(self, callback):
		"""
		Erzeugt mit dem übergebenen Callback einen Empfänger.

		*Siehe auch:*
		:py:class:`Listener`
		"""
		return Listener(callback, self)

	def __str__(self):
		return "Slot(job = %s, component = %s, name = %s, predicate: %s, transformation: %s)" \
			% (self._job, self._component, self._name,
			   self._transform != None, self._predicate != None)


class Listener(object):
	"""
	Diese Klasse repräsentiert einen Empfänger für das Nachrichtensystem.

	**Parameter**

	``callback``
		Das Callback welches beim Eintreffen einer passenden Nachricht
		aufgerufen werden soll. Die Funktion muss die folgende
		Signatur besitzen: ``(job, component, name, value)``.
		Wird eine dynamische Methode statt einer statischen Funktion übergeben,
		muss die Methode die folgende Signatur besitzen:
		``(self, job, component, name, value)``.
	``slot``
		Ein Empfangsmuster für die Filterung der Nachrichten.

	Ein Empfänger kann mit Hilfe der folgenden Methoden für den
	Nachrichtenempfang registriert werden:
	:py:meth:`MessageBus.add_listener`, :py:meth:`Job.add_listener` und
	:py:meth:`Component.add_listener`.

	*Siehe auch:*
	:py:class:`Slot`,
	:py:class:`MessageBus`
	"""

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
		"""
		Gibt den Namen des versendenden Jobs, einen Gruppennamen 
		oder ``None`` zurück.
		"""
		return self._slot.job

	@property
	def component(self):
		"""
		Gibt den Namen der versendenden Komponente, ``'JOB'``, 
		einen Gruppennamen oder ``None`` zurück.
		"""
		return self._slot.component

	@property
	def name(self):
		"""
		Gibt den Ereignisnamen, einen Gruppenname oder ``None`` zurück.
		"""
		return self._slot.name

	@property
	def receiver(self):
		"""
		Gibt die Bezeichnung des Empfängers zurück.

		Die Bezeichnung wird beim Protokollieren der Nachrichten
		verwendet, um den Weg der Nachrichten kenntlich zu machen.

		Werden die Methoden :py:meth:`Job.add_listener` oder 
		:py:meth:`Component.add_listener` verwendet, wird dieses Attribut
		automatisch gesetzt. Wird der Empfänger direkt mit
		:py:meth:`MessageBus.add_listener` registriert,
		sollte dieses Attribut vorher gesetzt werden um den Empfänger
		zu bezeichnen.
		"""
		return self._receiver
	@receiver.setter
	def receiver(self, value):
		self._receiver = value

	def __str__(self):
		return "Listener(job = %s, component = %s, name = %s, predicate: %s, transform: %s, receiver = %s)" \
			% (self._slot.job, self._slot.component, self._slot.name,
			   self._slot.transformation != None, self._slot.predicate != None, 
			   self._receiver)


class MultiListener(object):
	"""
	Diese Klasse implementiert einen Mehrfachempfänger.
	Das ist ein Mechanismus für den Empfang	von Nachrichten über das Nachrichtensystem, 
	bei dem mehrere Empfangsmuster mit einem Callback verknüpft	werden.

	**Parameter**

	``name``
		Der Name des Empfängers.
	``callback``
		Eine Funktion die bei einem Nachrichtenempfang aufgerufen werden soll.
		Die Funktion muss die Signatur ``(job, component, name, value)`` besitzen.

	**Beschreibung**

	Der Mehrfachempfänger wird mit einem Namen und einem Callback initialisiert.
	Anschließend können mit :py:meth:`add_slot` mehrere Empfangsmuster 
	eingerichtet werden.

	.. note::
		Der Mehrfachempfänger erzeugt für jedes Empfangsmuster
		einen eigenen Empfänger.
		Passt eine Nachricht zu mehr als einem Empfangsmuster,
		wird das Callback für die Nachricht auch mehr als einmal aufgerufen.

	Der Mehrfachempfänger muss mit dem Nachrichtensystem verknüpft werden,
	damit er funktioniert. Dazu wird die Methode :py:meth:`activate` aufgerufen.

	*Siehe auch:*
	:py:class:`Listener`,
	:py:meth:`add_slot`,
	:py:meth:`activate`
	"""

	def __init__(self, name, callback):
		self._callback = callback
		self._listeners = {}
		self._message_busses = []
		self._name = name

	@property
	def name(self):
		"""
		Gibt den Namen des Empfängers zurück.
		"""
		return self._name

	@property
	def slots(self):
		"""
		Gibt eine Sequenz mit allen eingerichteten Empfangsmustern zurück.
		"""
		return self._listeners.keys()

	@property
	def listeners(self):
		"""
		Gibt eine Sequenz mit allen zur Zeit erzeugten Empfängern zurück.
		"""
		return self._listeners.values()

	def add_slot(self, slot):
		"""
		Fügt ein Empfangsmuster hinzu.

		*Siehe auch:*
		:py:class:`Slot`
		"""
		listener = slot.listener(self._callback)
		listener.receiver = self.name
		self._listeners[slot] = listener
		for message_bus in self._message_busses:
			message_bus.add_listener(listener)

	def remove_slot(self, slot):
		"""
		Entfernt ein Empfangsmuster.

		.. note::
			Es muss die selbe Referenz auf das Empfangsmuster übergeben werden,
			wie an :py:meth:`add_slot` übergeben wurde.
		"""
		listener = self._listeners[slot]
		del(self._listeners[slot])
		for message_bus in self._message_busses:
			message_bus.remove_listener(listener)

	def activate(self, message_bus):
		"""
		Verknüpft den Mehrfachempfänger mit dem Nachrichtensystem.
		"""
		for listener in self._listeners.values():
			message_bus.add_listener(listener)
		self._message_busses.append(message_bus)

	def deactivate(self, message_bus):
		"""
		Löst die Verbindung des Mehrfachempfängers vom Nachrichtensystem.
		"""
		for listener in self._listeners.values():
			message_bus.remove_listener(listener)
		self._message_busses.remove(message_bus)
