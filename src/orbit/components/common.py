# Package orbit.components.common

from ..application import Component

class EventCallback(Component):

	def __init__(self, name, 
		slot, callback):
		
		super().__init__(name)

		self.callback = callback

		self.add_listener(slot.listener(self.event_handler))

	def event_handler(self, sender, name, value):
		self.callback()