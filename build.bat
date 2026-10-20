@echo off
REM Build script: PyInstaller (onedir) -> dist\PyDex\PyDex.exe
REM Then compile installer.iss with Inno Setup for a professional setup file.
setlocal
cd /d "%~dp0"
python -m pip install -r requirements.txt pyinstaller
python tools\make_icon.py
pyinstaller setup.spec --noconfirm
echo.
echo Build done: dist\PyDex\PyDex.exe
echo Optional: open installer.iss in Inno Setup to produce installer\PyDex-Setup-1.0.0.exe
