@echo off

rem search for Inkscape
for %%x in (inkscape.exe) do if not [%%~$PATH:x]==[] goto :ok_inkscape
echo Inkscape not on PATH
goto :end
:ok_inkscape

rem check git
for %%x in (git.exe) do if not [%%~$PATH:x]==[] goto :ok_git
echo git not on PATH
goto :end
:ok_git

pushd %~dp0

echo | set /p dummy=Converting images ... 

cd src
git clean -f -X > nul
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
