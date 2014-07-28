@echo off

call "%~dp0\project-vars.bat"

set eggname=%pfullname%.egg
set pdfname=%pname%.pdf
set docpdf=%doc%\out\latex\%pdfname%

set docarch=%dist%\%pfullname%-html_docs.zip
set distarch=%dist%\%pfullname%-complete.zip

echo # Building distribution package(s) of %pfullname% ...

rem check 7zip
for %%x in (7z.exe) do if not [%%~$PATH:x]==[] goto :ok_7z
echo 7z not on PATH
goto :end
:ok_7z

pushd "%root%"

  echo ## Building wheel ...
  pushd "%src%"
    call python setup.py bdist_wheel
    for %%f in ( %dist%\%pfullname%*.whl ) do ( set wheel=%%f )
  popd

  echo ## Building egg ...
  call src\build-egg.bat

  echo ## Building documentation ...
  if exist "%doc%\out" ( 
    echo Cleaning documentation output directory ...
    rmdir /S /Q "%doc%\out"
  )
  echo ### Creating PDF documentation ...
  call doc\make-pdf.bat
  copy /Y "%docpdf%" "%dist%\%pfullname%.pdf"

  echo ### Creating HTML documentation ...
  call doc\make-html.bat

  echo ### Creating HTML documentation archive ...
  del /Q "%docarch%"
  pushd "%doc%\out\html"
    7z a -xr!bootstrap-2* -xr!bootswatch-* "%docarch%" .\*
  popd
  
  echo ## Assembling the distribution archive ...
  
  del /Q "%distarch%"
  7z a -xr!__pycache__ -xr!*.pyc -xr!dist -xr!*.egg-info "%distarch%" src examples
  7z a -xr!out -xr!*.pdf "%distarch%" doc
  7z a "%distarch%" *.md
  
  pushd "%dist%"
    7z a "%distarch%" "%eggname%"
    7z a "%distarch%" "%wheel%"
    7z a "%distarch%" "%docarch%"
    7z a "%distarch%" "%pfullname%.pdf"
  popd
  
popd

echo.
echo Wheel created at\n\t%wheel%
echo Egg created at\n\t%dist%\%eggname%
echo PDF created at\n\t%dist%\%pfullname%.pdf
echo HTML site created at\n\t%doc%\out\html
echo HTML archive created at\n\t%docarch%
echo Distribution archive created at\n\t%distarch%
echo.

:end