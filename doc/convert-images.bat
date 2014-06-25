@echo off
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

popd
goto :end

:build
call inkscape -f %1 -A "%2.pdf"
call inkscape -f %1 -e "%2.png"
goto :EOF

:end
echo done