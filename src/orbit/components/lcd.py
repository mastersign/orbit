# Package orbit.components.lcd

from ..application import Component, MultiDeviceHandle
from tinkerforge.bricklet_lcd_20x4 import BrickletLCD20x4

LCD204 = BrickletLCD20x4

class LCDButtonsComponent(Component):

	def __init__(self, core, name, tracing = False):
		super().__init__(core, name, tracing = tracing)

		self.add_device_handle(MultiDeviceHandle(
			'lcd', LCD204.DEVICE_IDENTIFIER, 
			bind_callback=self.bind_lcd))

	def bind_lcd(self, device):
		uid = device.get_identity()[0]

		def button_pressed(no):
			self.send('button', (uid, no))

		device.register_callback(LCD204.CALLBACK_BUTTON_PRESSED, button_pressed)


class LCDBacklightComponent(Component):

	def __init__(self, core, name, event_info):
		super().__init__(core, name)
		self.state = False

		self.lcd_handle = MultiDeviceHandle(
			'lcd', LCD204.DEVICE_IDENTIFIER, 
			bind_callback = self.bind_lcd)
		self.add_device_handle(self.lcd_handle)

		self.listen(event_info.create_listener(self.process_event))

	def bind_lcd(self, device):
		self.update_device(device)

	def process_event(self, sender, name, value):
		self.set_state(value)

	def set_state(self, state):
		if self.state == state:
			return
		self.state = state
		self.update_devices()

	def update_device(self, device):
		if self.state:
			device.backlight_on()
		else:
			device.backlight_off()

	def update_devices(self):
		for device in self.lcd_handle.devices:
			self.update_device(device)

	def on_core_started(self):
		super().on_core_started()
		self.update_devices()
