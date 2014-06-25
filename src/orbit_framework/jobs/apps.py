# coding=utf-8

# Module orbit_framework.jobs.apps

"""
Dieses Modul enthält einige Apps und App-Basisklassen 
für den allgemeinen Einsatz.

Die folgenden Apps sind enthalten:

- :py:class:`EscapableApp` (Basisklasse)
- :py:class:`WatchApp`
- :py:class:`MessageApp`
- :py:class:`MenuApp`
"""

from .. import App
from ..messaging import Slot
from ..components.timer import IntervalTimerComponent
from ..components import lcd

class EscapableApp(App):
	"""
	Dies ist eine Basisklasse für Apps, welche sich durch das
	Drücken der ersten Taste (ganz links) eines LCD-20x4-Displays
	selbst beenden.

	Diese Funktionalität wird häufig in menügesteuerten
	Anwendungen im Zusammenspiel mit einem oder mehreren
	LCD-20x4-Displays benötigt.

	*Siehe auch:*
	:py:class:`orbit_framework.components.lcd.LCD20x4ButtonsComponent`
	"""

	def __init__(self, *args, **nargs):
		super(EscapableApp, self).__init__(*args, **nargs)

		self.add_component(
			lcd.LCD20x4ButtonsComponent('lcd_buttons'))

		self.add_deactivator(Slot(self.name, 'lcd_buttons', 'button_pressed',
			predicate = self._escape_predicate))

	def _escape_predicate(self, job, component, name, value):
		_, button = value
		return button == 0


class WatchApp(EscapableApp):
	"""
	Diese App zeigt, solange sie aktiviert ist, das Datum und die Uhrzeit
	auf allen angeschlossenen LCD-20x4-Displays an.

	**Parameter**

	``name``
		Der Name der App.

	**Beschreibung**

	Diese App erbt von :py:class:`EscapableApp` und kann daher mit einem
	Druck auf die erste Taste eines LCD-Displays (ganz links) deaktiviert werden.

	*Siehe auch:*
	:py:class:`orbit_framework.components.lcd.LCD20x4WatchComponent`,
	:py:class:`orbit_framework.components.timer.IntervalTimerComponent`
	"""

	def __init__(self, name, 
		**nargs):
	
		super(WatchApp, self).__init__(name, **nargs)

		self.add_component(
			IntervalTimerComponent('watch_timer'))

		self.add_component(
			lcd.LCD20x4WatchComponent('lcd_watch',
				lines = {1: "     %d.%m.%Y     ", 2: "      %H:%M:%S      "},
				slot = Slot(self.name, 'watch_timer', 'timer')))


class MessageApp(EscapableApp):
	"""
	Diese App zeigt, solange sie aktiviert ist, eine vorgegebene
	Nachricht auf allen angeschlossenen LCD-20x4-Displays an.

	**Parameter**

	``name``
		Der Name der App.
	``lines``
		Eine Sequenz mit bis zu vier Zeichenketten.
		Jede Zeichenkette wird in einer der vier LCD-Zeilen	dargestellt. 
		Ist eine Zeichenkette länger als 20 Zeichen, wird der Rest abgeschnitten.

	**Beschreibung**

	Diese App erbt von :py:class:`EscapableApp` und kann daher mit einem
	Druck auf die erste Taste eines LCD-Displays (ganz links) deaktiviert werden.

	*Siehe auch:*
	:py:class:`orbit_framework.components.lcd.LCD20x4MessageComponent`
	"""

	def __init__(self, name, 
		lines, 
		**nargs):

		super(MessageApp, self).__init__(name, **nargs)

		self.add_component(
			lcd.LCD20x4MessageComponent('msg', lines))


class MenuApp(App):
	"""
	Diese App zeigt, solange sie aktiviert ist, ein Menü 
	auf dem ersten angeschlossenen LCD-20x4-Display an.

	**Parameter**

	``name``
		Der Name der App.
	``entries``
		Eine Sequenz mit Menüpunkten.
		(*siehe auch:* :py:class:`orbit_framework.components.lcd.LCD20x4MenuComponent`)

	**Beschreibung**

	Diese App wird durch die *escape*-Nachricht der Menü-Komponente deaktiviert.
	Sie kann also durch einen Druck auf die erste Taste (ganz links)
	des LCD-Displays deaktiviert werden.

	.. note::
		Das Attribut :py:attr:`orbit_framework.App.in_history` wird 
		für diese App standardmäßig auf ``True`` gesetzt.
		In Folge wird die Menü-App in der App-History vermerkt
		und es kann unkompliziert durch mehrere	verknüpfte Menü-Apps
		navigiert werden möglich.

	*Siehe auch:*
	:py:class:`orbit_framework.components.lcd.LCD20x4MenuComponent`
	"""

	def __init__(self, name, 
		entries, 
		**nargs):

		nargs = dict({'in_history': True}, **nargs)
		super(MenuApp, self).__init__(name, **nargs)

		self.add_component(
			lcd.LCD20x4MenuComponent('menu', entries = entries))

		self.add_deactivator(Slot(self.name, 'menu', 'escape'))
