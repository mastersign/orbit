# Package orbit.devices

from tinkerforge.brick_dc import BrickDC
from tinkerforge.brick_imu import BrickIMU
from tinkerforge.brick_master import BrickMaster
from tinkerforge.brick_servo import BrickServo
from tinkerforge.brick_stepper import BrickStepper
from tinkerforge.bricklet_ambient_light import BrickletAmbientLight
from tinkerforge.bricklet_analog_in import BrickletAnalogIn
from tinkerforge.bricklet_analog_out import BrickletAnalogOut
from tinkerforge.bricklet_barometer import BrickletBarometer
from tinkerforge.bricklet_current12 import BrickletCurrent12
from tinkerforge.bricklet_current25 import BrickletCurrent25
from tinkerforge.bricklet_distance_ir import BrickletDistanceIR
from tinkerforge.bricklet_distance_us import BrickletDistanceUS
from tinkerforge.bricklet_dual_button import BrickletDualButton
from tinkerforge.bricklet_dual_relay import BrickletDualRelay
from tinkerforge.bricklet_gps import BrickletGPS
from tinkerforge.bricklet_hall_effect import BrickletHallEffect
from tinkerforge.bricklet_humidity import BrickletHumidity
from tinkerforge.bricklet_industrial_digital_in_4 import BrickletIndustrialDigitalIn4
from tinkerforge.bricklet_industrial_digital_out_4 import BrickletIndustrialDigitalOut4
from tinkerforge.bricklet_industrial_dual_0_20ma import BrickletIndustrialDual020mA
from tinkerforge.bricklet_industrial_quad_relay import BrickletIndustrialQuadRelay
from tinkerforge.bricklet_io4 import BrickletIO4
from tinkerforge.bricklet_io16 import BrickletIO16
from tinkerforge.bricklet_joystick import BrickletJoystick
from tinkerforge.bricklet_lcd_16x2 import BrickletLCD16x2
from tinkerforge.bricklet_lcd_20x4 import BrickletLCD20x4
from tinkerforge.bricklet_led_strip import BrickletLEDStrip
from tinkerforge.bricklet_line import BrickletLine
from tinkerforge.bricklet_linear_poti import BrickletLinearPoti
from tinkerforge.bricklet_moisture import BrickletMoisture
from tinkerforge.bricklet_motion_detector import BrickletMotionDetector
from tinkerforge.bricklet_multi_touch import BrickletMultiTouch
from tinkerforge.bricklet_piezo_buzzer import BrickletPiezoBuzzer
from tinkerforge.bricklet_piezo_speaker import BrickletPiezoSpeaker
from tinkerforge.bricklet_ptc import BrickletPTC
from tinkerforge.bricklet_remote_switch import BrickletRemoteSwitch
from tinkerforge.bricklet_rotary_encoder import BrickletRotaryEncoder
from tinkerforge.bricklet_rotary_poti import BrickletRotaryPoti
from tinkerforge.bricklet_segment_display_4x7 import BrickletSegmentDisplay4x7
from tinkerforge.bricklet_sound_intensity import BrickletSoundIntensity
from tinkerforge.bricklet_temperature import BrickletTemperature
from tinkerforge.bricklet_temperature_ir import BrickletTemperatureIR
from tinkerforge.bricklet_tilt import BrickletTilt
from tinkerforge.bricklet_voltage import BrickletVoltage
from tinkerforge.bricklet_voltage_current import BrickletVoltageCurrent

