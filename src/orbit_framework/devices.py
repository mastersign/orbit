# coding=utf-8

## ORBIT ist ein Python-Framework für TinkerForge-Anwendungen
## Copyright (C) 2014 Tobias Kiertscher <dev@mastersign.de>
##
## This program is free software: you can redistribute it and/or modify
## it under the terms of the GNU Lesser General Public License as
## published by the Free Software Foundation, either version 3
## of the License, or (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU (Lesser) General
## Public License along with this program.
## If not, see <http://www.gnu.org/licenses/>.

# Module orbit_framework.devices

"""
Dieses Modul implementiert den Gerätemanager von ORBIT.

Das Modul umfasst die folgenden Klassen:

- :py:class:`DeviceManager`
- :py:class:`DeviceHandle`
- :py:class:`SingleDeviceHandle`
- :py:class:`MultiDeviceHandle`

Darüber hinaus enthält es einige Hilfsfunktionen für den Umgang
mit TinkerForge-Gerätetypen:

- :py:func:`get_device_identifier`
- :py:func:`device_identifier_from_name`
- :py:func:`device_instance`
- :py:func:`device_name`
- :py:func:`known_device`
"""

import time
from .tools import MulticastCallback
from tinkerforge.ip_connection import IPConnection, Error


DEVICES = {
    11: {'package': 'tinkerforge.brick_dc', 'class': 'BrickDC', 'name': 'DC Brick'},
    13: {'package': 'tinkerforge.brick_master', 'class': 'BrickMaster', 'name': 'Master Brick'},
    14: {'package': 'tinkerforge.brick_servo', 'class': 'BrickServo', 'name': 'Servo Brick'},
    15: {'package': 'tinkerforge.brick_stepper', 'class': 'BrickStepper', 'name': 'Stepper Brick'},
    16: {'package': 'tinkerforge.brick_imu', 'class': 'BrickIMU', 'name': 'IMU Brick'},
    21: {'package': 'tinkerforge.bricklet_ambient_light', 'class': 'BrickletAmbientLight', 'name': 'Ambient Light Bricklet'},
    23: {'package': 'tinkerforge.bricklet_current12', 'class': 'BrickletCurrent12', 'name': 'Current 12.5A Bricklet'},
    24: {'package': 'tinkerforge.bricklet_current25', 'class': 'BrickletCurrent25', 'name': 'Current 25A Bricklet'},
    25: {'package': 'tinkerforge.bricklet_distance_ir', 'class': 'BrickletDistanceIR', 'name': 'Distance IR Bricklet'},
    26: {'package': 'tinkerforge.bricklet_dual_relay', 'class': 'BrickletDualRelay', 'name': 'Dual Relay Bricklet'},
    27: {'package': 'tinkerforge.bricklet_humidity', 'class': 'BrickletHumidity', 'name': 'Humidity Bricklet'},
    29: {'package': 'tinkerforge.bricklet_io4', 'class': 'BrickletIO4', 'name': 'IO-4 Bricklet'},
    28: {'package': 'tinkerforge.bricklet_io16', 'class': 'BrickletIO16', 'name': 'IO-16 Bricklet'},
    111: {'package': 'tinkerforge.brick_hat', 'class': 'BrickHAT', 'name': 'HAT Brick'},
    112: {'package': 'tinkerforge.brick_hat_zero', 'class': 'BrickHATZero', 'name': 'HAT Zero Brick'},
    210: {'package': 'tinkerforge.bricklet_joystick', 'class': 'BrickletJoystick', 'name': 'Joystick Bricklet'},
    211: {'package': 'tinkerforge.bricklet_lcd_16x2', 'class': 'BrickletLCD16x2', 'name': 'LCD 16x2 Bricklet'},
    212: {'package': 'tinkerforge.bricklet_lcd_20x4', 'class': 'BrickletLCD20x4', 'name': 'LCD 20x4 Bricklet'},
    213: {'package': 'tinkerforge.bricklet_linear_poti', 'class': 'BrickletLinearPoti', 'name': 'Linear Poti Bricklet'},
    214: {'package': 'tinkerforge.bricklet_piezo_buzzer', 'class': 'BrickletPiezoBuzzer', 'name': 'Piezo Buzzer Bricklet'},
    215: {'package': 'tinkerforge.bricklet_rotary_poti', 'class': 'BrickletRotaryPoti', 'name': 'Rotary Poti Bricklet'},
    216: {'package': 'tinkerforge.bricklet_temperature', 'class': 'BrickletTemperature', 'name': 'Temperature Bricklet'},
    217: {'package': 'tinkerforge.bricklet_temperature_ir', 'class': 'BrickletTemperatureIR', 'name': 'Temperature IR Bricklet'},
    218: {'package': 'tinkerforge.bricklet_voltage', 'class': 'BrickletVoltage', 'name': 'Voltage Bricklet'},
    219: {'package': 'tinkerforge.bricklet_analog_in', 'class': 'BrickletAnalogIn', 'name': 'Analog In Bricklet'},
    220: {'package': 'tinkerforge.bricklet_analog_out', 'class': 'BrickletAnalogOut', 'name': 'Analog Out Bricklet'},
    221: {'package': 'tinkerforge.bricklet_barometer', 'class': 'BrickletBarometer', 'name': 'Barometer Bricklet'},
    222: {'package': 'tinkerforge.bricklet_gps', 'class': 'BrickletGPS', 'name': 'GPS Bricklet'},
    223: {'package': 'tinkerforge.bricklet_industrial_digital_in_4', 'class': 'BrickletIndustrialDigitalIn4', 'name': 'Industrial Digital In 4 Bricklet'},
    224: {'package': 'tinkerforge.bricklet_industrial_digital_out_4', 'class': 'BrickletIndustrialDigitalOut4', 'name': 'Industrial Digital Out 4 Bricklet'},
    225: {'package': 'tinkerforge.bricklet_industrial_quad_relay', 'class': 'BrickletIndustrialQuadRelay', 'name': 'Industrial Quad Relay Bricklet'},
    226: {'package': 'tinkerforge.bricklet_ptc', 'class': 'BrickletPTC', 'name': 'PTC Bricklet'},
    227: {'package': 'tinkerforge.bricklet_voltage_current', 'class': 'BrickletVoltageCurrent', 'name': 'Voltage/Current Bricklet'},
    228: {'package': 'tinkerforge.bricklet_industrial_dual_0_20ma', 'class': 'BrickletIndustrialDual020mA', 'name': 'Industrial Dual Relay Bricklet'},
    229: {'package': 'tinkerforge.bricklet_distance_us', 'class': 'BrickletDistanceUS', 'name': 'Distance US Bricklet'},
    230: {'package': 'tinkerforge.bricklet_dual_button', 'class': 'BrickletDualButton', 'name': 'Dual Button Bricklet'},
    231: {'package': 'tinkerforge.bricklet_led_strip', 'class': 'BrickletLEDStrip', 'name': 'LED Strip Bricklet'},
    232: {'package': 'tinkerforge.bricklet_moisture', 'class': 'BrickletMoisture', 'name': 'Moisture Bricklet'},
    233: {'package': 'tinkerforge.bricklet_motion_detector', 'class': 'BrickletMotionDetector', 'name': 'Motion Detector Bricklet'},
    234: {'package': 'tinkerforge.bricklet_multi_touch', 'class': 'BrickletMultiTouch', 'name': 'Multi Touch Bricklet'},
    235: {'package': 'tinkerforge.bricklet_remote_switch', 'class': 'BrickletRemoteSwitch', 'name': 'Remote Switch Bricklet'},
    236: {'package': 'tinkerforge.bricklet_rotary_encoder', 'class': 'BrickletRotaryEncoder', 'name': 'Rotary Encoder Bricklet'},
    237: {'package': 'tinkerforge.bricklet_segment_display_4x7', 'class': 'BrickletSegmentDisplay4x7', 'name': 'Segment Display 4x7 Bricklet'},
    238: {'package': 'tinkerforge.bricklet_sound_intensity', 'class': 'BrickletSoundIntensity', 'name': 'Sound Intensity Bricklet'},
    239: {'package': 'tinkerforge.bricklet_tilt', 'class': 'BrickletTilt', 'name': 'Tilt Bricklet'},
    240: {'package': 'tinkerforge.bricklet_hall_effect', 'class': 'BrickletHallEffect', 'name': 'Hall Effect Bricklet'},
    241: {'package': 'tinkerforge.bricklet_line', 'class': 'BrickletLine', 'name': 'Line Sensor Bricklet'},
    242: {'package': 'tinkerforge.bricklet_piezo_speaker', 'class': 'BrickletPiezoSpeaker', 'name': 'Piezo Speaker Bricklet'},
    243: {'package': 'tinkerforge.bricklet_color', 'class': 'BrickletColor', 'name': 'Color Bricklet'},
    244: {'package': 'tinkerforge.bricklet_solid_state_relay', 'class': 'BrickletSolidStateRelay', 'name': 'Solid State Relay Bricklet'},
    246: {'package': 'tinkerforge.bricklet_nfc_rfid', 'class': 'BrickletNFCRFID', 'name': 'NFC/RFID Bricklet'},
    249: {'package': 'tinkerforge.bricklet_industrial_dual_analog_in', 'class': 'BrickletIndustrialDualAnalogIn', 'name': 'Industrial Dual Analog In Bricklet'},
    250: {'package': 'tinkerforge.bricklet_accelerometer', 'class': 'BrickletAccelerometer', 'name': 'Accelerometer Bricklet'},
    251: {'package': 'tinkerforge.bricklet_analog_in_v2', 'class': 'BrickletAnalogInV2', 'name': 'Analog In Bricklet 2.0'},
    253: {'package': 'tinkerforge.bricklet_load_cell', 'class': 'BrickletLoadCell', 'name': 'Load Cell Bricklet'},
    254: {'package': 'tinkerforge.bricklet_rs232', 'class': 'BrickletRS232', 'name': 'RS232 Bricklet'},
    255: {'package': 'tinkerforge.bricklet_laser_range_finder', 'class': 'BrickletLaserRangeFinder', 'name': 'Laser Range Finder Bricklet'},
    256: {'package': 'tinkerforge.bricklet_analog_out_v2', 'class': 'BrickletAnalogOutV2', 'name': 'Analog Out Bricklet 2.0'},
    258: {'package': 'tinkerforge.bricklet_industrial_analog_out', 'class': 'BrickletIndustrialAnalogOut', 'name': 'Industrial Analog Out Bricklet'},
    259: {'package': 'tinkerforge.bricklet_ambient_light_v2', 'class': 'BrickletAmbientLightV2', 'name': 'Ambient Light Bricklet 2.0'},
    260: {'package': 'tinkerforge.bricklet_dust_detector', 'class': 'BrickletDustDetector', 'name': 'Dust Detector Bricklet'},
    262: {'package': 'tinkerforge.bricklet_co2', 'class': 'BrickletCO2', 'name': 'CO2 Bricklet'},
    263: {'package': 'tinkerforge.bricklet_oled_128x64', 'class': 'BrickletOLED128x64', 'name': 'OLED 128x64 Bricklet'},
    264: {'package': 'tinkerforge.bricklet_oled_64x48', 'class': 'BrickletOLED64x48', 'name': 'OLED 64x48 Bricklet'},
    265: {'package': 'tinkerforge.bricklet_uv_light', 'class': 'BrickletUVLight', 'name': 'UV Light Bricklet'},
    266: {'package': 'tinkerforge.bricklet_thermocouple', 'class': 'BrickletThermocouple', 'name': 'Thermocouple Bricklet'},
    267: {'package': 'tinkerforge.bricklet_motorized_linear_poti', 'class': 'BrickletMotorizedLinearPoti', 'name': 'Motorized Linear Poti Bricklet'},
    268: {'package': 'tinkerforge.bricklet_real_time_clock', 'class': 'BrickletRealTimeClock', 'name': 'Real-Time Clock Bricklet'},
    270: {'package': 'tinkerforge.bricklet_can', 'class': 'BrickletCAN', 'name': 'CAN Bricklet'},
    271: {'package': 'tinkerforge.bricklet_rgb_led', 'class': 'BrickletRGBLED', 'name': 'RGB LED Bricklet'},
    272: {'package': 'tinkerforge.bricklet_rgb_led_matrix', 'class': 'BrickletRGBLEDMatrix', 'name': 'RGB LED Matrix Bricklet'},
    276: {'package': 'tinkerforge.bricklet_gps_v2', 'class': 'BrickletGPSV2', 'name': 'GPS Bricklet 2.0'},
    277: {'package': 'tinkerforge.bricklet_rs485', 'class': 'BrickletRS485', 'name': 'RS485 Bricklet'},
    278: {'package': 'tinkerforge.bricklet_thermal_imaging', 'class': 'BrickletThermalImaging', 'name': 'Thermal Imaging Bricklet'},
    279: {'package': 'tinkerforge.bricklet_xmc1400_breakout', 'class': 'BrickletXMC1400Breakout', 'name': 'XMC1400 Breakout Bricklet'},
    282: {'package': 'tinkerforge.bricklet_rgb_led_button', 'class': 'BrickletRGBLEDButton', 'name': 'RGB LED Button Bricklet'},
    283: {'package': 'tinkerforge.bricklet_humidity_v2', 'class': 'BrickletHumidityV2', 'name': 'Humidity Bricklet 2.0'},
    284: {'package': 'tinkerforge.bricklet_industrial_dual_relay', 'class': 'BrickletIndustrialDualRelay', 'name': 'Industrial Dual Relay Bricklet'},
    285: {'package': 'tinkerforge.bricklet_dmx', 'class': 'BrickletDMX', 'name': 'DMX Bricklet'},
    286: {'package': 'tinkerforge.bricklet_nfc', 'class': 'BrickletNFC', 'name': 'NFC Bricklet'},
    288: {'package': 'tinkerforge.bricklet_outdoor_weather', 'class': 'BrickletOutdoorWeather', 'name': 'Outdoor Weather Bricklet'},
    289: {'package': 'tinkerforge.bricklet_remote_switch_v2', 'class': 'BrickletRemoteSwitchV2', 'name': 'Remote Switch Bricklet 2.0'},
    290: {'package': 'tinkerforge.bricklet_sound_pressure_level', 'class': 'BrickletSoundPressureLevel', 'name': 'Sound Pressure Level Bricklet'},
    291: {'package': 'tinkerforge.bricklet_temperature_ir_v2', 'class': 'BrickletTemperatureIRV2', 'name': 'Temperature IR Bricklet 2.0'},
    292: {'package': 'tinkerforge.bricklet_motion_detector_v2', 'class': 'BrickletMotionDetectorV2', 'name': 'Motion Detector Bricklet 2.0'},
    293: {'package': 'tinkerforge.bricklet_industrial_counter', 'class': 'BrickletIndustrialCounter', 'name': 'Industrial Counter Bricklet'},
    294: {'package': 'tinkerforge.bricklet_rotary_encoder_v2', 'class': 'BrickletRotaryEncoderV2', 'name': 'Rotary Encoder Bricklet 2.0'},
    295: {'package': 'tinkerforge.bricklet_analog_in_v3', 'class': 'BrickletAnalogInV3', 'name': 'Analog In Bricklet 3.0'},
    296: {'package': 'tinkerforge.bricklet_solid_state_relay_v2', 'class': 'BrickletSolidStateRelayV2', 'name': 'Solid State Relay Bricklet 2.0'},
    297: {'package': 'tinkerforge.bricklet_air_quality', 'class': 'BrickletAirQuality', 'name': 'Air Quality Bricklet'},
    298: {'package': 'tinkerforge.bricklet_lcd_128x64', 'class': 'BrickletLCD128x64', 'name': 'LCD 128x64 Bricklet'},
    299: {'package': 'tinkerforge.bricklet_distance_us_v2', 'class': 'BrickletDistanceUSV2', 'name': 'Distance US Bricklet 2.0'},
    2100: {'package': 'tinkerforge.bricklet_industrial_digital_in_4_v2', 'class': 'BrickletIndustrialDigitalIn4V2', 'name': 'Industrial Digital In 4 Bricklet 2.0'},
    2101: {'package': 'tinkerforge.bricklet_ptc_v2', 'class': 'BrickletPTCV2', 'name': 'PTC Bricklet 2.0'},
    2102: {'package': 'tinkerforge.bricklet_industrial_quad_relay_v2', 'class': 'BrickletIndustrialQuadRelayV2', 'name': 'Industrial Quad Relay Bricklet 2.0'},
    2103: {'package': 'tinkerforge.bricklet_led_strip_v2', 'class': 'BrickletLEDStripV2', 'name': 'LED Strip Bricklet 2.0'},
    2104: {'package': 'tinkerforge.bricklet_load_cell_v2', 'class': 'BrickletLoadCellV2', 'name': 'Load Cell Bricklet 2.0'},
    2105: {'package': 'tinkerforge.bricklet_voltage_current_v2', 'class': 'BrickletVoltageCurrentV2', 'name': 'Voltage/Current Bricklet 2.0'},
    2106: {'package': 'tinkerforge.bricklet_real_time_clock_v2', 'class': 'BrickletRealTimeClockV2', 'name': 'Real-Time Clock Bricklet 2.0'},
    2107: {'package': 'tinkerforge.bricklet_can_v2', 'class': 'BrickletCANV2', 'name': 'CAN Bricklet 2.0'},
    2108: {'package': 'tinkerforge.bricklet_rs232_v2', 'class': 'BrickletRS232V2', 'name': 'RS232 Bricklet 2.0'},
    2109: {'package': 'tinkerforge.bricklet_thermocouple_v2', 'class': 'BrickletThermocoupleV2', 'name': 'Thermocouple Bricklet 2.0'},
    2110: {'package': 'tinkerforge.bricklet_particulate_matter', 'class': 'BrickletParticulateMatter', 'name': 'Particulate Matter Bricklet'},
    2111: {'package': 'tinkerforge.bricklet_io4_v2', 'class': 'BrickletIO4V2', 'name': 'IO-4 Bricklet 2.0'},
    2112: {'package': 'tinkerforge.bricklet_oled_128x64_v2', 'class': 'BrickletOLED128x64V2', 'name': 'OLED 128x64 Bricklet 2.0'},
    2113: {'package': 'tinkerforge.bricklet_temperature_v2', 'class': 'BrickletTemperatureV2', 'name': 'Temperature Bricklet 2.0'},
    2114: {'package': 'tinkerforge.bricklet_io16_v2', 'class': 'BrickletIO16V2', 'name': 'IO-16 Bricklet 2.0'},
    2115: {'package': 'tinkerforge.bricklet_analog_out_v3', 'class': 'BrickletAnalogOutV3', 'name': 'Analog Out Bricklet 3.0'},
    2116: {'package': 'tinkerforge.bricklet_industrial_analog_out_v2', 'class': 'BrickletIndustrialAnalogOutV2', 'name': 'Industrial Analog Out Bricklet 2.0'},
    2117: {'package': 'tinkerforge.bricklet_barometer_v2', 'class': 'BrickletBarometerV2', 'name': 'Barometer Bricklet 2.0'},
    2118: {'package': 'tinkerforge.bricklet_uv_light_v2', 'class': 'BrickletUVLightV2', 'name': 'UV Light Bricklet 2.0'},
    2119: {'package': 'tinkerforge.bricklet_dual_button_v2', 'class': 'BrickletDualButtonV2', 'name': 'Dual Button Bricklet 2.0'},
    2120: {'package': 'tinkerforge.bricklet_industrial_dual_0_20ma_v2', 'class': 'BrickletIndustrialDual020mAV2', 'name': 'Industrial Dual 0-20mA Bricklet 2.0'},
    2121: {'package': 'tinkerforge.bricklet_industrial_dual_analog_in_v2', 'class': 'BrickletIndustrialDualAnalogInV2', 'name': 'Industrial Dual Analog In Bricklet 2.0'},
    2122: {'package': 'tinkerforge.bricklet_isolator', 'class': 'BrickletIsolator', 'name': 'Isolator Bricklet'},
    2123: {'package': 'tinkerforge.bricklet_one_wire', 'class': 'BrickletOneWire', 'name': 'One Wire Bricklet'},
    2124: {'package': 'tinkerforge.bricklet_industrial_digital_out_4_v2', 'class': 'BrickletIndustrialDigitalOut4V2', 'name': 'Industrial Digital Out 4 Bricklet 2.0'},
    2125: {'package': 'tinkerforge.bricklet_distance_ir_v2', 'class': 'BrickletDistanceIRV2', 'name': 'Distance IR Bricklet 2.0'},
    2127: {'package': 'tinkerforge.bricklet_rgb_led_v2', 'class': 'BrickletRGBLEDV2', 'name': 'RGB LED Bricklet 2.0'},
    2128: {'package': 'tinkerforge.bricklet_color_v2', 'class': 'BrickletColorV2', 'name': 'Color Bricklet 2.0'},
    2129: {'package': 'tinkerforge.bricklet_multi_touch_v2', 'class': 'BrickletMultiTouchV2', 'name': 'Multi Touch Bricklet 2.0'},
    2130: {'package': 'tinkerforge.bricklet_accelerometer_v2', 'class': 'BrickletAccelerometerV2', 'name': 'Accelerometer Bricklet 2.0'},
    2131: {'package': 'tinkerforge.bricklet_ambient_light_v3', 'class': 'BrickletAmbientLightV3', 'name': 'Ambient Light Bricklet 3.0'},
    2132: {'package': 'tinkerforge.bricklet_hall_effect_v2', 'class': 'BrickletHallEffectV2', 'name': 'Hall Effect Bricklet 2.0'},
    2137: {'package': 'tinkerforge.bricklet_segment_display_4x7_v2', 'class': 'BrickletSegmentDisplay4x7V2', 'name': 'Segment Display 4x7 Bricklet 2.0'},
    2138: {'package': 'tinkerforge.bricklet_joystick_v2', 'class': 'BrickletJoystickV2', 'name': 'Joystick Bricklet 2.0'},
    2139: {'package': 'tinkerforge.bricklet_linear_poti_v2', 'class': 'BrickletLinearPotiV2', 'name': 'Linear Poti Bricklet 2.0'},
    2140: {'package': 'tinkerforge.bricklet_rotary_poti_v2', 'class': 'BrickletRotaryPotiV2', 'name': 'Rotary Poti Bricklet 2.0'},
    2144: {'package': 'tinkerforge.bricklet_laser_range_finder_v2', 'class': 'BrickletLaserRangeFinderV2', 'name': 'Laser Range Finder Bricklet 2.0'},
    2145: {'package': 'tinkerforge.bricklet_piezo_speaker_v2', 'class': 'BrickletPiezoSpeakerV2', 'name': 'Piezo Speaker Bricklet 2.0'},
    2146: {'package': 'tinkerforge.bricklet_e_paper_296x128', 'class': 'BrickletEPaper296x128', 'name': 'E-Paper 296x128 Bricklet'},
    2147: {'package': 'tinkerforge.bricklet_co2_v2', 'class': 'BrickletCO2V2', 'name': 'CO2 Bricklet 2.0'},
    2152: {'package': 'tinkerforge.bricklet_energy_monitor', 'class': 'BrickletEnergyMonitor', 'name': 'Energy Monitor Bricklet'},
    2153: {'package': 'tinkerforge.bricklet_compass', 'class': 'BrickletCompass', 'name': 'Compass Bricklet'},
    2156: {'package': 'tinkerforge.bricklet_performance_dc', 'class': 'BrickletPerformanceDC', 'name': 'Performance DC Bricklet'},
    2157: {'package': 'tinkerforge.bricklet_servo_v2', 'class': 'BrickletServoV2', 'name': 'Servo Bricklet 2.0'},
    2161: {'package': 'tinkerforge.bricklet_imu_v3', 'class': 'BrickletIMUV3', 'name': 'IMU Bricklet 3.0'},
    2162: {'package': 'tinkerforge.bricklet_industrial_dual_ac_relay', 'class': 'BrickletIndustrialDualACRelay', 'name': 'Industrial Dual AC Relay Bricklet'},
    2164: {'package': 'tinkerforge.bricklet_industrial_ptc', 'class': 'BrickletIndustrialPTC', 'name': 'Industrial PTC Bricklet'},
    2165: {'package': 'tinkerforge.bricklet_dc_v2', 'class': 'BrickletDCV2', 'name': 'DC Bricklet 2.0'},
    2166: {'package': 'tinkerforge.bricklet_silent_stepper_v2', 'class': 'BrickletSilentStepperV2', 'name': 'Silent Stepper Bricklet 2.0'},
}

