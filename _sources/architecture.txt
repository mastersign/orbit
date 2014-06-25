Architektur einer ORBIT-Anwendung
=================================

Eine ORBIT-Anwendung besteht aus einem Kern und assoziierten Jobs. 
Jobs können Dienste oder Apps sein. 
Die Dienste werden automatisch beim Start des Kerns aktiviert 
und sind gleichzeitig aktiv.
Von den Apps wird nur die Standard-App beim Start des Kerns akiviert
und zu jedem Zeitpunkt kann immer nur eine App aktiv sein.

Jobs und Komponenten
--------------------

Jobs werden aus Komponenten zusammengesetzt. 
Alle anwendungsspezifischen Fähigkeiten können in eigenen Komponenten
und Jobs implementiert werden.
Für einige Standardaufgaben bringt ORBIT :doc:`components` und :doc:`jobs` mit.

.. figure:: figures/architecture-overview.*
	:alt: Architekturübersicht

	Eine grobe Übersicht über die Architektur einer ORBIT-Anwendung

| *Siehe auch:*
| :py:class:`orbit_framework.Core`,
| :py:class:`orbit_framework.Component`,
| :py:class:`orbit_framework.App`,
  :py:class:`orbit_framework.Service`

Gerätemanager
-------------

Der Gerätemanager im Kern verwaltet die TinkerForge-Verbindungen und die angeschlossenen
Brick(let)s. Jede Komponente kann die Zuordnung von ein oder mehreren Brick(let)s eines 
Typs anfordern.
Dabei können auch UIDs von Brick(let)s als Einschränkung angegeben werden.
Sobald ein Brick(let) verfügbar ist, wird es den entsprechenden Komponenten zugeordnet
und die Komponenten werden über die Verfügbarkeit benachrichtigt. Wird eine Verbindung
getrennt, wird den Komponenten das Brick(let) wieder entzogen. 

.. figure:: figures/devicemanager-overview.*
	:alt: Gerätemanager

	Eine Übersicht über den Gerätemanager

| *Siehe auch:*
| :py:class:`orbit_framework.Component.add_device_handle`,
| :py:class:`orbit_framework.devices.DeviceHandle`,
| :py:class:`orbit_framework.devices.DeviceManager`

Nachrichtensystem
-----------------

Komponenten und Jobs können über ein integriertes, asynchrones Nachrichtensystem kommunizieren.
Das Nachrichtensystem ermöglicht eine weitgehende Entkopplung der Komponenten und Jobs 
von einander und sorgt für eine robuste Anwendung.

.. figure:: figures/messagebus-overview.*
	:alt: Nachrichtensystem

	Eine Übersicht über das Nachrichtensystem

| *Siehe auch:* 
| :py:meth:`orbit_framework.Component.add_listener`,
  :py:meth:`orbit_framework.Job.add_listener`,
| :py:meth:`orbit_framework.Component.send`,
  :py:meth:`orbit_framework.Job.send`,
| :py:class:`orbit_framework.messaging.MessageBus`

Übersicht
---------

Die folgende Übersicht stellt die wesentlichen Objekte in einer 
ORBIT-Anwendung und deren Assoziationen dar.
Grau hinterlegte Objekte werden von ORBIT implementiert. 
Blau hinterlegte Objekte werden durch die TinkerForge-Python-Bibliothek implementiert.
Grün hinterlegte Objekte werden anwendungsspezifisch implementiert,
wobei Basisklassen die die Implementierung erleichtern.

.. figure:: figures/architecture.*
	:alt: Architektur einer ORBIT-Anwendung

	Eine detaillierte Übersicht über die Architektur einer ORBIT-Anwendung
