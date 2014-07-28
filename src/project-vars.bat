@echo off

echo # Reading project name and version ...

pushd %~dp0\..
set root=%cd%
popd

set src=%root%\src
set dist=%src%\dist
set doc=%root%\doc

if not exist "%dist%\" ( mkdir %dist% )
python "%src%\setup.py" --name > "%dist%\name.txt"
set /P pname= < "%dist%\name.txt"
python "%src%\setup.py" --version > "%dist%\version.txt"
set /P pversion= < "%dist%\version.txt"

set pfullname=%pname%-%pversion%

echo.
echo Project: %pname%
echo Version: %pversion%
echo Root:    %root%
echo.