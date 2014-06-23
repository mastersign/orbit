# coding=utf-8

# Package orbit.jobs.apps

from .. import App
from ..messaging import Slot
from ..components.timer import IntervalTimerComponent
from ..components import lcd

class EscapableApp(App):

	def __init__(self, *args, **nargs):
		super().__init__(*args, **nargs)

		self.add_component(
			lcd.LCD20x4ButtonsComponent('lcd_buttons'))

		self.add_deactivator(Slot(self.name, 'lcd_buttons', 'button_pressed',
			predicate = self._escape_predicate))

	def _escape_predicate(self, job, component, name, value):
		uid, button = value
		return button == 0


class WatchApp(EscapableApp):

	def __init__(self, name, 
		**nargs):
	
		super().__init__(name, **nargs)

		self.add_component(
			IntervalTimerComponent('watch_timer'))

		self.add_component(
			lcd.LCD20x4WatchComponent('lcd_watch',
				lines = {1: "     %d.%m.%Y     ", 2: "      %H:%M:%S      "},
				slot = Slot(self.name, 'watch_timer', 'timer')))


class MessageApp(EscapableApp):

	def __init__(self, name, 
		lines, 
		**nargs):

		super().__init__(name, **nargs)

		self.add_component(
			lcd.LCD20x4MessageComponent('msg', lines))


class MenuApp(App):

	def __init__(self, name, 
		entries, 
		**nargs):

		if 'in_history' not in nargs:
			nargs['in_history'] = True
		super().__init__(name, **nargs)

		self.add_component(
			lcd.LCD20x4MenuComponent('menu', entries = entries))

		self.add_deactivator(Slot(self.name, 'menu', 'escape'))
