# coding=utf-8

# Module orbit_framework.components.lcd

"""
Dieses Modul enthält einige Komponenten für die Steuerung von LCD-Displays.

Enthalten sind die folgenden Komponenten:

- :py:class:`LCD20x4ButtonsComponent`
- :py:class:`LCD20x4BacklightComponent`
- :py:class:`LCD20x4WatchComponent`
- :py:class:`LCD20x4MessageComponent`
- :py:class:`LCD20x4MenuComponent`
"""

from datetime import datetime
from .. import Component
from ..devices import SingleDeviceHandle, MultiDeviceHandle
from tinkerforge.bricklet_lcd_20x4 import BrickletLCD20x4
from ..lcdcharset import unicode_to_ks0066u

LCD204 = BrickletLCD20x4

class LCD20x4ButtonsComponent(Component):
	"""
	Diese Komponente reagiert auf Tastendruck an allen angeschlossenen
	LCD-20x4-Displays und versendet entsprechende Nachrichten.

	**Parameter**

	``name``
		Der Name der Komponente.

	**Nachrichten**

	Wenn eine Taste gedrückt wird,
	versendet die Komponente die folgende Nachricht:

	*name:* ``'button_pressed'``, *value:* ``(uid, no)``

	Wenn eine Taste losgelassen wird,
	versendet die Komponente die folgende Nachricht:

	*name:* ``'button_released'``, *value:* ``(uid, no)``

	Der Nachrichteninhalt ist jeweils ein Tupel aus UID des LCD-Displays
	und der Tastennummer.
	"""

	def __init__(self, name, 
		**nargs):
		
		super().__init__(name, **nargs)

		self.lcd_handle = MultiDeviceHandle(
			'lcd', LCD204.DEVICE_IDENTIFIER, 
			bind_callback=self.bind_lcd)
		self.add_device_handle(self.lcd_handle)

	def bind_lcd(self, device):
		uid = device.identity[0]

		def button_pressed(no):
			self.send('button_pressed', (uid, no))

		self.lcd_handle.register_callback(
			LCD204.CALLBACK_BUTTON_PRESSED, button_pressed)

		def button_released(no):
			self.send('button_released', (uid, no))

		self.lcd_handle.register_callback(
			LCD204.CALLBACK_BUTTON_RELEASED, button_released)


class LCD20x4BacklightComponent(Component):
	"""
	Diese Komponente schaltet die Hintergrundbeleuchtung
	aller angeschlossener LCD-20x4-Displays entsprechend dem
	Nachrichteninhalt eintreffender Nachrichten.

	**Parameter**

	``name``
		Der Name der Komponente.
	``slot``
		Das Empfangsmuster für den Nachrichtenempfang.
	``initial_state`` (*optional*)
		Der Anfangszustand der Hintergrundbeleuchtung.
		Mögliche Werte sind ``True`` für eingeschaltet und ``False``
		für ausgeschaltet. 
		Der Standardwert ist ``False``.

	**Beschreibung**

	Trifft eine Nachricht ein, die dem abgegebenen Empfangsmuster entspricht,
	wird der Nachrichteninhalt entsprechend der Python-Semantik
	als Wahrheitswert interpretiert. 
	Ist der Wert Wahr, wird die Hintergrundbeleuchtung für aller
	angeschlossenen LCD-20x4-Displays eingeschaltet, andernfalls
	wird sie ausgeschaltet.
	"""

	def __init__(self, name, 
		slot, initial_state = False,
		**nargs):

		super().__init__(name, **nargs)
		self.state = initial_state

		self.lcd_handle = MultiDeviceHandle(
			'lcd', LCD204.DEVICE_IDENTIFIER, 
			bind_callback = self.bind_lcd)
		self.add_device_handle(self.lcd_handle)

		self.add_listener(slot.listener(self.process_message))

	def bind_lcd(self, device):
		self.update_device(device)

	def process_message(self, job, component, name, value):
		self.set_state(value)

	def set_state(self, state):
		val = True if state else False
		if self.state == val:
			return
		self.state = val
		self.update_devices()

	def update_device(self, device):
		if self.state:
			device.backlight_on()
		else:
			device.backlight_off()

	def update_devices(self):
		self.lcd_handle.for_each_device(self.update_device)

	def on_core_started(self):
		super().on_core_started()
		self.update_devices()


