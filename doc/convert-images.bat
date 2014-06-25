@echo off

rem search for Inkscape
for %%x in (inkscape.exe) do if not [%%~$PATH:x]==[] goto :ok_inkscape
echo Inkscape not on PATH
goto :end
:ok_inkscape

pushd %~dp0

echo | set /p dummy=Converting images ... 

cd src
for %%F in (*.svg) do (
	call :build %%F "%%~dpnF"
)
cd figures
for %%F in (*.svg) do (
	call :build %%F "%%~dpnF"
)

echo done

popd
goto :end

:build
call inkscape -f %1 -A "%2.pdf"
call inkscape -f %1 -e "%2.png"
goto :EOF

:end
