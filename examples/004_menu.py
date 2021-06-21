#!/usr/bin/python
# coding=utf-8

# -------------------------------------------------------------------
# ORBIT-Anwendungsbeispiel 4
#
# Eine ORBIT-Anwendung mit einem Menü.
# -------------------------------------------------------------------

# Hinweis: Für dieses Beispiel muss es einen Brick-Daemon geben,
#          mit dem sich ORBIT verbinden kann und es muss ein
#          LCD-20x4-Bricklet angeschlossen sein.

from sys import stdin

# Importieren der notwendigen Klassen von ORBIT
from orbit_framework import Core
from orbit_framework.messaging import Slot

# Importieren einiger integrierten Komponenten
from orbit_framework.jobs.apps import MenuApp, MessageApp

# Den Anwendungskern instanzieren
core = Core()

# Die Menü-App mit 5 Menüpunkten erzeugen
menu_app = MenuApp(
    'MenuApp',
    [('Punkt 1', 'one'),
     ('Punkt 2', 'two'),
     ('Punkt 3', 'three'),
     ('Punkt X', 'x'),
     ('Punkt Y', 'y')])
core.install(menu_app)

# Nachrichten-App für Menüpunkt 1
app1 = MessageApp('MsgApp1', ['Nachricht 1', '', '', 'zurück mit Taste 0'])

# Die App mit dem Menüpunkt 'one' verknüpfen
app1.add_activator(Slot('MenuApp', None, 'one'))

# Die App installieren
core.install(app1)

# Weitere Apps

app2 = MessageApp('MsgApp2', ['Nachricht 2', '', '', 'zurück mit Taste 0'])
app2.add_activator(Slot('MenuApp', None, 'two'))
core.install(app2)

app3 = MessageApp('MsgApp3', ['Nachricht 3', '', '', 'zurück mit Taste 0'])
app3.add_activator(Slot('MenuApp', None, 'three'))
core.install(app3)

# Das Menü als Standard-App einrichten.
core.default_application = menu_app

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
