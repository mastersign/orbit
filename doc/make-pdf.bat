pushd %~dp0

call convert-images.bat
call make.bat latex

pushd out\latex
for /L %%i in (1,1,3) do (
	pdflatex -interaction=batchmode orbit.tex
)
popd

popd