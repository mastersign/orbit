# Package orbit.jobs.apps

from ..application import App, Slot
from ..components.timer import IntervalTimerComponent
from ..components.lcd import LCDButtonsComponent, LCDWatchComponent, LCDMessageComponent

class EscapableApp(App):

	def __init__(self, *args, **nargs):
		super().__init__(*args, **nargs)

		self.add_component(
			LCDButtonsComponent('lcd_buttons'))

		self.add_deactivator(Slot(self.name, 'lcd_buttons', 'button_pressed',
			predicate = self._escape_predicate))

	def _escape_predicate(self, job, component, name, value):
		uid, button = value
		return button == 0


class WatchApp(EscapableApp):

	def __init__(self, name, **nargs):
		super().__init__(name, **nargs)

		self.add_component(
			IntervalTimerComponent('watch_timer'))

		self.add_component(
			LCDWatchComponent('lcd_watch',
				lines = {1: "     %d.%m.%Y     ", 2: "      %H:%M:%S      "},
				slot = Slot(self.name, 'watch_timer', 'timer')))


class MessageApp(EscapableApp):

	def __init__(self, name, lines, **nargs):
		super().__init__(name, **nargs)

		self.add_component(
			LCDMessageComponent('msg', lines))
