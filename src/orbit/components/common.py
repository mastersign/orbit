# Package orbit.components.common

from ..application import Component

class EventCallback(Component):

	def __init__(self, name, 
		slot, callback):
		
		super().__init__(name)

		self.callback = callback

		self.add_listener(slot.listener(self.process_message))

	def process_message(self, job, component, name, value):
		self.callback()