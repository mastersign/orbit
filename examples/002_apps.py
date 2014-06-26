#!/usr/bin/python
# coding=utf-8

# -------------------------------------------------------------------
# ORBIT-Anwendungsbeispiel 2
#
# Eine ORBIT-Anwendung mit einem Dienst und zwei Apps.
# -------------------------------------------------------------------

# Hinweis: Für dieses Beispiel muss es einen Brick-Daemon geben, 
#          mit dem sich ORBIT verbinden kann und es muss ein 
#          LCD-20x4-Bricklet angeschlossen sein.

from sys import stdin

# Importieren der notwendigen Klassen von ORBIT
from orbit_framework import Core, Service
from orbit_framework.messaging import Slot

# Importieren einiger integrierten Komponenten
from orbit_framework.components.lcd import LCD20x4ButtonsComponent
from orbit_framework.jobs.apps import MessageApp

# Den Anwendungskern instanzieren
core = Core()

# Einen Hintergrunddienst erzeugen
service = Service('ButtonService')

# Eine Komponente einrichten, die Nachrichten versendet
# wenn die Tasten am LCD-Display gedrückt werden.
service.add_component(
	LCD20x4ButtonsComponent('buttons'))

# Installieren des Hintergrunddienstes
core.install(service)

# Die erste App erzeugen
app1 = MessageApp('MsgApp1', ['Nachricht 1'])

# Die App durch eine Nachricht aktivieren
app1.add_activator(
	Slot('ButtonService', None, 'button_pressed',
		predicate = lambda j, c, n, v: v[1] == 1))

# Hinweis: In diesem Fall wird ein Prädikat verwendet, 
#          um den Nachrichtenempfang vom Nachrichteninhalt
#          abhängig zu machen. Die LCD-20x4-Buttons-Komponente
#          sendet als Nachrichteninhalt ein Tuple aus UID und 
#          Tastennummer. Das hier verwendete Prädikat prüft,
#          ob die zweite Taste (0-basiert) gedrückt wurde.

# Die App installieren
core.install(app1)

# Die zweite App erzeugen und installieren
app2 = MessageApp('MsgApp2', ['Nachricht 2'])
app2.add_activator(
	Slot('ButtonService', None, 'button_pressed',
		predicate = lambda j, c, n, v: v[1] == 2))
core.install(app2)

# Die erste App als Standard-App einrichten.
core.default_application = app1

# Hinweis: Die Standard-App wird automatisch beim Start 
#          der Anwendung (und wenn alle anderen Apps deaktiviert
#          werden) aktiviert.

# Starten der Anwendung
core.start()

# Auf eine Benutzereingabe warten
print(u"\nZum Beenden ENTER drücken.\n")
stdin.readline()

# Stoppen der Anwendung 
core.stop()
