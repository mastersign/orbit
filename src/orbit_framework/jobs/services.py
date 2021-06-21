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

    def __init__(self, name, activity_slot, timeout=6, **nargs):
        super(StandbyService, self).__init__(name, **nargs)

        self.add_component(
            ActivityTimerComponent(
                'standby_timer',
                initial_state=True, timeout=timeout,
                slot=activity_slot))

        self.add_component(
            LCD20x4BacklightComponent('lcd_backlight',
                                      initial_state=True,
                                      slot=Slot(self.name, 'standby_timer', 'state')))

        self.add_component(
            EventCallbackComponent('history_killer',
                                   slot=Slot(self.name, 'standby_timer', 'off'),
                                   callback=lambda: self.core.clear_application_history()))
