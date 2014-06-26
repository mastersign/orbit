Beispiele
#########

Die Python-Quelltexte der Beispiele befinden sich im Verzeichnis ``examples``.
Für die Ausführung der Beispiele muss ORBIT als Python-Package installiert sein (Siehe :doc:`Setup <setup>`),
Und es muss ein Brick-Deamon laufen. 
Mit der Standardkonfiguration versucht ORBIT
den Brick-Deamon unter ``localhost:4223`` zu erreichen.

Einige Beispiele setzen ein LCD-20x4-Bricklet und einige
auch ein Motion-Detector-Bricklet voraus.
Die Hardware-Voraussetzungen sind für jedes Beispiel
extra angegeben.

Grundlagen
==========

1. Basic
--------

`Quellcode <https://github.com/mastersign/orbit/blob/master/examples/1_basic.py>`_

**Hardware:**
keine

**Beschreibung:**
Grundaufbau einer ORBIT-Anwendung mit einem Dienst.

Das Beispiel demonstriert die Einrichtung, das Starten und Stoppen des Anwendungskerns. 
Darüber hinaus zeigt es, wie mit den beiden integrierten Komponenten 
:py:class:`orbit_framework.components.common.EventCallbackComponent`
und :py:class:`orbit_framework.components.timer.IntervalTimerComponent`
in regelmäßigen Abständen eine Funktion aufgerufen werden kann.
Die beiden Komponenten werden in einem Dienst zusammengefasst,
damit sie zur gesamten Laufzeit der Anwendung aktiv sind.
Die Timer-Komponente sendet in regelmäßigen Abständen eine Nachricht
über das ORBIT-Nachrichtensystem. 
Die Callback-Komponente wird so eingerichtet, dass sie die Timer-Nachrichten
empfängt und beim Eintreffen einer Nachricht die Funktion aufruft.
