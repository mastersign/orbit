# Package orbit.jobs.apps

from ..application import App, Slot
from ..components.timer import IntervalTimerComponent
from ..components.lcd import LCDButtonsComponent, LCDWatchComponent

class WatchApp(App):

	def __init__(self, name, **nargs):
		super().__init__(name, **nargs)

		self.add_component(
			IntervalTimerComponent('watch_timer'))

		self.add_component(
			LCDWatchComponent('lcd_watch',
				lines = {1: "     %d.%m.%Y     ", 2: "      %H:%M:%S      "},
				slot = Slot(self.name, 'watch_timer', 'timer')))

		self.add_component(
			LCDButtonsComponent('lcd_buttons'))

		self.add_deactivator(Slot(self.name, 'lcd_buttons', 'button_pressed',
			predicate = self._exit_predicate))

	def _exit_predicate(self, job, component, name, value):
		uid, button = value
		return button == 0
