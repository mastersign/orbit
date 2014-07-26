@echo off

python "%~dp0\setup.py" --name > "%~dp0\dist\name.txt"
set /P pname= < "%~dp0\dist\name.txt"
python "%~dp0\setup.py" --version > "%~dp0\dist\version.txt"
set /P pversion= < "%~dp0\dist\version.txt"

set sname=%pname%-%pversion%
set eggname=%pname%.egg
set pdfname=%pname%.pdf

echo Building distribution package of %sname% ...

rem check 7zip
for %%x in (7z.exe) do if not [%%~$PATH:x]==[] goto :ok_7z
echo 7z not on PATH
goto :end
:ok_7z

pushd "%~dp0\.."

set docpdf=%~dp0\..\doc\out\latex\%pdfname%
set docarch=%~dp0\..\doc\out\%sname%_html-docs.zip
set distarch=%~dp0\dist\%sname%_complete.zip

rem build the source distribution
pushd src
call python setup.py sdist
popd

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
copy "%docarch%" src\dist

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