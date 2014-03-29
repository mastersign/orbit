# Package orbit.devices

DEVICES = {
	11: {'package': 'tinkerforge.brick_dc', 'class': 'BrickDC', 'name': 'DC Brick'},
	16: {'package': 'tinkerforge.brick_imu', 'class': 'BrickIMU', 'name': 'IMU Brick'},
	13: {'package': 'tinkerforge.brick_master', 'class': 'BrickMaster', 'name': 'Master Brick'},
	14: {'package': 'tinkerforge.brick_servo', 'class': 'BrickServo', 'name': 'Servo Brick'},
	15: {'package': 'tinkerforge.brick_stepper', 'class': 'BrickStepper', 'name': 'Stepper Brick'},
	21: {'package': 'tinkerforge.bricklet_ambient_light', 'class': 'BrickletAmbientLight', 'name': 'Ambient Light Bricklet'},
	219: {'package': 'tinkerforge.bricklet_analog_in', 'class': 'BrickletAnalogIn', 'name': 'Analog In Bricklet'},
	220: {'package': 'tinkerforge.bricklet_analog_out', 'class': 'BrickletAnalogOut', 'name': 'Analog Out Bricklet'},
	221: {'package': 'tinkerforge.bricklet_barometer', 'class': 'BrickletBarometer', 'name': 'Barometer Bricklet'},
	23: {'package': 'tinkerforge.bricklet_current12', 'class': 'BrickletCurrent12', 'name': 'Current 12.5A Bricklet'},
	24: {'package': 'tinkerforge.bricklet_current25', 'class': 'BrickletCurrent25', 'name': 'Current 25A Bricklet'},
	25: {'package': 'tinkerforge.bricklet_distance_ir', 'class': 'BrickletDistanceIR', 'name': 'Distance IR Bricklet'},
	229: {'package': 'tinkerforge.bricklet_distance_us', 'class': 'BrickletDistanceUS', 'name': 'Distance US Bricklet'},
	230: {'package': 'tinkerforge.bricklet_dual_button', 'class': 'BrickletDualButton', 'name': 'Dual Button Bricklet'},
	26: {'package': 'tinkerforge.bricklet_dual_relay', 'class': 'BrickletDualRelay', 'name': 'Dual Relay Bricklet'},
	222: {'package': 'tinkerforge.bricklet_gps', 'class': 'BrickletGPS', 'name': 'GPS Bricklet'},
	240: {'package': 'tinkerforge.bricklet_hall_effect', 'class': 'BrickletHallEffect', 'name': 'Hall Effect Bricklet'},
	27: {'package': 'tinkerforge.bricklet_humidity', 'class': 'BrickletHumidity', 'name': 'Humidity Bricklet'},
	223: {'package': 'tinkerforge.bricklet_industrial_digital_in_4', 'class': 'BrickletIndustrialDigitalIn4', 'name': 'Industrial Digital In 4 Bricklet'},
	224: {'package': 'tinkerforge.bricklet_industrial_digital_out_4', 'class': 'BrickletIndustrialDigitalOut4', 'name': 'Industrial Digital Out 4 Bricklet'},
	228: {'package': 'tinkerforge.bricklet_industrial_dual_0_20ma', 'class': 'BrickletIndustrialDual020mA', 'name': 'Industrial Dual Relay Bricklet'},
	225: {'package': 'tinkerforge.bricklet_industrial_quad_relay', 'class': 'BrickletIndustrialQuadRelay', 'name': 'Industrial Quad Relay Bricklet'},
	29: {'package': 'tinkerforge.bricklet_io4', 'class': 'BrickletIO4', 'name': 'IO-4 Bricklet'},
	28: {'package': 'tinkerforge.bricklet_io16', 'class': 'BrickletIO16', 'name': 'IO-16 Bricklet'},
	210: {'package': 'tinkerforge.bricklet_joystick', 'class': 'BrickletJoystick', 'name': 'Joystick Bricklet'},
	211: {'package': 'tinkerforge.bricklet_lcd_16x2', 'class': 'BrickletLCD16x2', 'name': 'LCD 16x2 Bricklet'},
	212: {'package': 'tinkerforge.bricklet_lcd_20x4', 'class': 'BrickletLCD20x4', 'name': 'LCD 20x4 Bricklet'},
	231: {'package': 'tinkerforge.bricklet_led_strip', 'class': 'BrickletLEDStrip', 'name': 'LED Strip Bricklet'},
	241: {'package': 'tinkerforge.bricklet_line', 'class': 'BrickletLine', 'name': 'Line Sensor Bricklet'},
	213: {'package': 'tinkerforge.bricklet_linear_poti', 'class': 'BrickletLinearPoti', 'name': 'Linear Poti Bricklet'},
	232: {'package': 'tinkerforge.bricklet_moisture', 'class': 'BrickletMoisture', 'name': 'Moisture Bricklet'},
	233: {'package': 'tinkerforge.bricklet_motion_detector', 'class': 'BrickletMotionDetector', 'name': 'Motion Detector Bricklet'},
	234: {'package': 'tinkerforge.bricklet_multi_touch', 'class': 'BrickletMultiTouch', 'name': 'Multi Touch Bricklet'},
	214: {'package': 'tinkerforge.bricklet_piezo_buzzer', 'class': 'BrickletPiezoBuzzer', 'name': 'Piezo Buzzer Bricklet'},
	242: {'package': 'tinkerforge.bricklet_piezo_speaker', 'class': 'BrickletPiezoSpeaker', 'name': 'Piezo Speaker Bricklet'},
	226: {'package': 'tinkerforge.bricklet_ptc', 'class': 'BrickletPTC', 'name': 'PTC Bricklet'},
	235: {'package': 'tinkerforge.bricklet_remote_switch', 'class': 'BrickletRemoteSwitch', 'name': 'Remote Switch Bricklet'},
	236: {'package': 'tinkerforge.bricklet_rotary_encoder', 'class': 'BrickletRotaryEncoder', 'name': 'Rotary Encoder Bricklet'},
	215: {'package': 'tinkerforge.bricklet_rotary_poti', 'class': 'BrickletRotaryPoti', 'name': 'Rotary Poti Bricklet'},
	237: {'package': 'tinkerforge.bricklet_segment_display_4x7', 'class': 'BrickletSegmentDisplay4x7', 'name': 'Segment Display 4x7 Bricklet'},
	238: {'package': 'tinkerforge.bricklet_sound_intensity', 'class': 'BrickletSoundIntensity', 'name': 'Sound Intensity Bricklet'},
	216: {'package': 'tinkerforge.bricklet_temperature', 'class': 'BrickletTemperature', 'name': 'Temperature Bricklet'},
	217: {'package': 'tinkerforge.bricklet_temperature_ir', 'class': 'BrickletTemperatureIR', 'name': 'Temperature IR Bricklet'},
	239: {'package': 'tinkerforge.bricklet_tilt', 'class': 'BrickletTilt', 'name': 'Tilt Bricklet'},
	218: {'package': 'tinkerforge.bricklet_voltage', 'class': 'BrickletVoltage', 'name': 'Voltage Bricklet'},
	227: {'package': 'tinkerforge.bricklet_voltage_current', 'class': 'BrickletVoltageCurrent', 'name': 'Voltage/Current Bricklet'}
}

