# Documentation Build Info

Die Dokumentation wird mit [Sphinx](http://sphinx-doc.org/) gebaut.

Für die Installation muss das Python-Paket `sphinx` installiert werden.

    easy_install sphinx

Die Dokumentation benutzt das Bootstrap-Theme für Sphinx. Dazu muss das Python-Paket `sphinx_bootstrap_theme` installiert werden.

    easy_install sphinx_bootstrap_theme

Anschließend kann die Dokumentation unter Angabe des Ausgabetyps und des Ausgabeverzeichnisses gebaut werden.

    sphinx-build -b html -d out/doctrees src out/html

Zur Vereinfachung unter Windows können die Dateien `make.bat` und `make-html.bat` verwendet werden. Das Batch-Script `make.bat` nimmt als einzigen Parameter den Ausgabetyp (`html`, `singlehtml`, ...) entgegen. Das Script `make-html.bat` kann ohne Parameter gestartet werden und baut die Dokumentation als HTML-Website.
