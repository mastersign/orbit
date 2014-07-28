@echo off

pip search orbit_framework
if %ERRORLEVEL% gtr 0 (
  python setup.py register
)
python setup.py bdist_wheel upload
python setup.py upload_docs
