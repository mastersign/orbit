# coding=utf-8

## ORBIT ist ein Python-Framework für TinkerForge-Anwendungen
## Copyright (C) 2021 Tobias Kiertscher <dev@mastersign.de>
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

# Module orbit_framework.components.remoteswitch_v2

"""
Dieses Modul enthält Komponenten für die Steuerung mit einem
Remote-Switch-Bricklet 2.0.

Enthalten sind die folgenden Komponenten:

- :py:class:`RemoteSwitchV2Component`
- :py:class:`RemoteSwitchV2ReceiverComponent`
"""

import time
from collections import namedtuple
from tinkerforge.bricklet_remote_switch_v2 import BrickletRemoteSwitchV2

from .. import Component
from ..devices import SingleDeviceHandle, MultiDeviceHandle

RS2 = BrickletRemoteSwitchV2

SwitchCommand = namedtuple('SwitchCommand', ['state', 'dim', 'dim_value'])


class RemoteSwitchV2Component(Component):
    """
    Diese Komponente steuert eine Funksteckdose mit Hilfe
    des Remote-Switch-Bricklets 2.0 wenn Nachrichten über das Nachrichtensystem
    empfangen werden.

    **Parameter**

    ``name``
        Der Name der Komponente.
    ``group``
        Die Gruppennummer der Funksteckdose.
        Typ A: House-Code, Typ B: Address, Typ C: System-Code
    ``socket``
        Die ID der Funksteckdose.
        Typ A: Receiver-Code, Typ B: Unit, Typ C: Device-Code
    ``on_slot`` (*optional)
        Ein Empfangsmuster welches die Funksteckdose einschalten soll.
    ``off_slot`` (*optional*)
        Ein Empfangsmuster welches die Funksteckdose ausschalten soll.
    ``switch_slot`` (*optional*)
        Ein Empfangsmuster welches die Funksteckdose anhand des Nachrichtenwertes schalten soll.
    ``dim_slot`` (*optional*)
        Ein Empfangsmuster welches die Funksteckdose dimmen soll.
    ``remote_type`` (*optional*)
        Der Typ der Funksteckdose.
        Mögliche Werte sind ``'A'``, ``'B'`` oder ``'C'``.
        Der Standardwert ist ``'A'``.
        Mehr Informationen zu Steckdosentypen sind in der `Remote-Switch-Dokumentation`_
        zu finden.
    ``send_repeats`` (*optional*)
        Die Anzahl der Sendewiederholungen beim Schalten.
        Der Standardwert ist 5.
    ``uid`` (*optional*)
        Die UID des Remote-Switch-Bricklets oder ``None`` für den ersten
        der gefunden wird.
        Der Standardwert ist ``None``.

    **Beschreibung**

    Wenn eine Nachricht mit dem Empfangsmuster von ``on_slot`` eintrifft,
    wird der Einschaltbefehl an die angegebene Steckdose gesendet.
    Wenn eine Nachricht mit dem Empfangsmuster von ``off_slot`` eintrifft,
    wird der Ausschaltbefehl an die angegebene Steckdose gesendet.
    Wenn eine Nachricht mit dem Empfangsmuster von ``switch_slot`` eintrifft,
    wird der Einschaltbefehl an die angegebene Steckdose gesendet,
    wenn der Nachrichtenwert *wahr* ist, sonst wird der Ausschaltbefehl gesendet.
    Wenn eine Nachricht mit dem Empfangsmuster von ``dim_slot`` eintrifft und der ``typ`` = ``'B'`` ist,
    wird ein Dim-Befehl an die angegebene Steckdose gesendet.
    Als Wert der Nachricht wird eine Zahl zwischen 0 und 255 erwartet.

    *Siehe auch:*
    `Remote-Switch-2.0-Dokumentation`_

    .. _Remote-Switch-2.0-Dokumentation: https://www.tinkerforge.com/de/doc/Hardware/Bricklets/Remote_Switch_V2.html
    """

    def __init__(self, name,
                 group, socket,
                 on_slot=None, off_slot=None, switch_slot=None, dim_slot=None,
                 remote_type='A', send_repeats=5, uid=None,
                 **nargs):

        super(RemoteSwitchV2Component, self).__init__(name, **nargs)

        self._group = group
        self._socket = socket
        self._remote_type = remote_type
        self._send_repeats = send_repeats

        self._tasks = []

        if on_slot:
            self.add_listener(on_slot.listener(self._process_on_event))
        if off_slot:
            self.add_listener(off_slot.listener(self._process_off_event))
        if switch_slot:
            self.add_listener(switch_slot.listener(self._process_switch_event))
        if dim_slot:
            self.add_listener(dim_slot.listener(self._process_dim_event))

        self._switch_handle = SingleDeviceHandle(
            'switch', RS2.DEVICE_IDENTIFIER, uid=uid,
            bind_callback=self._on_bind,
            unbind_callback=self._on_unbind)

        self._switch_handle.register_callback(
            RS2.CALLBACK_SWITCHING_DONE, self._try_process_tasks)

        self.add_device_handle(self._switch_handle)

    @staticmethod
    def _device_id(device):
        identity = device.get_identity()
        return identity.connected_uid + '_' + identity.uid

    def _on_bind(self, device):
        device.set_repeats(self._send_repeats)

    def _on_unbind(self, device):
        self._tasks = []

    def _process_on_event(self, *_):
        self._enqueue_task(SwitchCommand(True, False, 0))
        self._try_process_tasks()

    def _process_off_event(self, *_):
        self._enqueue_task(SwitchCommand(False, False, 0))
        self._try_process_tasks()

    def _process_switch_event(self, job, component, name, value):
        self._enqueue_task(SwitchCommand(RS2.SWITCH_TO_ON if value else RS2.SWITCH_TO_OFF, False, 0))
        self._try_process_tasks()

    def _process_dim_event(self, job, component, name, value):
        dim_value = value
        self._enqueue_task(SwitchCommand(True, True, dim_value))
        self._try_process_tasks()

    def _enqueue_task(self, task):
        self._tasks.insert(0, task)

    def _try_process_tasks(self, device=None, **_):
        if len(self._tasks) == 0:
            return
        if not device:
            self._switch_handle.for_each_device(
                lambda d: self._try_process_tasks(d))
            return

        if device.get_switching_state() == RS2.SWITCHING_STATE_BUSY:
            return

        command = self._tasks.pop()
        if command.dim:
            self.trace(f'sending dim command to [{device.get_identity().uid}],'
                       f'B({self._group}, {self._socket}):'
                       f' {command.state}, {command.dim_value}')
            if self._remote_type == 'B':
                device.dim_socket_b(self._group, self._socket, command.dim_value)
            else:
                self.trace("can not dim with remote switch typ: '%s'; can dim only with typ 'B'" % self._remote_type)
        else:
            self.trace(f'sending switch command to [{device.get_identity().uid}],'
                       f' {self._remote_type}({self._group}, {self._socket}):'
                       f' {command.state}, {command.dim_value}')
            if self._remote_type == 'A':
                device.switch_socket_a(self._group, self._socket, command.state)
            elif self._remote_type == 'B':
                device.switch_socket_b(self._group, self._socket, command.state)
            elif self._remote_type == 'C':
                device.switch_socket_c(self._group, self._socket, command.state)
            else:
                self.trace("invalid remote switch typ: '%s'" % self._remote_type)