class LCD20x4WatchComponent(Component):
	"""
	Diese Komponente zeigt beim Eintreffen einer Nachricht
	auf einem oder allen LCD-20x4-Displays
	eine formatierte Uhrzeit an.

	**Parameter**

	``name``
		Der Name der Komponente.
	``slot``
		Das Empfangsmuster für den Nachrichtenempfang.
	``lcd_uid`` (*optional*)
		Die UID eines LCD-20x4-Displays oder ``None``.
		Wird ``None`` angegeben, wird die Uhrzeit auf allen
		angeschlossenen Displays angezeigt.
		Der Standardwert ist ``None``.
	``lines`` (*optional*)
		Ein Dictionary welches eine Zeilennummer auf
		eine Formatierungszeichenkette abbildet.
		Die Zeilennummer gibt die 0-basierte Zeile im LCD-Display an.
		Die Formatierungszeichenkette muss der Formatierungssyntax von
		:py:meth:`datetime.strftime` entsprechen.
		Standardwert ist ``{0: '%d.%m.%Y  %H:%M:%S'}``.

	**Beschreibung**

	Sobald eine Nachricht empfangen wird, die dem angegebenen
	Empfangsmuster entspricht, wird die aktuelle Uhrzeit
	mit dem im Parameter ``lines`` angegebenen Format formatiert
	angezeigt.
	Wenn für Parameter ``lcd_uid`` eine UID übergeben wird,
	wird die Uhrzeit nur auf dem Display mit dieser UID angezeigt,
	andernfalls wird die Uhrzeit auf allen angeschlossenen 
	LCD-20x4-Displays angezeigt.
	"""

	def __init__(self, name, 
		slot, lcd_uid = None, lines = {0: '%d.%m.%Y  %H:%M:%S'},
		**nargs):

		super().__init__(name, **nargs)
		self.lines = lines

		if lcd_uid:
			self.lcd_handle = SingleDeviceHandle(
				'lcd', LCD204.DEVICE_IDENTIFIER, uid = lcd_uid)
		else:
			self.lcd_handle = MultiDeviceHandle(
				'lcds', LCD204.DEVICE_IDENTIFIER)

		self.add_device_handle(self.lcd_handle)

		self.add_listener(slot.listener(self.process_message))

	def process_message(self, job, component, name, value):
		self.lcd_handle.for_each_device(self.show_time)

	def on_enabled(self):
		self.lcd_handle.for_each_device(self.show_time)

	def show_time(self, device):
		for line in self.lines.keys():
			text = datetime.now().strftime(self.lines[line])
			device.write_line(line, 0, text)

class LCD20x4MessageComponent(Component):
	"""
	Diese Komponente zeigt eine konstante Nachricht
	auf einem oder allen LCD-20x4-Displays an.

	**Parameter**

	``name``
		Der Name der Komponente.
	``slot``
		Das Empfangsmuster für den Nachrichtenempfang.
	``lcd_uid`` (*optional*)
		Die UID eines LCD-20x4-Displays oder ``None``.
		Wird ``None`` angegeben, wird die Nachricht auf allen
		angeschlossenen Displays angezeigt.
		Der Standardwert ist ``None``.
	``lines``
		Eine Sequenz mit Zeichenketten.
		Es werden maximal 4 Zeichenketten ausgegeben.
		Ist eine Zeichenkette länger als 20 Zeichen, 
		wird der Rest abgeschnitten.

	**Beschreibung**

	Sobald eine Nachricht empfangen wird, die dem angegebenen
	Empfangsmuster entspricht, wird die Nachricht aus dem
	Parameter ``lines`` angezeigt.
	Wenn für Parameter ``lcd_uid`` eine UID übergeben wird,
	wird die Nachricht nur auf dem Display mit dieser UID angezeigt,
	andernfalls wird die Nachricht auf allen angeschlossenen 
	LCD-20x4-Displays angezeigt.
	"""

	def __init__(self, name, 
		lines, lcd_uid = None,
		**nargs):

		super().__init__(name, **nargs)
		self.lines = lines

		if lcd_uid:
			self.lcd_handle = SingleDeviceHandle(
				'lcd', LCD204.DEVICE_IDENTIFIER, uid = lcd_uid)
		else:
			self.lcd_handle = MultiDeviceHandle(
				'lcds', LCD204.DEVICE_IDENTIFIER)
		self.add_device_handle(self.lcd_handle)

	def on_enabled(self):
		self.lcd_handle.for_each_device(self.show_message)

	def on_disabled(self):
		self.lcd_handle.for_each_device(lambda device: device.clear_display())

	def show_message(self, device):
		device.clear_display()
		device.set_config(False, False)
		for i in range(0, min(len(self.lines), 4)):
			device.write_line(i, 0, unicode_to_ks0066u(self.lines[i]))