## initialize the name lookup table

NAMES = {}

for dev_id in DEVICES.keys():
    DEVICES[dev_id]['id'] = dev_id
    NAMES[DEVICES[dev_id]['name']] = dev_id


def device_identifier_from_name(name):
    """
    Gibt die Geräte-ID für einen Namen zurück.
    """
    if name in NAMES:
        return NAMES[name]
    else:
        raise KeyError("the given device name '%s' is unknown" % name)


def get_device_identifier(name_or_id):
    """
    Ermittelt die Geräte-ID für einen Gerätetyp.
    Es kann der Name des Gerätetyps oder die Geräte-ID übergeben werden.
    """
    if type(name_or_id) is int:
        return name_or_id
    elif type(name_or_id) is str:
        return device_identifier_from_name(name_or_id)
    else:
        raise ValueError("the given value is neither a string nor an integer")


def known_device(device_identifier):
    """
    Überprüft ob eine Geräte-ID bekannt ist.
    """
    return device_identifier in DEVICES


def device_name(device_identifier):
    """
    Gibt den Namen eines Gerätetyps anhand der Geräte-ID zurück.
    """
    if device_identifier in DEVICES:
        return DEVICES[device_identifier]['name']
    else:
        return "Unknown Device"


LOAD_CLASSES = {}


