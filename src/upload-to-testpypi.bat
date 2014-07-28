@echo off

set indexurl=https://testpypi.python.org/pypi

pip search --index %indexurl% orbit_framework
if %ERRORLEVEL% gtr 0 (
  python setup.py register -r %indexurl%
)
python setup.py bdist_wheel upload -r %indexurl%
rem python setup.py upload_docs -r %indexurl%
