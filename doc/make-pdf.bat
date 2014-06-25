@echo off
pushd %~dp0

rem search for pdflatex
for %%x in (pdflatex.exe) do if not [%%~$PATH:x]==[] goto :ok_pdflatex
echo pdflatex not on PATH (install LaTeX distribution)
goto :end
:ok_pdflatex

call convert-images.bat
call make.bat latex

pushd out\latex
for /L %%i in (1,1,3) do (
	pdflatex -interaction=batchmode orbit.tex
)
popd

popd

:end