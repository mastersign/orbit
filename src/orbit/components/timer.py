# Package orbit.components.timer

from threading import Timer
from ..application import Component

class ActivityTimer(Component):

	def __init__(self, core, name, event_info, timeout = 6):
		super().__init__(core, name)
		self.timeout = timeout
		self.timer = None
		self.state = False
		self.listen(event_info.create_listener(self.process_event))

	def process_event(self, sender, name, value):
		self.trigger()

	def trigger(self):
		if self.timer:
			self.timer.cancel()
			self.trace("cancel timer")
		self.timer = Timer(self.timeout, self.timer_callback)
		self.timer.start()
		self.trace("set timer to %d seconds" % self.timeout)
		self.set_state(True)

	def timer_callback(self):
		self.timer = None
		self.trace("timeout")
		self.set_state(False)

	def set_state(self, state):
		if self.state == state:
			return
		self.state = state
		self.notify()

	def notify(self):
		self.send('state', self.state)

	def on_core_started(self):
		super().on_core_started()
		self.trigger()

	def on_core_stopped(self):
		if self.timer:
			self.timer.cancel()
			self.timer = None
		super().on_core_stopped()
