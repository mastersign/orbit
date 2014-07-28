@echo off

call "%~dp0\project-vars.bat"

rem check 7zip
for %%x in (7z.exe) do if not [%%~$PATH:x]==[] goto :ok_7z
echo 7z not on PATH
goto :end
:ok_7z

pushd %src%

  del /Q "%dist%\%pname%*.egg"

  python setup.py bdist_egg
  rmdir /S /Q %pname%.egg-info
  rmdir /S /Q build

  pushd %dist%
  
    if exist _tmp ( rmdir /S /Q _tmp )
    if exist tmp_egg.zip ( del /Q tmp_egg.zip )
    
    7z x -o_tmp %pname%-*.egg
    
    pushd _tmp
      7z a -xr!__pycache__ -xr!*.pyc ..\tmp_egg.zip .\*
    popd
    
    rmdir /S /Q _tmp
    del /Q %pname%*.egg
    ren tmp_egg.zip "%pname%-%pversion%.egg"
    
  popd

popd

echo.
echo Egg created at\n\t%dist%\%pname%-%pversion%.egg
echo.

:end