def device_instance(device_identifier, uid, ipcon):
    """
    Erzeugt eine TinkerForge-Binding-Instanz anhand
    der Geräte-ID, der UID und der Verbindung.
    """
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
        raise KeyError(
            "the given device identifier '%i' is unknown" % device_identifier)


class DeviceManager(object):
    """
    Diese Klasse implementiert den Gerätemanager einer ORBIT-Anwendung.

    **Parameter**

    ``core``
        Ein Verweis auf den Anwendungskern der ORBIT-Anwendung.
        Eine Instanz der Klasse :py:class:`Core`.

    **Beschreibung**

    Der Gerätemanager baut eine Verbindung zu einem TinkerForge-Server auf,
    ermittelt die angeschlossenen Bricks und Bricklets und stellt
    den Komponenten in den Jobs die jeweils geforderten Geräte zur Verfügung.

    Dabei behält der Gerätemanager die Kontrolle über den Gerätezugriff.
    Das bedeutet, dass der Gerätemanager die Autorität hat, einer Komponente
    ein Gerät zur Verfügung zu stellen, aber auch wieder zu entziehen.

    Eine Komponente bekommt ein von ihm angefordertes Gerät
    i.d.R. dann zugewiesen, wenn die Komponente aktiv
    und das Gerät verfügbar ist.
    Wird die Verbindung zum TinkerForge-Server unterbrochen oder verliert
    der TinkerForge-Server die Verbindung zum Master-Brick
    (USB-Kabel herausgezogen), entzieht der Gerätemanager der Komponente
    automatisch das Gerät, so dass eine Komponente i.d.R.
    keine Verbindungsprobleme behandeln muss.

    Umgesetzt wird dieses Konzept mit Hilfe der Klassen
    :py:class:`SingleDeviceHandle` und :py:class:`MultiDeviceHandle`.
    """

    def __init__(self, core):
        self._core = core
        self._connected = False
        self._devices = {}
        self._device_handles = []
        self._device_callbacks = {}
        self._device_initializers = {}
        self._device_finalizers = {}

        # initialize IP connection
        self._conn = IPConnection()
        self._conn.set_auto_reconnect(True)
        self._conn.register_callback(IPConnection.CALLBACK_ENUMERATE, self._cb_enumerate)
        self._conn.register_callback(IPConnection.CALLBACK_CONNECTED, self._cb_connected)
        self._conn.register_callback(IPConnection.CALLBACK_DISCONNECTED, self._cb_disconnected)

    def trace(self, text):
        """
        Schreibt eine Nachverfolgungsmeldung mit dem Ursprung ``DeviceManager``
        auf die Konsole.
        """
        if self._core.configuration.device_tracing:
            self._core._trace_function(text, 'DeviceManager')

    @property
    def devices(self):
        """
        Ein Dictionary mit allen zur Zeit verfügbaren Geräten.
        Die UID des Geräts ist der Schlüssel und der Wert ist eine Instanz
        der TinkerForge-Geräte-Klasse
        (wie z.B. ``tinkerforge.bricklet_lcd_20x4.BrickletLCD20x4``).
        """
        return self._devices

    def start(self):
        """
        Startet den Gerätemanager und baut eine Verbindung zu einem TinkerForge-Server auf.
        Die Verbindungdaten für den Server werden der ORBIT-Konfiguration entnommen.

        Gibt ``True`` zurück, wenn die Verbindung aufgebaut werden konnte, sonst ``False``.

        Siehe auch: :py:meth:`stop`
        """
        if self._conn.get_connection_state() == IPConnection.CONNECTION_STATE_DISCONNECTED:
            host = self._core.configuration.host
            port = self._core.configuration.port
            retry_time = self._core.configuration.connection_retry_time
            self.trace("connecting to %s:%d ..." % (host, port))
            connected = False
            while not connected:
                try:
                    self._conn.connect(host, port)
                    connected = True
                except KeyboardInterrupt:
                    connected = False
                    break
                except:
                    connected = False
                    self.trace("... connection failed, waiting %d, retry ..." % retry_time)
                    try:
                        time.sleep(retry_time)
                    except KeyboardInterrupt:
                        break
            if connected:
                self.trace("... connected")
            return connected

    def stop(self):
        """
        Trennt die Verbindung zum TinkerForge-Server und beendet den Gerätemanager.

        Vor dem Trennen der Verbindung wird die Zuordnung zwischen den Geräten
        und den Komponenten aufgehoben.

        Siehe auch: :py:meth:`start`
        """
        self._finalize_and_unbind_devices()
        if self._conn.get_connection_state() != IPConnection.CONNECTION_STATE_DISCONNECTED:
            self.trace("disconnecting")
            self._conn.disconnect()

    def _cb_enumerate(self, uid, connected_uid, position, hardware_version,
                      firmware_version, device_identifier, enumeration_type):

        if enumeration_type == IPConnection.ENUMERATION_TYPE_AVAILABLE or \
                enumeration_type == IPConnection.ENUMERATION_TYPE_CONNECTED:
            # initialize device configuration and bindings
            self.trace("device present '%s' [%s]" % (device_name(device_identifier), uid))
            if known_device(device_identifier):
                # bind device and notify components
                self._bind_device(device_identifier, uid)
            else:
                self.trace("could not create a device binding for device identifier " + str(device_identifier))
        if enumeration_type == IPConnection.ENUMERATION_TYPE_DISCONNECTED:
            # recognize absence of device
            self.trace("device absent '%s' [%s]" % (device_name(device_identifier), uid))
            # unbind device and notify components
            self._unbind_device(uid)

    def _cb_connected(self, reason):
        self._connected = True
        # recognize connection
        if reason == IPConnection.CONNECT_REASON_AUTO_RECONNECT:
            self.trace("connection established (auto reconnect)")
        else:
            self.trace("connection established")
        # enumerate devices
        self._conn.enumerate()

    def _cb_disconnected(self, reason):
        self._connected = False
        # recognize lost connection
        if reason == IPConnection.DISCONNECT_REASON_ERROR:
            self.trace("connection lost (error)")
        elif reason == IPConnection.DISCONNECT_REASON_SHUTDOWN:
            self.trace("connection lost (shutdown)")
        else:
            self.trace("connection lost")

    def _bind_device(self, device_identifier, uid):
        self.trace("binding '%s' [%s]" %
                   (device_name(device_identifier), uid))
        # create binding instance
        device = device_instance(device_identifier, uid, self._conn)
        # add passive identity attribute
        identity = device.get_identity()
        device.identity = identity
        # initialize device
        self._initialize_device(device)
        # store reference to binding instance
        self.devices[uid] = device
        # register callbacks

        if uid in self._device_callbacks:
            callbacks = self._device_callbacks[uid]
            for event in callbacks:
                self.trace("binding dispatcher to '%s' [%s] (%s)" %
                           (device_name(device_identifier), uid, event))
                mcc = callbacks[event]
                device.register_callback(
                    event, lambda *pargs, **nargs: mcc(*pargs, device=device, **nargs))
        # notify device handles
        for device_handle in self._device_handles:
            device_handle.on_bind_device(device)

    def _unbind_device(self, uid):
        if uid in self._devices:
            device = self._devices[uid]
            self.trace("unbinding '%s' [%s]" %
                       (device_name(device.identity[5]), uid))
            # notify device handles
            for device_handle in self._device_handles:
                device_handle.on_unbind_device(device)
            # delete reference to binding interface
            del (self._devices[uid])

            # delete reference to multicast callbacks
            if uid in self._device_callbacks:
                del (self._device_callbacks[uid])
        else:
            self.trace("attempt to unbind not bound device [%s]" % uid)

    def _finalize_and_unbind_devices(self):
        for uid in list(self._devices.keys()):
            self._finalize_device(self._devices[uid])
            self._unbind_device(uid)

    def add_device_initializer(self, device_identifier, initializer):
        """
        Richtet eine Initialisierungsfunktion für einen Brick- oder Bricklet-Typ ein.

        **Parameter**

        ``device_identifier``
            Die Geräte-ID der TinkerForge-API.
            Z.B. ``tinkerforge.bricklet_lcd_20x4.BrickletLCD20x4.DEVICE_IDENTIFIER``
        ``initializer``
            Eine Funktion, welche als Parameter eine Instanz der TinkerForge-Geräteklasse
            entgegennimmt.

        **Beschreibung**

        Sobald der Gerätemanager ein neues Gerät entdeckt,
        zu dem er bisher keine Verbindung aufgebaut hatte,
        ruft er alle Initialisierungsfunktionen für die entsprechende
        Geräte-ID auf.

        *Siehe auch:*
        :py:meth:`add_device_finalizer`
        """
        if device_identifier not in self._device_initializers:
            self._device_initializers[device_identifier] = []
        self._device_initializers[device_identifier].append(initializer)
        self.trace("added initializer for '%s'" %
                   (device_name(device_identifier)))

    def _initialize_device(self, device):
        device_identifier = device.identity[5]
        if device_identifier in self._device_initializers:
            self.trace("initializing '%s' [%s]" %
                       (device_name(device.identity[5]), device.identity[0]))
            for initializer in self._device_initializers[device_identifier]:
                try:
                    initializer(device)
                except Error as err:
                    if err.value != -8:  # connection lost
                        self.trace("Error during initialization of : %s" % err.description)
                except Exception as exc:
                    self.trace("Exception caught during device initialization:\n%s" % exc)

    def add_device_finalizer(self, device_identifier, finalizer):
        """
        Richtet eine Abschlussfunktion für einen Brick- oder Bricklet-Typ ein.

        **Parameter**

        ``device_identifier``
            Die Geräte-ID der TinkerForge-API.
            Z.B. ``tinkerforge.bricklet_lcd_20x4.BrickletLCD20x4.DEVICE_IDENTIFIER``
        ``finalizer``
            Eine Funktion, welche als Parameter eine Instanz der TinkerForge-Geräteklasse
            entgegennimmt.

        **Beschreibung**

        Sobald der Gerätemanager die Verbindung zu einem Gerät selbstständig
        aufgibt (d.h. die Verbindung nicht durch eine Störung unterbrochen wurde),
        ruft er alle Abschlussfunktionen für die entsprechende
        Geräte-ID auf.

        *Siehe auch:*
        :py:meth:`add_device_initializer`
        """
        if device_identifier not in self._device_finalizers:
            self._device_finalizers[device_identifier] = []
        self._device_finalizers[device_identifier].append(finalizer)
        self.trace("added finalizer for '%s'" %
                   device_name(device_identifier))

    def _finalize_device(self, device):
        device_identifier = device.identity[5]
        if device_identifier in self._device_finalizers:
            self.trace("finalizing '%s' [%s]" %
                       (device_name(device.identity[5]), device.identity[0]))
            for finalizer in self._device_finalizers[device_identifier]:
                try:
                    finalizer(device)
                except Error as err:
                    if err.value != -8:  # connection lost
                        self.trace("Error during device finalization: %s" % err.description)
                except Exception as exc:
                    self.trace("Exception caught during device finalization:\n%s" % exc)

    def add_handle(self, device_handle):
        """
        Richtet eine Geräteanforderung (Geräte-Handle) ein.

        Eine Geräteanforderung ist eine Instanz einer Sub-Klasse
        von :py:class:`DeviceHandle`. Das kann entweder eine Instanz von
        :py:class:`SingleDeviceHandle` oder von :py:class:`MultiDeviceHandle` sein.

        Das übergebene Geräte-Handle wird über alle neu entdeckten Geräte
        mit einem Aufruf von :py:meth:`DeviceHandle.on_bind_device` benachrichtigt.
        Je nach Konfiguration nimmt das Handle das neue Gerät an oder ignoriert es.
        Verliert der Gerätemanager die Verbindung zu einem Gerät, wird das
        Geräte-Handle ebenfalls mit einem Aufruf von
        :py:meth:`DeviceHandle.on_unbind_device` benachrichtigt.

        *Siehe auch:*
        :py:meth:`remove_handle`
        """
        if device_handle in self._device_handles:
            return
        self._device_handles.append(device_handle)
        device_handle.on_add_handle(self)
        for device in list(self._devices.values()):
            device_handle.on_bind_device(device)

    def remove_handle(self, device_handle):
        """
        Entfernt eine Geräteanforderung (Geräte-Handle).

        Eine Geräteanforderung ist eine Instanz einer Sub-Klasse
        von :py:class:`DeviceHandle`. Das kann entweder eine Instanz von
        :py:class:`SingleDeviceHandle` oder von :py:class:`MultiDeviceHandle` sein.

        *Siehe auch:*
        :py:meth:`add_handle`
        """
        if device_handle not in self._device_handles:
            return
        for device in list(self._devices.values()):
            device_handle.on_unbind_device(device)
        device_handle.on_remove_handle()
        self._device_handles.remove(device_handle)

    def add_device_callback(self, uid, event, callback):
        """
        Richtet eine Callback-Funktion für ein Ereignis
        eines Bricks oder eines Bricklets ein.

        **Parameter**

        ``uid``
            Die UID des Gerätes für das ein Ereignis abgefangen werden soll.
        ``event``
            Die ID für das abzufangene Ereignis.
            Z.B. ``tinkerforge.bricklet_lcd_20x4.BrickletLCD20x4.CALLBACK_BUTTON_PRESSED``
        ``callback``
            Eine Callback-Funktion die bei Auftreten des Ereignisses aufgerufen werden soll.

        **Beschreibung**

        Da jedes Ereignis andere Ereignisparameter besitzt,
        muss die richtige Signatur für die Callback-Funktion der TinkerForge-Dokumentation
        entnommen werden. Die Ereignisparameter werden in der API-Dokumentation
        für jeden Brick und jedes Bricklet im Abschnitt *Callbacks* beschrieben.

        .. note:: Der Gerätemanager stellt einen zentralen
            Mechanismus für die Registrierung von Callbacks
            für Geräteereignisse zur Verfügung, weil die
            TinkerForge-Geräteklassen nur ein Callback per Ereignis
            zulassen. Der Gerätemanager hingegen unterstützt beliebig viele
            Callbacks für ein Ereignis eines Gerätes.

        *Siehe auch:*
        :py:meth:`remove_device_callback`
        """
        if uid not in self._device_callbacks:
            self._device_callbacks[uid] = {}

        callbacks = self._device_callbacks[uid]

        if event not in callbacks:
            self.trace("creating dispatcher for [%s] (%s)" % (uid, event))
            mcc = MulticastCallback()
            callbacks[event] = mcc
            if uid in self._devices:
                device = self._devices[uid]
                self.trace("binding dispatcher to [%s] (%s)" % (uid, event))
                device.register_callback(
                    event, lambda *pargs, **nargs: mcc(*pargs, device=device, **nargs))

        mcc = callbacks[event]
        self.trace("adding callback to dispatcher for [%s] (%s)" % (uid, event))
        mcc.add_callback(callback)

    def remove_device_callback(self, uid, event, callback):
        """
        Entfernt eine Callback-Funktion von einem Ereignis
        eines Bricks oder eines Bricklets.

        **Parameter**

        ``uid``
            Die UID des Gerätes für das ein Callback aufgehoben werden soll.
        ``event``
            Die ID für das Ereignis.
            Z.B. ``tinkerforge.bricklet_lcd_20x4.BrickletLCD20x4.CALLBACK_BUTTON_PRESSED``
        ``callback``
            Die registrierte Callback-Funktion die entfernt werde soll.

        **Beschreibung**

        Für die Aufhebung des Callbacks muss die gleiche Funktionsreferenz übergeben werden
        wie bei der Einrichtung des Callback.

        *Siehe auch:*
        :py:meth:`add_device_callback`
        """
        if uid in self._device_callbacks:
            callbacks = self._device_callbacks[uid]
            if event in callbacks:
                mcc = callbacks[event]
                self.trace("removing callback from dispatcher for [%s] (%s)" % (uid, event))
                mcc.remove_callback(callback)