SwitchNotification = namedtuple('SwitchNotification', ['group', 'socket', 'state', 'dim_value'])


class RemoteSwitchV2ReceiverComponent(Component):
    """
    Diese Komponente empfängt Schaltbefehle mit Hilfe des Remote-Switch-Bricklets 2.0
    und sendet entsprechende Nachrichten über das Nachrichtensystem.

    **Parameter**

    ``name``
        Der Name der Komponente.
    ``remote_type`` (*optional*)
        Der Typ der Funksteckdose.
        Mögliche Werte sind ``'A'``, ``'B'`` oder ``'C'``.
        Der Standardwert ist ``'A'``.
        Mehr Informationen zu Steckdosentypen sind in der `Remote-Switch-Dokumentation`_
        zu finden.
    ``group`` (*optional*)
        Die Gruppennummer auf die reagiert werden soll oder ``None``,
        wenn auf jede Gruppennummer reagiert werden soll.
        Typ A: House-Code, Typ B: Address, Typ C: System-Code.
        Standardwert: ``None``
    ``socket`` (*optional*)
        Die Geräte-ID auf die reagiert werden soll oder ``None``,
        wenn auf jede Geräte-ID reagiert werden soll.
        Typ A: Receiver-Code, Typ B: Unit, Typ C: Device-Code
    ``min_receive_repeats`` (*optional*)
        Die Anzahl der minimalen Wiederholungen von aufeinanderfolgenden identischen
        Befehlen beim Empfang, die zum Versenden einer Nachricht über das Nachrichtensystem führen.
        Der Standardwert ist 2.
    ``filter_repeats`` (*optional*)
        Schaltet die Unterdrückung von wiederholten Nachrichten ein.
    ``repeat_filter_duration`` (*optional*)
        Das Zeitfenster in Sekunden in dem sich wiederholende Nachrichten unterdrückt werden.
        Der Standardwert ist 0.5.
    ``uid`` (*optional*)
        Die UID eines Remote-Switch-Bricklets oder ``None`` für alle die gefunden werden.
        Der Standardwert ist ``None``.

    **Beschreibung**

    Wenn ein Schaltbefehl empfangen wird, werden die folgenden Nachrichten über
    das Nachrichtensystem gesendet:

    * ``switch_on`` mit ``True`` als Nachrichtenwert
    * ``switch_off`` mit ``False`` als Nachrichtenwert
    * ``switch`` mit einem Objekt mit den folgenden Eigenschaften als Nachrichtenwert:
        * ``group``: Die Gruppennummer
        * ``socket``: Die Geräte-ID
        * ``state``: ``True`` oder ``False``
        * ``dim_value``: ``None`` oder eine Zahl zwischen 0 und 255

    *Siehe auch:*
    `Remote-Switch-2.0-Dokumentation`_

    .. _Remote-Switch-2.0-Dokumentation: https://www.tinkerforge.com/de/doc/Hardware/Bricklets/Remote_Switch_V2.html
    """

    def __init__(self, name,
                 remote_type='A', group=None, socket=None,
                 min_receive_repeats=5, filter_repeats=False,
                 repeat_filter_duration=0.5, uid=None,
                 **nargs):
        super(RemoteSwitchV2ReceiverComponent, self).__init__(name, **nargs)

        self._remote_type = remote_type
        self._group = group
        self._socket = socket
        self._min_receive_repeats = min_receive_repeats
        self._filter_repeats = filter_repeats
        self._repeat_filter_duration = repeat_filter_duration

        self._last_event = None
        self._last_repeats = 9999
        self._last_ts = 0

        if uid:
            self._receiver_handle = SingleDeviceHandle(
                'receiver', RS2.DEVICE_IDENTIFIER, uid=uid,
                bind_callback=self._on_bind)
        else:
            self._receiver_handle = MultiDeviceHandle(
                'receiver', RS2.DEVICE_IDENTIFIER,
                bind_callback=self._on_bind,
                unbind_callback=self._on_unbind)

        if self._remote_type == 'A':
            self._receiver_handle.register_callback(RS2.CALLBACK_REMOTE_STATUS_A, self._on_remote_a)
        elif self._remote_type == 'B':
            self._receiver_handle.register_callback(RS2.CALLBACK_REMOTE_STATUS_B, self._on_remote_b)
        elif self._remote_type == 'C':
            self._receiver_handle.register_callback(RS2.CALLBACK_REMOTE_STATUS_C, self._on_remote_c)

        self.add_device_handle(self._receiver_handle)

    def _remote_type_code(self):
        if self._remote_type == 'A':
            return RS2.REMOTE_TYPE_A
        if self._remote_type == 'B':
            return RS2.REMOTE_TYPE_B
        if self._remote_type == 'C':
            return RS2.REMOTE_TYPE_C
        return None

    def _on_bind(self, device):
        self.trace('starting receiver in ' + device.get_identity().uid)
        device.set_remote_configuration(self._remote_type_code(), self._min_receive_repeats, True)

    def _on_unbind(self, device):
        self.trace('stopping receiver in ' + device.get_identity().uid)
        device.set_remote_configuration(RS2.REMOTE_TYPE_A, 2, False)

    def _can_send(self, group, socket, switch_to, dim_value, repeats):
        if self._group and self._group != group:
            return False
        if self._socket and self._socket != socket:
            return False
        if not self._filter_repeats:
            return True

        event = (group, socket, switch_to, dim_value)
        ts = time.time()
        is_repeat = self._last_event == event \
            and self._last_repeats < repeats \
            and ts - self._last_ts < self._repeat_filter_duration
        self._last_event = event
        self._last_repeats = repeats
        self._last_ts = ts
        return not is_repeat

    def _on_remote_a(self, house_code, receiver_code, switch_to, repeats, *, device, **_):
        if not self._can_send(house_code, receiver_code, switch_to, 0, repeats):
            return
        self.trace(f'received remote command from [{device.identity.uid}],'
                   f' {house_code}, {receiver_code}: {switch_to}')
        if switch_to == RS2.SWITCH_TO_ON:
            self.send('switch_on', True)
        else:
            self.send('switch_off', False)
        self.send('switch', SwitchNotification(house_code, receiver_code, switch_to, None))

    def _on_remote_b(self, address, unit, switch_to, dim_value, repeats, *, device, **_):
        if not self._can_send(address, unit, switch_to, dim_value, repeats):
            return
        self.trace(f'received remote command from [{device.identity.uid}],'
                   f' {address}, {unit}: {switch_to}, {dim_value}')
        if switch_to == RS2.SWITCH_TO_ON:
            self.send('switch_on', True)
        else:
            self.send('switch_off', False)
        self.send('switch', SwitchNotification(address, unit, switch_to == RS2.SWITCH_TO_ON, dim_value))

    def _on_remote_c(self, system_code, device_code, switch_to, repeats, *, device, **_):
        if not self._can_send(system_code, device_code, switch_to, 0, repeats):
            return
        self.trace(f'received remote command from [{device.identity.uid}],'
                   f' {system_code}, {device_code}: {switch_to}')
        if switch_to == RS2.SWITCH_TO_ON:
            self.send('switch_on', True)
        else:
            self.send('switch_off', False)
        self.send('switch', SwitchNotification(system_code, device_code, switch_to, None))
