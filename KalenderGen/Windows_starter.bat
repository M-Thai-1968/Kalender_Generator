@echo off
rem KalenderGen - Starter fuer Windows (funktioniert auch ohne installiertes Python)
setlocal EnableExtensions
cd /d "%~dp0"
title KalenderGen

set "VENV=%~dp0.venv"
set "PY=%VENV%\Scripts\python.exe"
if exist "%PY%" goto deps
set "PY=%VENV%\python.exe"
if exist "%PY%" goto deps

echo [KalenderGen] Erster Start - die Umgebung (.venv) wird eingerichtet ...
set "SYSPY="
py -3 -c "import sys;sys.exit(0 if sys.version_info>=(3,9) else 1)" >nul 2>&1
if not errorlevel 1 set "SYSPY=py -3"
if defined SYSPY goto makevenv
python -c "import sys;sys.exit(0 if sys.version_info>=(3,9) else 1)" >nul 2>&1
if not errorlevel 1 set "SYSPY=python"
if defined SYSPY goto makevenv
goto embedded

:makevenv
echo Verwende vorhandenes Python: %SYSPY%
%SYSPY% -m venv "%VENV%"
if errorlevel 1 goto embedded
set "PY=%VENV%\Scripts\python.exe"
goto deps

:embedded
echo Kein nutzbares Python gefunden - lade portables Python (einmalig, ca. 10 MB) ...
if exist "%VENV%" rmdir /s /q "%VENV%"
set "PYVER=3.12.8"
set "ZIPF=%TEMP%\kalendergen_pyembed.zip"
powershell -NoProfile -ExecutionPolicy Bypass -Command "[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -UseBasicParsing -Uri 'https://www.python.org/ftp/python/%PYVER%/python-%PYVER%-embed-amd64.zip' -OutFile '%ZIPF%'"
if errorlevel 1 goto neterr
powershell -NoProfile -ExecutionPolicy Bypass -Command "Expand-Archive -Force -Path '%ZIPF%' -DestinationPath '%VENV%'"
if errorlevel 1 goto fail
for %%F in ("%VENV%\python*._pth") do powershell -NoProfile -ExecutionPolicy Bypass -Command "Set-Content -Path '%%~fF' -Value @('python312.zip','.','Lib\site-packages','import site')"
powershell -NoProfile -ExecutionPolicy Bypass -Command "[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -UseBasicParsing -Uri 'https://bootstrap.pypa.io/get-pip.py' -OutFile '%VENV%\get-pip.py'"
if errorlevel 1 goto neterr
"%VENV%\python.exe" "%VENV%\get-pip.py" --no-warn-script-location --disable-pip-version-check
if errorlevel 1 goto fail
set "PY=%VENV%\python.exe"

:deps
if exist "%VENV%\.deps_ok" goto run
echo [KalenderGen] Installiere Pakete ...
if exist "%~dp0wheels\*.whl" goto offline
"%PY%" -m pip install --disable-pip-version-check -r "%~dp0requirements.txt"
if errorlevel 1 goto neterr
goto depsdone
:offline
"%PY%" -m pip install --disable-pip-version-check --no-index --find-links "%~dp0wheels" -r "%~dp0requirements.txt"
if errorlevel 1 goto fail
:depsdone
echo ok> "%VENV%\.deps_ok"

:run
"%PY%" "%~dp0main.py" %*
if errorlevel 1 pause
endlocal
exit /b 0

:neterr
echo.
echo Download/Installation fehlgeschlagen. Bitte Internetverbindung pruefen und erneut starten.
echo (Offline: .whl-Dateien von reportlab, dearpygui, Pillow, numpy in den Ordner wheels\ legen.)
pause
exit /b 1

:fail
echo.
echo Einrichtung fehlgeschlagen. Zum Neuaufbau den Ordner .venv loeschen und erneut starten.
pause
exit /b 1
