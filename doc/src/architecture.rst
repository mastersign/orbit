Architektur einer ORBIT-Anwendung
=================================

Eine ORBIT-Anwendung besteht aus einem Kern und assoziierten Jobs. 
Jobs können Dienste oder Apps sein. 
Die Dienste werden automatisch beim Start des Kerns aktiviert. Es können mehrere Dienste gleichzeitig aktiv sein. Von den Apps wird nur die Standard-App beim Start des Kerns akiviert
und es kann zu jedem Zeitpunkt immer nur eine App aktiv sein.

Jobs werden aus Komponenten zusammengesetzt. ORBIT bringt einige Komponenten und Jobs mit. 
Alle anwendungsspezifischen Fähigkeiten können in eigenen Komponente und Jobs implementiert
werden.

Der Gerätemanager im Kern verwaltet die TinkerForge-Verbindungen und die angeschlossenen
Bricklets. Jede Komponente kann die Zuordnung von ein oder mehreren Bricklets eines Typs anfordern.
Dabei können auch UIDs von Bricklets als Einschränkung angegeben werden.
Sobald ein Bricklet verfügbar ist, wird es den entsprechenden Komponenten zugeordnet
und die Komponenten werden über die Verfügbarkeit benachrichtigt. Wird eine Verbindung
getrennt, wird den Komponenten das Bricklet wieder entzogen.

Komponente und Jobs können über ein integriertes Nachrichtensystem kommunizieren.
Das Nachrichtensystem ermöglicht eine weitgehende Entkopplung der Komponenten und Jobs 
von einander und sorgt für eine robustere Anwendung.
