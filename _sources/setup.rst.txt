Setup
#####

Voraussetzungen
===============

Software
--------

ORBIT unterstützt Python 2.6+ und Python 3.x.

Die Installation kann mit dem Python-Paket-Manager `pip`_ durchgeführt werden. Dabei werden die TinkerForge-Python-Bindings automatisch mit installiert.

Paket-Manager *pip* installieren
''''''''''''''''''''''''''''''''

Wenn der Befehl ``pip --version`` auf der Befehlszeile die Version von *pip* ausgibt, ist *pip* bereits installiert. Um sicher zu stellen, dass die neueste Version von *pip* verwendet wird, kann *pip* aktualisiert werden:

.. code::

	> pip install --upgrade pip

Falls der Befehl ``pip`` nicht verfügbar ist, muss *pip* zunächst `installiert`__ werden.
Der einfachste Weg führt über das Setup-Script von *pip*:

__ pip_install_

**Linux:**

.. code::

	> wget -qO- https://bootstrap.pypa.io/get-pip.py | sudo python

**Windows:**

Zunächst ``https://bootstrap.pypa.io/get-pip.py`` herunterladen und anschließend ``python get-pip.py`` ausführen.

Hardware
--------

Für die Verwendung von TinkerForge ist mindestens ein Master-Brick 
und ein Bricklet erforderlich.
Wenn der Master-Brick per USB an den Computer (PC, Raspberry PI, o.a.)
angeschlossen werden soll, muss der `Brick-Deamon`_ installiert sein.

Einige der :doc:`Beispiele <examples>` verwenden ein LCD-20x4-Display-Bricklet und ein Motion-Detector-Bricklet.

Installation
============

Um ORBIT zu installieren, reicht der folgende Befehl:

**Linux:**

In einigen Linux-Umgebungen muss die Installation mit Root-Rechten durchgeführt werden. Dazu kann dem Befehl ein ``sudo`` vorangestellt werden.

.. code::

	> pip install orbit_framework

*Tipp:* Um ORBIT unter Linux für eine bestimmte Python-Version zu installieren, können die versionsspezifischen *pip*-Befehle benutzt werden.

*Python 2.7:*

.. code::

	> pip2.7 install orbit_framework

*jüngste Python 3.x:*

.. code::

	> pip3 install orbit_framework

**Windows:**

.. code::

	> pip install orbit_framework

Nun ist ORBIT installiert und es können die :doc:`Beispiele <examples>` ausgeführt werden.

Links
-----

* `Dokumentation der Python-Bindings`_
* `Download-Archiv`_

.. _pip: https://pypi.python.org/pypi/pip
.. _pip_install: https://pip.pypa.io/en/latest/installing.html
.. _`Dokumentation der Python-Bindings`: http://www.tinkerforge.com/de/doc/Software/API_Bindings_Python.html
.. _`Download-Archiv`: http://download.tinkerforge.com/bindings/python/
.. _`Brick-Deamon`: http://www.tinkerforge.com/de/doc/Software/Brickd.html
.. _Release: https://github.com/mastersign/orbit/releases