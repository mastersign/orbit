# Package orbit.components.common

from ..application import Component

class EventCallback(Component):

	def __init__(self, name, 
		event_info, callback,
		tracing = None, event_tracing = None):
		
		super().__init__(name, 
			tracing = tracing, event_tracing = event_tracing)

		self.callback = callback

		self.add_event_listener(event_info.create_listener(self.event_handler))

	def event_handler(self, sender, name, value):
		self.callback()