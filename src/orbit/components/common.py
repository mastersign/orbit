# coding=utf-8

# Package orbit.components.common

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
		slot, callback):
		
		super().__init__(name)

		self.callback = callback

		self.add_listener(slot.listener(self.process_message))

	def process_message(self, job, component, name, value):
		self.callback()
