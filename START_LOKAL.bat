@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel% equ 0 (
  set "SHIURIM_PY=py -3"
) else (
  set "SHIURIM_PY=python"
)
if not exist ".venv\Scripts\python.exe" (
  %SHIURIM_PY% -m venv .venv
  if errorlevel 1 goto :error
)
".venv\Scripts\python.exe" -c "import pyluach" >nul 2>nul
if errorlevel 1 (
  ".venv\Scripts\python.exe" -m pip install -r requirements.txt
  if errorlevel 1 goto :error
)
".venv\Scripts\python.exe" tools\shiurim.py build
if errorlevel 1 goto :error
start "" "http://localhost:8766"
echo Shiurim: http://localhost:8766
echo Dieses Fenster geoeffnet lassen. Beenden mit Strg+C.
".venv\Scripts\python.exe" -m http.server 8766 --bind 127.0.0.1 --directory dist
exit /b
:error
echo Start fehlgeschlagen. Python 3.11 oder neuer wird benoetigt.
pause
exit /b 1
