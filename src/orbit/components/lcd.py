# Package orbit.components.lcd

from datetime import datetime
from ..application import Component, SingleDeviceHandle, MultiDeviceHandle
from tinkerforge.bricklet_lcd_20x4 import BrickletLCD20x4
from ..lcdcharset import unicode_to_ks0066u

LCD204 = BrickletLCD20x4

class LCDButtonsComponent(Component):

	def __init__(self, core, name, 
		tracing = None, event_tracing = None):
		
		super().__init__(core, name, 
			tracing = tracing, event_tracing = event_tracing)

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

	def __init__(self, core, name, event_info, 
		tracing = None, event_tracing = None):

		super().__init__(core, name, 
			tracing = tracing, event_tracing = event_tracing)
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

	def __init__(self, core, name, event_info,
		lcd_uid = None, lines = {0: "%d.%m.%Y  %H:%M:%S"},
		tracing = None, event_tracing = None):

		super().__init__(core, name, 
			tracing = tracing, event_tracing = event_tracing)
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

class LCDMessage(Component):

	def __init__(self, core, name, event_info, lines, 
		lcd_uid = None,
		tracing = None, event_tracing = None):

		super().__init__(core, name,
			tracing = tracing, event_tracing = event_tracing)
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
		self.lcd_handle.for_all_devices(self.show_message)

	def show_message(self, device):
		device.clear_display()
		for i in range(0, min(len(self.lines), 4)):
			device.write_line(i, 0, unicode_to_ks0066u(self.lines[i]))

class LCDMenu(Component):

	def __init__(self, core, name, event_info, button_event_info,
		lcd_uid = None,	entries = [('None', 'none')],
		tracing = None, event_tracing = None):

		super().__init__(core, name,
			tracing = tracing, event_tracing = event_tracing)
		self.entries = entries
		self.selected = 0
		self.active = False

		self.lcd_handle = SingleDeviceHandle(
			'lcd', LCD204.DEVICE_IDENTIFIER, uid = lcd_uid,
			bind_callback = self.bind_lcd)
		self.add_device_handle(self.lcd_handle)

		self.listen(event_info.create_listener(self.process_activation_event))
		self.listen(button_event_info.create_listener(self.process_button_event))

	def bind_lcd(self, device):
		if self.active:
			self.update_lcd(device)

	def process_activation_event(self, sender, name, value):
		self.set_active(value)

	def process_button_event(self, sender, name, value):
		if not self.active:
			return
		_, no = value
		if no == 0:
			self.on_button_escape()
		elif no == 1:
			self.on_button_previous()
		elif no == 2:
			self.on_button_next()
		elif no == 3:
			self.on_button_enter()

	def set_active(self, value):
		if self.active == value:
			return
		self.active = value
		self.lcd_handle.for_all_devices(self.update_lcd)

	def set_selected(self, index):
		self.selected = index % len(self.entries)
		self.lcd_handle.for_all_devices(self.update_lcd)

	def lcd_pos(self, index):
		return (index % 4, (index // 4) * 10)

	def update_lcd(self, device):
		device.clear_display()

		if not self.active:
			device.set_config(False, False)
			return

		for i in range(0, 7):
			if len(self.entries) > i:
				entry, _ = self.entries[i]
				l, r = self.lcd_pos(i)
				device.write_line(l, r, unicode_to_ks0066u(" " + entry)[0:9])
		if self.selected >= 0:
			l, r = self.lcd_pos(self.selected)
			device.write_line(l, r, "*")
			device.write_line(l, r, "")
			device.set_config(True, True)
		else:
			device.set_config(False, False)

	def on_button_escape(self):
		self.trace("escape")
		self.set_active(False)
		self.send('escape', None)

	def on_button_previous(self):
		self.set_selected(self.selected - 1)

	def on_button_next(self):
		self.set_selected(self.selected + 1)

	def on_button_enter(self):
		if self.selected >= 0 and self.selected < len(self.entries):
			label, name = self.entries[self.selected]
			self.trace("selected entry %s" % name)
			self.set_active(False)
			self.send(name, None)