class DeviceHandle(object):
    """
    Diese Klasse ist die Basisklasse für Geräteanforderungen.

    Anstelle diese Klasse direkt zu verwenden, werden die beiden Kindklassen
    :py:class:`SingleDeviceHandle` und :py:class:`MultiDeviceHandle`
    verwendet.

    **Parameter**

    ``name``
        Der Name der Geräteanforderung.
        Dieser Name hilft, verschiedene Geräte, die von einer Komponente
        angesteuert werden, zu unterscheiden.
    ``bind_callback``
        Eine Funktion, die aufgerufen wird, sobald die Verbindung zu einem
        Gerät verfügbar ist.
    ``unbind_callback``
        Eine Funktion, die aufgerufen wird, sobald eine Verbindung zu einem
        Gerät verloren geht.

    **Beschreibung**

    Eine Geräteanforderung repräsentiert die Fähigkeit einer Komponente
    mit einem Typ von TinkerForge-Brick(let)s zu kommunizieren.
    Sie entbindet die Komponente aber von der Aufgabe die Verbindung
    zu den Brick(let)s zu verwalten.
    Die Komponente wird durch Callbacks darüber informiert,
    ab wann ein Brick(let) verfügbar ist und ab wann es nicht
    mehr verfügbar ist.
    Eine Geräteanforderung kann mehrere Brick(let)s gleichen Typs
    umfassen.
    Eine Komponente kann jederzeit alle verfügbaren Brick(let)s einer
    Geräteanforderung abfragen und ansteuern.

    Geräteanforderungen verwalten auch Ereignis-Callbacks für Brick(let)s.
    Eine Komponente kann durch den Aufruf von :py:meth:`register_callback`
    ein Callback für ein Brick(let)-Ereignis einrichten und die Geräteanforderung
    übernimmt gemeinsam mit dem :py:class:`DeviceManager` die Verwaltung.

    *Siehe auch:*
    :py:class:`SingleDeviceHandle`,
    :py:class:`MultiDeviceHandle`,
    :py:meth:`orbit_framework.Component.add_device_handle`,
    :py:meth:`register_callback`
    """

    def __init__(self, name, bind_callback, unbind_callback):
        self._name = name
        self._bind_callback = bind_callback
        self._unbind_callback = unbind_callback
        self._devices = []
        self._callbacks = {}
        self._device_manager = None

    @property
    def name(self):
        """
        Gibt den Namen der Geräteanforderung zurück.
        """
        return self._name

    @property
    def devices(self):
        """
        Gibt eine Liste mit allen verfügbaren Brick(let)s zurück.

        Ein Brick(let) wird durch ein Objekt der entsprechenden
        TinkerForge-Geräteklasse
        (wie z.B. ``tinkerforge.bricklet_lcd_20x4.BrickletLCD20x4``)
        repräsentiert.
        """
        return self._devices

    def on_add_handle(self, device_manager):
        """
        Wird aufgerufen, wenn die Geräteanforderung im :py:class:`DeviceManager`
        registriert wurde.

        .. note::
            Kann von einer abgeleiteten Klasse überschrieben werden.
            Eine überschreibende Methode muss jedoch die Implementierung der
            Elternklasse aufrufen.

        *Siehe auch:*
        :py:meth:`DeviceManager.add_handle`,
        :py:meth:`on_remove_handle`
        """
        self._device_manager = device_manager

    def on_remove_handle(self):
        """
        Wird aufgerufen, wenn die Geräteanforderung im :py:class:`DeviceManager`
        deregistriert wurde.

        .. note::
            Kann von einer abgeleiteten Klasse überschrieben werden.
            Eine überschreibende Methode muss jedoch die Implementierung der
            Elternklasse aufrufen.

        *Siehe auch:*
        :py:meth:`DeviceManager.remove_handle`,
        :py:meth:`on_add_handle`
        """
        self._device_manager = None

    def on_bind_device(self, device):
        """
        Wird aufgerufen, wenn ein beliebiges Gerät verfügbar wird.

        .. note::
            Muss von einer abgeleiteten Klasse überschrieben werden.

        Eine Implementierung muss die Methode :py:meth:`accept_device`
        für alle Geräte aufrufen, die der Geräteanforderung entsprechen.

        *Siehe auch:*
        :py:meth:`accept_device`
        """
        raise Exception("Not implented. Must be overridden in a child class.")

    def accept_device(self, device):
        """
        Nimmt ein Gerät in die Geräteanforderung auf.
        Wird von :py:meth:`on_bind_device` aufgerufen.

        *Siehe auch:*
        :py:meth:`on_bind_device`
        """
        self._device_manager.trace("binding '%s' [%s] to handle '%s'" \
                                   % (device_name(device.identity[5]), device.identity[0], self.name))

        self.devices.append(device)

        for event_code in self._callbacks:
            self._install_callback(
                device, event_code, self._callbacks[event_code])

        if self._bind_callback:
            self._bind_callback(device)

    def on_unbind_device(self, device):
        """
        Wird aufgerufen, wenn ein beliebiges Gerät nicht mehr verfügbar ist.

        Ruft die Methode :py:meth:`release_device` auf, wenn das
        Gerät in dieser Geräteanforderung gebunden ist.

        *Siehe auch:*
        :py:meth:`release_device`
        """
        if device not in self.devices:
            return
        self.release_device(device)

    def release_device(self, device):
        """
        Wird aufgerufen, wenn ein Gerät aus der Geräteanforderung
        nicht mehr verfügbar ist.

        .. note::
            Kann von einer abgeleiteten Klasse überschrieben werden.
            Eine überschreibende Methode muss jedoch die Implementierung
            der Elternklasse aufrufen.

        *Siehe auch:*
        :py:meth:`on_unbind_device`
        """
        self._device_manager.trace("unbinding '%s' [%s] from handle '%s'" \
                                   % (device_name(device.identity[5]), device.identity[0], self.name))

        if self._unbind_callback:
            self._unbind_callback(device)

        for event_code in self._callbacks:
            self._uninstall_callback(
                device, event_code)

        self.devices.remove(device)

    def for_each_device(self, f):
        """
        Führt eine Funktion für alle verfügbaren Geräte
        dieser Geräteanforderung aus.
        """
        for d in self.devices:
            try:
                f(d)
            except Error as err:
                if err.value != -8:  # connection lost
                    if self._device_manager:
                        self._device_manager.trace(err.description)
                    else:
                        print(err.description)

    def _install_callback(self, device, event_code, callback):
        self._device_manager.add_device_callback(
            device.identity[0], event_code, callback)

    def _uninstall_callback(self, device, event_code):
        callback = self._callbacks[event_code]
        self._device_manager.remove_device_callback(
            device.identity[0], event_code, callback)

    def register_callback(self, event_code, callback):
        """
        Richtet ein Callback für ein Brick(let)-Ereignis ein.

        **Parameter**

        ``event_code``
            Der Code für das Brick(let)-Ereignis.
            Der Code kann der TinkerForge-Dokumentation entnommen werden.
            (Z.B. ``tinkerforge.bricklet_lcd_20x4.BrickletLCD20x4.CALLBACK_BUTTON_PRESSED``)
        ``callback``
            Das Callback, das bei Eintreten des Ereignisses aufgerufen
            werden soll.
            Die Signatur muss dem Ereignis entsprechen und ist der
            TinkerForge-Dokumentation zu entnehmen.

        **Beschreibung**

        Für jeden Ereignis-Code kann in jeder Geräteanforderung
        immer nur ein Callback registriert werden.
        Das Callback wird immer aufgerufen, sobald ein verfügbares Brick(let)
        dieser Geräteanforderung das beschriebene Ereignis auslöst.

        *Siehe auch:*
        :py:meth:`unregister_callback`,
        :py:meth:`DeviceManager.add_device_callback`
        """
        self.unregister_callback(event_code)
        self._callbacks[event_code] = callback
        if self._device_manager:
            self.for_each_device(
                lambda device: self._install_callback(
                    device, event_code, callback))

    def unregister_callback(self, event_code):
        """
        Meldet ein Callback von einem Brick(let)-Ereignis ab.

        **Parameter**

        ``event_code``
            Der Code für das Brick(let)-Ereignis.

        *Siehe auch:*
        :py:meth:`register_callback`,
        :py:meth:`DeviceManager.remove_device_callback`
        """
        if event_code not in self._callbacks:
            return
        if self._device_manager:
            self.for_each_device(
                lambda device: self._uninstall_callback(
                    device, event_code))
        del (self._callbacks[event_code])


