@echo off
pushd %~dp0

cd src
for %%F in (*.svg) do (
	call :build %%F "%%~dpnF"
)
cd figures
for %%F in (*.svg) do (
	call :build %%F "%%~dpnF"
)

popd
goto :end

:build
call inkscape -f %1 -A "%2.pdf"
call inkscape -f %1 -e "%2.png"
goto :EOF

:end
