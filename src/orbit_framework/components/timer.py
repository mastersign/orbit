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

# Module orbit_framework.components.timer

"""
Dieses Modul enthält einige Komponenten für die zeitabhängige Steuerung.

Enthalten sind die folgenden Komponenten:

- :py:class:`ActivityTimerComponent`
- :py:class:`IntervalTimerComponent`
"""

from datetime import datetime
from time import time
from threading import Timer, Thread
from .. import Component

class ActivityTimerComponent(Component):
	"""
	Diese Komponente schaltet zwischen den zwei Zuständen 
	**aktiv** und **inaktiv** um und versendet Nachrichten
	bei einer Änderung des Zustands. 
	Der Zustand wird durch Nachrichtenaktivität gesteuert.
	Dazu empfängt die Komponente Nachrichten mit einem Empfangsmuster
	und schaltet auf *aktiv*, sobald eine Nachricht eintrifft.
	Vergeht eine vorgegebene Zeitspanne ohne eingehende Nachrichten,
	schaltet die Komponente auf *inaktiv*.

	**Parameter**

	``name``
		Der Name der Komponente.
	``slot``
		Das Empfangsmuster für den Empfang der Nachrichten.
	``initial_state`` (*optional*)
		Der Anfangszustand der Komponente.
		Mögliche Werte sind ``True`` für *aktiv* und ``False`` für *inaktiv*.
		Standardwert ist ``True`` für *aktiv*.
	``timeout``
		Die Zeitspanne in Sekunden ohne Nachrichten, bis die Komponente in
		den Zustand *inaktiv* wechselt.

	**Nachrichten**

	Wenn die Komponente in den Zustand *aktiv* wechselt, 
	werden die folgenden beiden Nachrichten versandt:

	- *name:* ``'state'``, *value:* ``True``
	- *name:* ``'on'``, *value:* ``None``

	Wenn die Komponente in den Zustand *inaktiv* wechselt, 
	werden die folgenden beiden Nachrichten versandt:

	- *name:* ``'state'``, *value:* ``False``
	- *name:* ``'off'``, *value:* ``None``
	"""

	def __init__(self, name, slot, 
		initial_state = True, timeout = 6,
		**nargs):

		super(ActivityTimerComponent, self).__init__(name, **nargs)
		self.timeout = timeout
		self.timer = None
		self.state = False
		self.initial_state = initial_state

		self.add_listener(slot.listener(self.process_message))

	def process_message(self, job, component, name, value):
		self.trigger()

	def trigger(self):
		if self.timer:
			self.timer.cancel()
			self.trace("cancel timer")
		self.timer = Timer(self.timeout, self.timer_callback)
		self.timer.start()
		self.trace("set timer to %d seconds" % self.timeout)
		self.set_state(True)

	def timer_callback(self):
		self.timer = None
		self.trace("timeout")
		self.set_state(False)

	def set_state(self, state):
		if self.state == state:
			return
		self.state = state
		self.notify()

	def notify(self):
		self.send('state', self.state)
		if self.state:
			self.send('on')
		else:
			self.send('off')

	def on_enabled(self):
		if self.initial_state:
			self.trigger()

	def on_disabled(self):
		if self.timer:
			self.timer.cancel()
			self.timer = None

class IntervalTimerComponent(Component):
	"""
	Diese Komponente implementiert einen Zeitgeber,
	der in regelmäßigen Abständen eine Nachricht versendet.

	**Parameter**

	``name``
		Der Name der Komponente.
	``interval``
		Das Interval für den Nachrichtenversand in Sekunden.

	**Nachrichten**

	Die Komponente sendet im angegebenen Intervall die folgende Nachricht:

	- *name:* ``'timer'``, *value:* Der Zeitpunkt an dem die Nachricht versandt wurde.
	"""

	def __init__(self, name, interval = 1, 
		**nargs):

		super(IntervalTimerComponent, self).__init__(name, **nargs)
		self.next_call = time()
		self.interval = interval
		self.timer = None
		self.state = False

	def on_enabled(self):
		self.start()

	def on_disabled(self):
		self.stop()

	def start(self, fire = True):
		self.state = True
		self.next_call = time()
		self.timer_callback(fire = fire)

	def stop(self):
		self.state = False
		if self.timer:
			self.timer.cancel()
			self.timer = None

	def timer_callback(self, fire = True):
		if fire and self.enabled:
			self.send('timer', self.next_call)
		self.next_call = self.next_call + self.interval
		td = self.next_call - time()
		if td > 0:
			self.timer = Timer(td, self.timer_callback)
			self.timer.start()
		else:
			self.trace("overtaken by workload - interval exceeded")
			Thread(target = self.start).start()

