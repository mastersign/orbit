# Package tink.components.lcd

from .. import application
from tinkerforge.bricklet_lcd_20x4 import BrickletLCD20x4

LCD204 = BrickletLCD20x4

class LCDBacklightSwitchComponent(application.Component):

	def __init__(self):
		super().__init__("LCD Background Light Switch")
		self.state = False

		self.add_device_handle(application.MultiDeviceHandle(
			'lcd', LCD204.DEVICE_IDENTIFIER, 
			bind_callback=self.bind_lcd))

	def bind_lcd(self, device):

		def button_pressed(no):
			if no == 0:
				if device.is_backlight_on():
					device.backlight_off()
				else:
					device.backlight_on()

		device.register_callback(LCD204.CALLBACK_BUTTON_PRESSED, button_pressed)