class LCD20x4MenuComponent(Component):
	"""
	Diese Komponente stellt ein Menü mit bis zu 8 Menüpunkten
	auf einem LCD-20x4-Display zur Verfügung.
	Die Navigation im Menü erfolgt mit Hilfe der 4 Tasten
	des LCD-20x4-Bricklets. Wird ein Menüpunkt ausgewählt,
	wird eine Nachricht mit der ID des gewählten Menüpunktes versandt.

	**Parameter**

	``name``
		Der Name der Komponente.
	``lcd_uid`` (*optional*)
		Die UID eines LCD-20x4-Displays oder ``None``.
	``entries`` (*optional*)
		Eine Sequenz von Menüpunkten.
		Jeder Menüpunkt wird durch ein Tuple aus zwei Zeichenketten
		definiert. Die erste Zeichenkette ist die Beschriftung des Menüpunktes
		und die zweite Zeichekette ist die ID des Menüpunktes.
		Der Standardwert ist ``[('None', 'none')]``.

	**Beschreibung**

	Wenn für den Parameter ``lcd_uid`` eine UID übergeben wird,
	wird das Menü auf dem Display mit der angegebenen UID angezeigt,
	andernfalls wird es auf dem ersten angeschlossenen LCD-20x4-Display
	angezeigt.

	Die Navigation im Menü erfolgt mit den vier Tasten am Display.
	Die Tasten sind von links nach rechts zwischen 0 und 3 durchnummeriert.
	Die Tasten sind wie folgt belegt:

	0. Escape oder Verlassen - sendet eine Nachricht mit dem Ereignisnamen ``'escape'``.
	1. Zurück - markiert den vorhergehenden Menüpunkt.
	2. Vorwärts - markiert den nächsten Menüpunkt.
	3. Enter oder Auswählen - sendet eine Nachricht mit der ID des Menüpunkts als Ereignisname.

	**Nachrichten**

	Wenn die Taste 0 gedrückt wird, sendet die Komponente die folgende Nachricht:

	- *name:* ``'escape'``, *value:* ``None``

	Wenn die Taste 3 gedrückt wird, sendet die Komponente die folgende Nachricht:

	- *name:* ``'<ID>'``, *value:* ``None``

	Wobei ``<ID>`` durch die ID des aktuell markierten Menüpunkts ersetzt wird.
	"""

	def __init__(self, name, 
		lcd_uid = None, entries = [('None', 'none')],
		**nargs):

		super().__init__(name, **nargs)
		self.entries = entries
		self.selected = 0
		self.active = False

		self.lcd_handle = SingleDeviceHandle(
			'lcd', LCD204.DEVICE_IDENTIFIER, uid = lcd_uid,
			bind_callback = self.bind_lcd)
		self.add_device_handle(self.lcd_handle)

		self.lcd_handle.register_callback(
			LCD204.CALLBACK_BUTTON_PRESSED, self.button_pressed)

	def bind_lcd(self, device):
		if self.active:
			self.update_lcd(device)

	def on_enabled(self):
		self.set_active(True)

	def on_disabled(self):
		self.set_active(False)

	def button_pressed(self, no):
		if not self.active:
			return
		if no == 0:
			self.on_button_escape()
		elif no == 1:
			self.on_button_previous()
		elif no == 2:
			self.on_button_next()
		elif no == 3:
			self.on_button_enter()

	def set_active(self, value):
		if self.active == value:
			return
		self.active = value
		self.lcd_handle.for_each_device(self.update_lcd)

	def set_selected(self, index):
		self.selected = index % len(self.entries)
		self.lcd_handle.for_each_device(self.update_lcd)

	def lcd_pos(self, index):
		return (index % 4, (index // 4) * 10)

	def update_lcd(self, device):
		device.clear_display()

		if not self.active:
			device.set_config(False, False)
			return

		for i in range(0, 7):
			if len(self.entries) > i:
				entry, _ = self.entries[i]
				l, r = self.lcd_pos(i)
				device.write_line(l, r, unicode_to_ks0066u(" " + entry)[0:9])
		if self.selected >= 0:
			l, r = self.lcd_pos(self.selected)
			device.write_line(l, r, "*")
			device.write_line(l, r, "")
			device.set_config(True, True)
		else:
			device.set_config(False, False)

	def on_button_escape(self):
		self.trace("escape")
		self.send('escape', None)

	def on_button_previous(self):
		self.set_selected(self.selected - 1)

	def on_button_next(self):
		self.set_selected(self.selected + 1)

	def on_button_enter(self):
		if self.selected >= 0 and self.selected < len(self.entries):
			label, name = self.entries[self.selected]
			self.trace("selected entry %s" % name)
			self.send(name, None)
