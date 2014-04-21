# Package orbit.components.common

from ..application import Component

class EventCallback(Component):

	def __init__(self, core, name, 
		event_info, callback,
		tracing = None, event_tracing = None):
		
		super().__init__(core, name, 
			tracing = tracing, event_tracing = event_tracing)

		self.callback = callback

		self.listen(event_info.create_listener(self.event_handler))

	def event_handler(self, sender, name, value):
		self.callback()