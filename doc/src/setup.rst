Setup
#####

Voraussetzungen
===============

Software
--------

ORBIT unterstützt Python 2.6+ und Python 3.x.

Für die Installation werden die setuptools_ benötigt, 
die den Installationsbefehl *easy_install* zur Verfügung stellen, 
mit dem Python-Eggs installiert werden können.

ORBIT setzt die TinkerForge-Python-Bindings voraus.
Diese werden auf der Website von TinkerForge als Download zur Verfügung gestellt. 
Das im Download enthaltene Python-Egg ``tinkerforge.egg`` muss mit *easy_install*
installiert werden.

* `Dokumentation der Python-Bindings`_
* `Download-Archiv`_

Hardware
--------

Für die Verwendung von TinkerForge ist mindestens ein Master-Brick 
und ein Bricklet erforderlich.
Wenn der Master-Brick per USB an den Computer (PC, Raspberry PI, o.a.)
angeschlossen werden soll, muss der `Brick-Deamon`_ installiert sein.

Einige der Beispiele verwenden ein LCD-20x4-Display-Bricklet und ein Motion-Detector-Bricklet.

Installation
============

ORBIT wird, wie die TinkerForge-Bindings, als Python-Egg installiert.
Die Datei ``orbit_framework.egg`` kann als Release_ heruntergeladen werden.

Anschließend kann ORBIT mit *easy_install* installiert werden.
Dazu wird *easy_install* wie folgt aufgerufen:
::

	> easy_install orbit_framework.egg

Unter Umständen muss der Befehl mit Administrator- bzw. Root-Rechten (z.B. mit ``sudo``) aufgerufen werden.

Nun ist ORBIT installiert und es können die :doc:`Beispiele <examples>` ausgeführt werden.

.. _setuptools: https://pypi.python.org/pypi/setuptools
.. _`Dokumentation der Python-Bindings`: http://www.tinkerforge.com/de/doc/Software/API_Bindings_Python.html
.. _`Download-Archiv`: http://download.tinkerforge.com/bindings/python/
.. _`Brick-Deamon`: http://www.tinkerforge.com/de/doc/Software/Brickd.html
.. _Release: https://github.com/mastersign/orbit/releases