DEVICES = {
	BrickDC.DEVICE_IDENTIFIER: {'class': BrickDC, 'name': 'DC Brick'},
	BrickIMU.DEVICE_IDENTIFIER: {'class': BrickIMU, 'name': 'IMU Brick'},
	BrickMaster.DEVICE_IDENTIFIER: {'class': BrickMaster, 'name': 'Master Brick'},
	BrickServo.DEVICE_IDENTIFIER: {'class': BrickServo, 'name': 'Servo Brick'},
	BrickStepper.DEVICE_IDENTIFIER: {'class': BrickStepper, 'name': 'Stepper Brick'},
	BrickletAmbientLight.DEVICE_IDENTIFIER: {'class': BrickletAmbientLight, 'name': 'Ambient Light Bricklet'},
	BrickletAnalogIn.DEVICE_IDENTIFIER: {'class': BrickletAnalogIn, 'name': 'Analog In Bricklet'},
	BrickletAnalogOut.DEVICE_IDENTIFIER: {'class': BrickletAnalogOut, 'name': 'Analog Out Bricklet'},
	BrickletBarometer.DEVICE_IDENTIFIER: {'class': BrickletBarometer, 'name': 'Barometer Bricklet'},
	BrickletCurrent12.DEVICE_IDENTIFIER: {'class': BrickletCurrent12, 'name': 'Current 12.5A Bricklet'},
	BrickletCurrent25.DEVICE_IDENTIFIER: {'class': BrickletCurrent25, 'name': 'Current 25A Bricklet'},
	BrickletDistanceIR.DEVICE_IDENTIFIER: {'class': BrickletDistanceIR, 'name': 'Distance IR Bricklet'},
	BrickletDistanceUS.DEVICE_IDENTIFIER: {'class': BrickletDistanceUS, 'name': 'Distance US Bricklet'},
	BrickletDualButton.DEVICE_IDENTIFIER: {'class': BrickletDualButton, 'name': 'Dual Button Bricklet'},
	BrickletDualRelay.DEVICE_IDENTIFIER: {'class': BrickletDualRelay, 'name': 'Dual Relay Bricklet'},
	BrickletGPS.DEVICE_IDENTIFIER: {'class': BrickletGPS, 'name': 'GPS Bricklet'},
	BrickletHallEffect.DEVICE_IDENTIFIER: {'class': BrickletHallEffect, 'name': 'Hall Effect Bricklet'},
	BrickletHumidity.DEVICE_IDENTIFIER: {'class': BrickletHumidity, 'name': 'Humidity Bricklet'},
	BrickletIndustrialDigitalIn4.DEVICE_IDENTIFIER: {'class': BrickletIndustrialDigitalIn4, 'name': 'Industrial Digital In 4 Bricklet'},
	BrickletIndustrialDigitalOut4.DEVICE_IDENTIFIER: {'class': BrickletIndustrialDigitalOut4, 'name': 'Industrial Digital Out 4 Bricklet'},
	BrickletIndustrialDual020mA.DEVICE_IDENTIFIER: {'class': BrickletIndustrialDual020mA, 'name': 'Industrial Dual Relay Bricklet'},
	BrickletIndustrialQuadRelay.DEVICE_IDENTIFIER: {'class': BrickletIndustrialQuadRelay, 'name': 'Industrial Quad Relay Bricklet'},
	BrickletIO4.DEVICE_IDENTIFIER: {'class': BrickletIO4, 'name': 'IO-4 Bricklet'},
	BrickletIO16.DEVICE_IDENTIFIER: {'class': BrickletIO16, 'name': 'IO-16 Bricklet'},
	BrickletJoystick.DEVICE_IDENTIFIER: {'class': BrickletJoystick, 'name': 'Joystick Bricklet'},
	BrickletLCD16x2.DEVICE_IDENTIFIER: {'class': BrickletLCD16x2, 'name': 'LCD 16x2 Bricklet'},
	BrickletLCD20x4.DEVICE_IDENTIFIER: {'class': BrickletLCD20x4, 'name': 'LCD 20x4 Bricklet'},
	BrickletLEDStrip.DEVICE_IDENTIFIER: {'class': BrickletLEDStrip, 'name': 'LED Strip Bricklet'},
	BrickletLine.DEVICE_IDENTIFIER: {'class': BrickletLine, 'name': 'Line Sensor Bricklet'},
	BrickletLinearPoti.DEVICE_IDENTIFIER: {'class': BrickletLinearPoti, 'name': 'Linear Poti Bricklet'},
	BrickletMoisture.DEVICE_IDENTIFIER: {'class': BrickletMoisture, 'name': 'Moisture Bricklet'},
	BrickletMotionDetector.DEVICE_IDENTIFIER: {'class': BrickletMotionDetector, 'name': 'Motion Detector Bricklet'},
	BrickletMultiTouch.DEVICE_IDENTIFIER: {'class': BrickletMultiTouch, 'name': 'Multi Touch Bricklet'},
	BrickletPiezoBuzzer.DEVICE_IDENTIFIER: {'class': BrickletPiezoBuzzer, 'name': 'Piezo Buzzer Bricklet'},
	BrickletPiezoSpeaker.DEVICE_IDENTIFIER: {'class': BrickletPiezoSpeaker, 'name': 'Piezo Speaker Bricklet'},
	BrickletPTC.DEVICE_IDENTIFIER: {'class': BrickletPTC, 'name': 'PTC Bricklet'},
	BrickletRemoteSwitch.DEVICE_IDENTIFIER: {'class': BrickletRemoteSwitch, 'name': 'Remote Switch Bricklet'},
	BrickletRotaryEncoder.DEVICE_IDENTIFIER: {'class': BrickletRotaryEncoder, 'name': 'Rotary Encoder Bricklet'},
	BrickletRotaryPoti.DEVICE_IDENTIFIER: {'class': BrickletRotaryPoti, 'name': 'Rotary Poti Bricklet'},
	BrickletSegmentDisplay4x7.DEVICE_IDENTIFIER: {'class': BrickletSegmentDisplay4x7, 'name': 'Segment Display 4x7 Bricklet'},
	BrickletSoundIntensity.DEVICE_IDENTIFIER: {'class': BrickletSoundIntensity, 'name': 'Sound Intensity Bricklet'},
	BrickletTemperature.DEVICE_IDENTIFIER: {'class': BrickletTemperature, 'name': 'Temperature Bricklet'},
	BrickletTemperatureIR.DEVICE_IDENTIFIER: {'class': BrickletTemperatureIR, 'name': 'Temperature IR Bricklet'},
	BrickletTilt.DEVICE_IDENTIFIER: {'class': BrickletTilt, 'name': 'Tilt Bricklet'},
	BrickletVoltage.DEVICE_IDENTIFIER: {'class': BrickletVoltage, 'name': 'Voltage Bricklet'},
	BrickletVoltageCurrent.DEVICE_IDENTIFIER: {'class': BrickletVoltageCurrent, 'name': 'Voltage/Current Bricklet'}
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

def device_instance(device_identifier, uid, ipcon):
	if device_identifier in DEVICES:
		return DEVICES[device_identifier]['class'](uid, ipcon)
	else:
		raise KeyError("the given device identifier '%i' is unknown" % device_identifier)
