#!/usr/bin/python
# coding=utf-8

# -------------------------------------------------------------------
# ORBIT-Anwendungsbeispiel 101
#
# Eine ORBIT-Anwendung mit Geräteinitialisierer und -abschluss
# -------------------------------------------------------------------

# Hinweis: Für dieses Beispiel muss es einen Brick-Daemon geben, 
#          mit dem sich ORBIT verbinden kann und es muss ein 
#          LCD-20x4-Bricklet angeschlossen sein.

# Dieses Beispiel baut auf Anwendungsbeispiel 002 auf.

from sys import stdin

# Importieren der notwendigen Klassen von ORBIT
from orbit_framework import Core, Service
from orbit_framework.messaging import Slot

# Importieren einiger integrierten Komponenten
from orbit_framework.components.lcd import LCD20x4ButtonsComponent
from orbit_framework.jobs.apps import MessageApp

# Importieren der TInkerForge-Bindings für LCD 20x4
from tinkerforge.bricklet_lcd_20x4 import BrickletLCD20x4

# Den Anwendungskern instanzieren
core = Core()

# Geräteinitialisierung einrichten

def initialize_lcd_device(device):
	device.clear_display()
	device.backlight_on()

core.device_manager.add_device_initializer(
	BrickletLCD20x4.DEVICE_IDENTIFIER,
	initialize_lcd_device)

# Hinweis: Eine Geräteinitialisierungsfunktion wird immer dann
#          aufgerufen, wenn das angegebene Brick(let) neu erkannt
#          wird. Das geschieht beim Start der Anwendung und
#          wenn die Verbindung nach einem Verbindungsabbruch
#          wieder hergestellt wird.

# Geräteabschluss (Finalizer) einrichten

def finalize_lcd_device(device):
	device.backlight_off()
	device.clear_display()

core.device_manager.add_device_finalizer(
	BrickletLCD20x4.DEVICE_IDENTIFIER, 
	finalize_lcd_device)

# Hinweis: Eine Geräteabschlussfunktione wird aufgerufen,
#          wenn die Anwendung beendet wird. Sie wird nicht
#          aufgerufen, wenn ein Brick(let) wegen eines 
#          Vergbindungsabbruchs nicht mehr verfügbar ist.

# Anwendung mit Dienst und Apps (aus Beispiel 002)

service = Service('ButtonService')
service.add_component(
	LCD20x4ButtonsComponent('buttons'))
core.install(service)

app1 = MessageApp('MsgApp1', ['Nachricht 1'])
app1.add_activator(
	Slot('ButtonService', None, 'button_pressed',
		predicate = lambda j, c, n, v: v[1] == 1))
core.install(app1)

app2 = MessageApp('MsgApp2', ['Nachricht 2'])
app2.add_activator(
	Slot('ButtonService', None, 'button_pressed',
		predicate = lambda j, c, n, v: v[1] == 2))
core.install(app2)

core.default_application = app1

# Starten der Anwendung
core.start()

# Auf eine Benutzereingabe warten
print(u"\nZum Beenden ENTER drücken.\n")
stdin.readline()

# Stoppen der Anwendung 
core.stop()
