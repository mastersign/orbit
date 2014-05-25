# coding=utf-8

# Package orbit.jobs.services

from ..application import Service, Slot
from ..components.common import EventCallbackComponent
from ..components.timer import ActivityTimerComponent
from ..components.lcd import LCDBacklightComponent

class StandbyService(Service):

	def __init__(self, name, activity_slot, timeout = 6, **nargs):
		super().__init__(name, **nargs)

		self.add_component(
			ActivityTimerComponent('standby_timer',
				initial_state = True, timeout = timeout,
				slot = activity_slot))

		self.add_component(
			LCDBacklightComponent('lcd_backlight',
				initial_state = True,
				slot = Slot(self.name, 'standby_timer', 'state')))

		self.add_component(
			EventCallbackComponent('history_killer',
				slot = Slot(self.name, 'standby_timer', 'off'),
				callback = lambda: self.core.clear_application_history()))
