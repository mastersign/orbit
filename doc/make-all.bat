pushd %~dp0

call convert-images.bat

call make.bat linkcheck
call make.bat html
call make.bat dirhtml
call make.bat singlehtml
call make.bat epub
call make.bat htmlhelp
call make.bat latex
call make.bat xml
call make.bat pseudoxml

set ProgFilesX86Root=%ProgramFiles(x86)%
if "%ProgFilesX86Root%"=="" (
	set ProgFilesX86Root=%ProgramFiles%
)

pushd out\htmlhelp
"%ProgFilesX86Root%\HTML Help Workshop\hhc.exe" orbit.hhp
popd

pushd out\latex
for /L %%i in (1,1,3) do (
	pdflatex -interaction=batchmode orbit.tex
)
popd

popd