@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

echo.
echo ========================================
echo          INAZUMA - LOCAL START
echo ========================================
echo.

REM This project is pinned to Python 3.13 because libsql ships a Windows wheel for it.
py -3.13 --version >nul 2>&1
if errorlevel 1 (
  echo [INAZUMA] Python 3.13 was not found.
  echo [INAZUMA] Install Python 3.13 x64 from https://www.python.org/downloads/
  echo [INAZUMA] Keep Python 3.14 installed if you use it for other projects.
  echo [INAZUMA] During setup, keep the Python Launcher option enabled.
  echo.
  pause
  exit /b 1
)

echo [INAZUMA] Using:
py -3.13 --version

if not exist ".venv\Scripts\python.exe" (
  echo [INAZUMA] Creating a dedicated Python 3.13 environment...
  py -3.13 -m venv .venv
  if errorlevel 1 goto :error
)

echo.
echo [INAZUMA] Installing/checking dependencies with Python 3.13...
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto :error
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto :error

if not exist "data\admin_codes.txt" (
  echo.
  echo [INAZUMA] First launch: choose an admin code.
  set /p TEAM_ADMIN_CODE=Admin code: 
  if defined TEAM_ADMIN_CODE >"data\admin_codes.txt" echo !TEAM_ADMIN_CODE!
)

echo.
echo [INAZUMA] Starting dashboard at http://127.0.0.1:8000
".venv\Scripts\python.exe" run.py
if errorlevel 1 goto :error
pause
exit /b 0

:error
echo.
echo [INAZUMA] Something went wrong. Copy the error above and send it to ChatGPT.
pause
exit /b 1
