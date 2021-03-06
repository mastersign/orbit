@echo off

set trg=%~dp0\..\..\orbit-gh-pages\

rem check gh-pages working copy
if not exist "%trg%" (
	echo ..\orbit-gh-pages not found
	goto :end
)

rem check git
for %%x in (git.exe) do if not [%%~$PATH:x]==[] goto :ok_git
echo git not on PATH
goto :end
:ok_git

pushd "%~dp0"

if exist out ( 
	echo Cleaning output directory ...
	rmdir /S /Q out
)
call make-html.bat
call make-pdf.bat

pushd "%trg%"
git reset --hard
git checkout gh-pages
git pull
popd

copy /Y out\latex\orbit_framework.pdf "%trg%"
del /Q "%trg%\*.html"
copy /Y out\html\*.* "%trg%"
del /Q "%trg%\_images\*.*"
copy /Y out\html\_images\*.* "%trg%_images\"
del /Q "%trg%\_sources\*.*"
copy /Y out\html\_sources\*.* "%trg%_sources\"

pushd "%trg%"
git add --all
git commit --all -m "auto update"
popd

popd

echo.
echo You can now push '..\orbit-gh-pages' to the remote(s)
echo.

:end