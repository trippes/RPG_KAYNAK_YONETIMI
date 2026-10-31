@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo HATA: Proje sanal ortami bulunamadi.
    echo .venv klasorunu kontrol edin.
    pause
    exit /b 1
)
".venv\Scripts\python.exe" main.py --play
pause
