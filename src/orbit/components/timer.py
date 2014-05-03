# Package orbit.components.timer

from datetime import datetime
from time import time
from threading import Timer, Thread
from ..application import Component

class ActivityTimer(Component):

	def __init__(self, name, event_info, 
		initial_state = True, timeout = 6):

		super().__init__(name)
		self.timeout = timeout
		self.timer = None
		self.state = False
		self.initial_state = initial_state

		self.add_event_listener(event_info.create_listener(self.process_event))

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
		if self.state:
			self.send('on')
		else:
			self.send('off')

	def on_enabled(self):
		if self.initial_state:
			self.trigger()

	def on_disabled(self):
		if self.timer:
			self.timer.cancel()
			self.timer = None

class IntervalTimer(Component):

	def __init__(self, name, interval = 1):

		super().__init__(name)
		self.next_call = time()
		self.interval = interval
		self.timer = None
		self.state = False

	def on_enabled(self):
		self.start()

	def on_disabled(self):
		self.stop()

	def start(self, fire = True):
		self.state = True
		self.next_call = time()
		self.timer_callback(fire = fire)

	def stop(self):
		self.state = False
		if self.timer:
			self.timer.cancel()
			self.timer = None

	def timer_callback(self, fire = True):
		if fire and self.enabled:
			self.send('timer', self.next_call)
		self.next_call = self.next_call + self.interval
		td = self.next_call - time()
		if td > 0:
			self.timer = Timer(td, self.timer_callback)
			self.timer.start()
		else:
			self.trace("overtaken by workload - interval exceeded")
			Thread(target = self.start).start()

