# coding=utf-8

# Module orbit_framework.jobs.services

"""
Dieses Modul enthält einige Services für den allgemeinen Einsatz.

Enthalten sind die folgenden Services:

- :py:class:`StandbyService`
"""

from .. import Service
from ..messaging import Slot
from ..components.common import EventCallbackComponent
from ..components.timer import ActivityTimerComponent
from ..components.lcd import LCD20x4BacklightComponent

class StandbyService(Service):
	"""
	Dieser Service überwacht mit Hilfe eines Empfangsmusters
	die Benutzeraktivität und schaltet die Anwendung nach einem
	vorgegebenen Zeitfenster ohne Aktivität in den Standby-Modus.
	Was soviel bedeutet, wie die Hintergrundbeleuchtung
	der angeschlossenen LCD-Displays abzuschalten und die
	App-History zu leeren.

	**Parameter**

	``name``
		Der Name des Service.
	``activity_slot``
		Ein Empfangsmuster für alle Nachrichten, die als Benutzeraktivität
		interpretiert werde können.
	``timeout`` (*optional*)
		Das Länge des Zeitfensters für Inaktivität in Sekunden, 
		nach dem in den Standby geschaltet wird.
		Standardwert ist ``6`` Sekunden.

	**Nachrichten**

	Der Service sendet die folgenden Nachrichten, wenn Benutzeraktivität
	detektiert wird:

	- *component:* ``'standby_timer'``, *name:* ``'state'``, *value:* ``True``
	- *component:* ``'standby_timer'``, *name:* ``'on'``, *value:* ``None``

	Wenn die angegebene Zeitspanne für Inaktivität erreicht ist, wird
	in den Standby-Modus geschaltet und es werden die folgenden Nachrichten versandt:

	- *component:* ``'standby_timer'``, *name:* ``'state'``, *value:* ``False``
	- *component:* ``'standby_timer'``, *name:* ``'off'``, *value:* ``None``

	*Siehe auch:*
	:py:class:`orbit_framework.components.timer.ActivityTimerComponent`
	"""

	def __init__(self, name, 
		activity_slot, timeout = 6, 
		**nargs):
		
		super(StandbyService, self).__init__(name, **nargs)

		self.add_component(
			ActivityTimerComponent('standby_timer',
				initial_state = True, timeout = timeout,
				slot = activity_slot))

		self.add_component(
			LCD20x4BacklightComponent('lcd_backlight',
				initial_state = True,
				slot = Slot(self.name, 'standby_timer', 'state')))

		self.add_component(
			EventCallbackComponent('history_killer',
				slot = Slot(self.name, 'standby_timer', 'off'),
				callback = lambda: self.core.clear_application_history()))
