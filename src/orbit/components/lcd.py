# Package orbit.components.lcd

from datetime import datetime, timedelta
from threading import Timer, Event
from ..application import Component, MultiDeviceHandle
from tinkerforge.bricklet_lcd_20x4 import BrickletLCD20x4

LCD204 = BrickletLCD20x4

class LCDButtonEventsComponent(Component):

	def __init__(self, core):
		super().__init__(core, "LCD Button Events")

		self.add_device_handle(MultiDeviceHandle(
			'lcd', LCD204.DEVICE_IDENTIFIER, 
			bind_callback=self.bind_lcd))

	def bind_lcd(self, device):
		uid = device.get_identity()[0]

		def button_pressed(no):
			self.send((uid, no), 'device', 'UI', 'LCD20x4', uid, 'button')

		device.register_callback(LCD204.CALLBACK_BUTTON_PRESSED, button_pressed)


class LCDAutoBacklightComponent(Component):

	def __init__(self, core, timeout = 6):
		super().__init__(core, "LCD Auto Backlight")
		self.timeout = timeout
		self.timer = None
		self.state = False

		self.lcd_handle = MultiDeviceHandle('lcd', LCD204.DEVICE_IDENTIFIER, 
			bind_callback = self.bind_lcd)
		self.add_device_handle(self.lcd_handle)

		self.listen_for_tag('UI', self.process_ui_event)

	def bind_lcd(self, device):
		self.update_device(device)

	def process_ui_event(self, sender, value, tags):
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
		for device in self.lcd_handle.devices:
			self.update_device(device)
		self.notify()

	def update_device(self, device):
		if self.state:
			device.backlight_on()
		else:
			device.backlight_off()

	def notify(self):
		self.send(self.state, 'LCD', 'backlight')

	def on_core_started(self):
		super().on_core_started()
		self.trigger()

	def on_core_stopped(self):
		if self.timer:
			self.timer.cancel()
			self.timer = None
		super().on_core_stopped()
