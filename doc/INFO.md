# Documentation Build Info

Die Dokumentation wird mit [Sphinx](http://sphinx-doc.org/) gebaut.

Für die Installation muss das Python-Paket `sphinx` installiert werden.

    pip install sphinx

Die Dokumentation benutzt das Bootstrap-Theme für Sphinx. Dazu muss das Python-Paket `sphinx_bootstrap_theme` installiert werden.

    pip install sphinx_bootstrap_theme

Anschließend kann die Dokumentation unter Angabe des Ausgabetyps und des Ausgabeverzeichnisses gebaut werden.

    sphinx-build -b html -d out/doctrees src out/html

Zur Vereinfachung unter Windows können die Dateien `make.bat` und `make-html.bat` verwendet werden. Das Batch-Script `make.bat` nimmt als einzigen Parameter den Ausgabetyp (`html`, `epub`, ...) entgegen. Das Script `make-html.bat` kann ohne Parameter gestartet werden und baut die Dokumentation als HTML-Website.

Für die Erzeugung eines PDFs wird eine LaTeX-Distribution wie z.B. [MiKTeX](http://miktex.org/) benötigt. Die SVG-Grafiken können nicht direkt in das PDF eingebunden werden, sondern müssen zunächst in PDF konvertiert werden. Dazu dient das Batch-Script `convert-images.bat`. Das Skript benutzt das Grafikprogramm [Inkscape](http://www.inkscape.org/de/) für die Konvertierung. Dafür muss Inkscape installiert und über die `PATH`-Variable erreichbar sein.

Sind diese Voraussetzungen erfüllt, kann die Datei `make-pdf.bat` verwendet werden, um das PDF zu erzeugen.