NAMES = {}

for id in DEVICES.keys():
	DEVICES[id]['id'] = id
	NAMES[DEVICES[id]['name']] = id

def device_identifier_from_name(name):
	if name in NAMES:
		return NAMES[name]
	else:
		raise KeyError("the given device name '%s' is unknown" % name)

def get_device_identifier(name_or_id):
	if type(name_or_id) is int:
		return name_or_id
	elif type(name_or_id) is str:
		return device_identifier_from_name(name_or_id)
	else:
		raise ValueError("the given value is neither a string nor an integer")

def known_device(device_identifier):
	return device_identifier in DEVICES

def device_name(device_identifier):
	if device_identifier in DEVICES:
		return DEVICES[device_identifier]['name']
	else:
		return "Unknown Device"

LOAD_CLASSES = {}

def device_instance(device_identifier, uid, ipcon):
	if device_identifier in DEVICES:
		if device_identifier not in LOAD_CLASSES:
			device = DEVICES[device_identifier]
			module = __import__(device['package'], fromlist=[device['class']])
			clazz = getattr(module, device['class'])
			LOAD_CLASSES[device_identifier] = clazz
		else:
			clazz = LOAD_CLASSES[device_identifier]
		return clazz(uid, ipcon)
	else:
		raise KeyError("the given device identifier '%i' is unknown" % device_identifier)
