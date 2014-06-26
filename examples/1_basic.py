#!/usr/bin/python
# coding=utf-8

# -------------------------------------------------------------------
# ORBIT-Anwendungsbeispiel 1
#
# Grundaufbau einer ORBIT-Anwendung mit einem Dienst.
# -------------------------------------------------------------------

# Hinweis: Für dieses Beispiel ist keine TinkerForge-Hardware
#          erforderlich, aber es muss einen lokal laufenden 
#          Brick-Deamon geben, mit dem sich ORBIT verbinden kann.

# Importieren des Standardeingabe-Objektes für Benutzereingaben
from sys import stdin

# Importieren der notwendigen Klassen von ORBIT
from orbit_framework import Core, Service
from orbit_framework.messaging import Slot

# Importieren einiger integrierten Komponenten
from orbit_framework.components.common import EventCallbackComponent
from orbit_framework.components.timer import IntervalTimerComponent

# Eine Aktion die in regelmäßigen Abständen ausgeführt werden soll
def my_action():
	print("---- Action! ----")

# Den Anwendungskern instanzieren
core = Core()

# Einen Hintergrunddienst erzeugen
service = Service('ActionService')

# Hinweis: In diesem Fall wird die Basisklasse 'Service'
#          direkt benutzt und von außen mit Komponenten bestückt.
#          Es kann jedoch genausogut eine eigene Dienst-Klasse
#          implementiert werden, welche von 'Service' erbt
#          und in der Initialisierungsmethode die Komponenten
#          einrichtet.

# Eine Komponente einrichten, die alle 3 Sekunden 
# eine Nachricht versendet.
service.add_component(
	IntervalTimerComponent('action_timer', interval = 3))

# Eine Komponente einrichten, welche die Nachrichten
# der Komponente 'action_timer' empfängt
# und bei jeder Nachricht die Funktion 'my_action' 
# als Callback aufruft.
service.add_component(
	EventCallbackComponent('action_trigger', 
		Slot('ActionService', 'action_timer', 'timer'),
		my_action))

# Installieren des Hintergrunddienstes
core.install(service)

# Starten der Anwendung
core.start()

# Auf eine Benutzereingabe warten
print("\nENTER drücken zum Beenden.\n")
stdin.readline()

# Stoppen der Anwendung 
core.stop()
