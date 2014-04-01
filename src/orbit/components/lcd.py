# Package orbit.components.lcd

from datetime import datetime
from ..application import Component, SingleDeviceHandle, MultiDeviceHandle
from tinkerforge.bricklet_lcd_20x4 import BrickletLCD20x4

LCD204 = BrickletLCD20x4

class LCDButtonsComponent(Component):

	def __init__(self, core, name, tracing = False):
		super().__init__(core, name, tracing = tracing)

		self.add_device_handle(MultiDeviceHandle(
			'lcd', LCD204.DEVICE_IDENTIFIER, 
			bind_callback=self.bind_lcd))

	def bind_lcd(self, device):
		uid = device.identity[0]

		def button_pressed(no):
			self.send('button_pressed', (uid, no))

		device.register_callback(LCD204.CALLBACK_BUTTON_PRESSED, button_pressed)

		def button_released(no):
			self.send('button_released', (uid, no))

		device.register_callback(LCD204.CALLBACK_BUTTON_RELEASED, button_released)


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


class LCDWatch(Component):

	def __init__(self, core, name, event_info, lcd_uid = None, 
		lines = {0: "%d.%m.%Y  %H:%M:%S"}):

		super().__init__(core, name)
		self.lines = lines

		if lcd_uid:
			self.lcd_handle = SingleDeviceHandle(
				'lcd', LCD204.DEVICE_IDENTIFIER, uid = lcd_uid)
		else:
			self.lcd_handle = MultiDeviceHandle(
				'lcds', LCD204.DEVICE_IDENTIFIER)

		self.add_device_handle(self.lcd_handle)

		self.listen(event_info.create_listener(self.process_event))

	def process_event(self, sender, name, value):
		self.lcd_handle.for_all_devices(self.show_time)

	def show_time(self, device):
		for line in self.lines.keys():
			text = datetime.now().strftime(self.lines[line])
			device.write_line(line, 0, text)