class SingleDeviceHandle(DeviceHandle):
    """
    Eine Geräteanforderung für ein einzelnes Brick(let).

    **Parameter**

    ``name``
        Der Name der Geräteanforderung.
        Der Name wird zur Unterscheidung von mehreren Geräteanforderungen
        einer Komponente verwendet.
    ``device_name_or_id``
        Der Typenname oder die Typen-ID des Gerätes.
        Wird eine Zeichenkette übergeben, wird sie als Name des Brick(let)s
        interpretiert, z.B. ``'LCD 20x4 Bricklet'``.
        Wird eine Zahl übergeben, wird sie als Typen-ID interpretiert,
        z.B. ``tinkerforge.bricklet_lcd_20x4.BrickletLCD20x4.DEVICE_IDENTIFIER``.
    ``bind_callback`` (*optional*)
        Ein Callback das aufgerufen wird, sobald ein Gerät an die
        Geräteanforderung gebunden wird.
        Der Standardwert ist ``None``.
    ``unbind_callback`` (*optional*)
        Ein Callback das aufgerufen wird, sobald ein gebundenes Gerät
        nicht mehr verfügbar ist.
        Der Standardwert ist ``None``.
    ``uid`` (*optional*)
        Die UID eines Brick(let)s. Wenn eine UID angegeben wird,
        akzeptiert die Geräteanforderung nur genau dieses Brick(let).
        Wenn keine UID angegeben wird, wird das erste Gerät mit dem
        angegebenen Gerätetyp akzeptiert.
        Der Standardwert ist ``None``.
    ``auto_fix`` (*optional*)
        Gibt an, ob nach der Bindung zwischen einem Gerät und der Geräteanforderung
        andere Geräte gebunden werden dürfen.

        Mögliche Werte sind ``True``, wenn nach dem ersten gebundenen Gerät
        andere Geräte gebunden werden dürfen, und ``False``,
        wenn nach einer Bindung nur noch dieses Gerät gebunden werden darf.
        Der Standardwert ist ``False``.

    **Beschreibung**

    Diese Variante einer Geräteanforderung akzeptiert zu jeder Zeit
    immer nur ein Gerät.
    Wird keine UID angegeben, um ein konkretes Brick(let) zu beschreiben,
    wird das erste Brick(let) des angegebenen Gerätetyps aktzeptiert.
    Wird die Verbindung zum gebundenen Gerät getrennt, entscheidet der
    Parameter ``auto_fix`` ob anschließend das nächste verfügbare
    Gerät mit dem passenden Typ akzeptiert wird oder ob solange gewartet
    wird, bis das vormals gebundene Brick(let) wieder verfügbar wird.

    *Siehe auch:*
    :py:class:`DeviceHandle`,
    :py:class:`MultiDeviceHandle`
    """

    def __init__(self, name, device_name_or_id,
                 bind_callback=None, unbind_callback=None,
                 uid=None, auto_fix=False):

        super(SingleDeviceHandle, self).__init__(name, bind_callback, unbind_callback)
        self._device_identifier = get_device_identifier(device_name_or_id)
        self._uid = uid
        self._auto_fix = auto_fix
        self._device = None

    @property
    def device(self):
        """
        Gibt das gebundene Brick(let) oder ``None`` zurück.

        Ein Brick(let) wird durch ein Objekt der entsprechenden
        TinkerForge-Geräteklasse
        (wie z.B. ``tinkerforge.bricklet_lcd_20x4.BrickletLCD20x4``)
        repräsentiert.
        """
        return self._device

    def on_bind_device(self, device):
        if len(self.devices) > 0:
            return
        if device.identity[5] != self._device_identifier:
            return
        if self._uid is None:
            if self._auto_fix:
                self._uid = device.identity[0]
        elif device.identity[0] != self._uid:
            return
        self._device = device
        self.accept_device(device)

    def release_device(self, device):
        super(SingleDeviceHandle, self).release_device(device)
        if self._device == device:
            self._device = None


