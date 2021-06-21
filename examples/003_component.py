#!/usr/bin/python
# coding=utf-8

# -------------------------------------------------------------------
# ORBIT-Anwendungsbeispiel 3
#
# Eine ORBIT-Anwendung mit einer eigenen Komponente.
# -------------------------------------------------------------------

# Hinweis: Für dieses Beispiel muss es einen Brick-Daemon geben,
#          mit dem sich ORBIT verbinden kann und es muss ein
#          LCD-20x4-Bricklet angeschlossen sein.

from sys import stdin

# Importieren der notwendigen Klassen von ORBIT
from orbit_framework import Core, App, Component
from orbit_framework.devices import SingleDeviceHandle

# Importieren der TinkerForge-Bindings
from tinkerforge.bricklet_lcd_20x4 import BrickletLCD20x4


# Eine eigene Komponente
class MyLcdComponent(Component):

    def __init__(self, name, **nargs):
        # Name der Komponente und optionale benannte Parameter
        # an Initialisierungsfunktion der Basisklasse übergeben
        super(MyLcdComponent, self).__init__(name, **nargs)

        self._counter = 0

        # Geräteanforderung für LCD-20x4-Bricklet erzeugen
        self._lcd_handle = SingleDeviceHandle(
            'lcd', BrickletLCD20x4.DEVICE_IDENTIFIER)

        # Callback für Ereignis registrieren
        self._lcd_handle.register_callback(
            BrickletLCD20x4.CALLBACK_BUTTON_PRESSED,
            self.process_button)

        # Geräteanforderung einrichten
        self.add_device_handle(self._lcd_handle)

    def process_button(self, no):
        # Zähler hochzählen
        self._counter = self._counter + 1
        # Nachricht auf allen durch die Geräteanforderung
        # gebundenen Display ausgeben
        self._lcd_handle.for_each_device(self.update_display)

    def update_display(self, device):
        device.clear_display()
        device.write_line(0, 0, str(self._counter))


# Eine eigene App als Container für die Komponente
class MyApp(App):

    def __init__(self, name, **nargs):
        # Name der App und optionale benannte Parameter
        # an Initialisierungsfunktion der Basisklasse übergeben
        super(MyApp, self).__init__(name, **nargs)

        # Eigene Komponente der App hinzufügen
        self.add_component(MyLcdComponent('my_lcd'))


# Den Anwendungskern instanzieren
core = Core()

# Die App erzeugen
app = MyApp('MyApp')

# Die App installieren
core.install(app)

# Die App als Standard-App einrichten.
core.default_application = app

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
