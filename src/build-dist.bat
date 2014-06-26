@echo off

set sname=orbit-0.1.0-alpha
set eggname=orbit_framework.egg
set pdfname=orbit.pdf

echo Building distribution package of %sname% ...

rem check 7zip
for %%x in (7z.exe) do if not [%%~$PATH:x]==[] goto :ok_7z
echo 7z not on PATH
goto :end
:ok_7z

pushd "%~dp0\.."

set docpdf=%~dp0\..\doc\out\latex\%pdfname%
set docarch=%~dp0\..\doc\out\%sname%_html-docs.zip
set distarch=%~dp0\dist\%sname%.zip

rem build the egg distribution package
call src\build-egg.bat

rem build the documentation
if exist doc\out ( 
	echo Cleaning documentation output directory ...
	rmdir /S /Q doc\out
)
call doc\make-pdf.bat
copy /Y "%docpdf%" doc\out\%sname%.pdf
call doc\make-html.bat
del /Q "%docarch%"
pushd doc\out\html
7z a -xr!bootstrap-2* -xr!bootswatch-* "%docarch%" .\*
popd

rem assemble the distribution archive
del /Q "%distarch%"
7z a -xr!__pycache__ -xr!*.pyc -xr!dist -xr!*.egg-info "%distarch%" src examples
7z a -xr!out -xr!*.pdf "%distarch%" doc
7z a "%distarch%" *.md
pushd src\dist
7z a "%distarch%" %eggname%
popd
pushd doc\out
7z a "%distarch%" "%docarch%"
7z a "%distarch%" %sname%.pdf
popd

popd

:end