class MultiDeviceHandle(DeviceHandle):
    """
    Eine Geräteanforderung für alle Brick(let)s eines Typs.

    **Parameter**

    ``name``
        Der Name der Geräteanforderung.
        Der Name wird zur Unterscheidung von mehreren Geräteanforderungen
        einer Komponente verwendet.
    ``device_name_or_id``
        Der Typenname oder die Typen-ID des Gerätes.
        Wird eine Zeichenkette übergeben, wird sie als Name des Brick(let)s
        interpretiert, z.B. ``'LCD 20x4 Bricklet'``.
        Wird eine Zahl übergeben, wird sie als Typen-ID interpretiert,
        z.B. ``tinkerforge.bricklet_lcd_20x4.BrickletLCD20x4.DEVICE_IDENTIFIER``.
    ``bind_callback`` (*optional*)
        Ein Callback das aufgerufen wird, sobald ein Gerät an die
        Geräteanforderung gebunden wird.
    ``unbind_callback`` (*optional*)
        Ein Callback das aufgerufen wird, sobald ein gebundenes Gerät
        nicht mehr verfügbar ist.

    **Beschreibung**

    Diese Variante einer Geräteanforderung akzeptiert alle Geräte des
    angegebenen Gerätetyps.

    *Siehe auch:*
    :py:class:`DeviceHandle`,
    :py:class:`SingleDeviceHandle`
    """

    def __init__(self, name, device_name_or_id, bind_callback=None, unbind_callback=None):
        super(MultiDeviceHandle, self).__init__(name, bind_callback, unbind_callback)
        self._device_identifier = get_device_identifier(device_name_or_id)

    def on_bind_device(self, device):
        if not device.identity[5] == self._device_identifier:
            return
        self.accept_device(device)
