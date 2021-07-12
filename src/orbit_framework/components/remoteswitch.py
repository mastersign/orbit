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

# Module orbit_framework.components.remoteswitch

"""
Dieses Modul enthält Komponenten für die Steuerung mit einem
Remote-Switch-Bricklet.

Enthalten sind die folgenden Komponenten:

- :py:class:`RemoteSwitchComponent`
"""

from .. import Component
from ..devices import SingleDeviceHandle
from tinkerforge.bricklet_remote_switch import BrickletRemoteSwitch

RS = BrickletRemoteSwitch


class RemoteSwitchComponent(Component):
    """
    Diese Komponente steuert eine Funksteckdose mit Hilfe
    des Remote-Switch-Bricklets	wenn Nachrichten über das Nachrichtensystem
    empfangen werden.

    **Parameter**

    ``name``
        Der Name der Komponente.
    ``group``
        Die Gruppennummer der Funksteckdose.
    ``socket``
        Die ID der Funksteckdose.
    ``on_slot``
        Ein Empfangsmuster welches die Funksteckdose einschalten soll.
    ``off_slot``
        Ein Empfangsmuster welches die Funksteckdose ausschalten soll.
    ``remote_type`` (*optional*)
        Der Typ der Funksteckdose.
        Mögliche Werte sind ``'A'``, ``'B'`` oder ``'C'``.
        Der Standardwert ist ``'A'``.
        Mehr Informationen zu Steckdosentypen sind in der `Remote-Switch-Dokumentation`_
        zu finden.
    ``switch_uid`` (*optional*)
        Die UID des Remote-Switch-Bricklets oder ``None`` für den ersten
        der gefunden wird.
        Der Standardwert ist ``None``.

    **Beschreibung**

    Wenn eine Nachricht mit dem Empfangsmuster von ``on_slot`` eintrifft,
    wird der Einschaltbefehl an die angegebene Steckdose gesendet.
    Wenn eine Nachricht mit dem Empfangsmuster von ``off_slot`` eintrifft,
    wird der Ausschaltbefehl an die angegebene Steckdose gesendet.

    *Siehe auch:*
    `Remote-Switch-Dokumentation`_

    .. _Remote-Switch-Dokumentation: http://www.tinkerforge.com/de/doc/Hardware/Bricklets/Remote_Switch.html
    """

    def __init__(self, name,
                 group, socket, on_slot, off_slot,
                 remote_type='A', switch_uid=None,
                 **nargs):

        super(RemoteSwitchComponent, self).__init__(name, **nargs)

        self._group = group
        self._socket = socket
        self._remote_type = remote_type

        self.add_listener(on_slot.listener(self._process_on_event))
        self.add_listener(off_slot.listener(self._process_off_event))

        self._switch_handle = SingleDeviceHandle(
            'switch', RS.DEVICE_IDENTIFIER, uid=switch_uid)
        self.add_device_handle(self._switch_handle)

    def _process_on_event(self, *args):
        self._switch_handle.for_each_device(
            lambda device: self._switch(device, RS.SWITCH_TO_ON))

    def _process_off_event(self, *args):
        self._switch_handle.for_each_device(
            lambda device: self._switch(device, RS.SWITCH_TO_OFF))

    def _switch(self, device, state):
        if self._remote_type == 'A':
            device.switch_socket_a(self._group, self._socket, state)
        elif self._remote_type == 'B':
            device.switch_socket_b(self._group, self._socket, state)
        elif self._remote_type == 'C':
            device.switch_socket_c(self._group, self._socket, state)
        else:
            self.trace("invalid remote switch typ: '%s'" % self._remote_type)
