@echo off

set pname=orbit_framework

rem search for 7zip
for %%x in (7z.exe) do if not [%%~$PATH:x]==[] goto :ok_7z
echo 7zip not on command line
goto :end
:ok_7z

pushd "%~dp0"

del /Q dist\%pname%*.egg

python setup.py bdist_egg
rmdir /S /Q %pname%.egg-info
rmdir /S /Q build

pushd dist
if exist _tmp ( rmdir /S /Q _tmp )
7z x -o_tmp %pname%-*.egg
pushd _tmp
rem del /S /Q *.pyc
7z a -xr!__pycache__ -xr!*.pyc ..\%pname%.zip .\*
popd
rmdir /S /Q _tmp
ren %pname%.zip %pname%.egg
popd

popd

:end