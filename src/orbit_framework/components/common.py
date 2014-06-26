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

# Module orbit_framework.components.common

"""
Dieses Modul enthält einige Komponenten für den allgemeinen Einsatz.

Enthalten sind die folgenden Komponenten:

- :py:class:`EventCallbackComponent`
"""

from .. import Component

class EventCallbackComponent(Component):
	"""
	Diese Komponente wartet mit Hilfe eines Empfangsmusters auf Nachrichten,
	und ruft ein Callback auf, wenn eine passende Nachricht eintrifft.

	**Parameter**

	``name``
		Der Name der Komponente.
	``slot``
		Das Empfangsmuster für den Empfang der Nachrichten.
	``callback``
		Eine parameterlose Funktion.
	"""

	def __init__(self, name, 
		slot, callback,
		**nargs):
		
		super(EventCallbackComponent, self).__init__(name, **nargs)

		self.callback = callback

		self.add_listener(slot.listener(self.process_message))

	def process_message(self, job, component, name, value):
		self.callback()
