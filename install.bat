@echo off
:: Install script for Windows

echo =======================================================
echo === Antigravity Skill Symlinker Installer (Windows) ===
echo =======================================================

:: Check for python in PATH
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo Error: python is not installed or not in your PATH.
    echo Please install Python and try again.
    pause
    exit /b 1
)

:: Execute the python script, forwarding all arguments
python "%~dp0\link_skills.py" %*
if %ERRORLEVEL% neq 0 (
    echo Error: Failed to execute link_skills.py.
    pause
    exit /b %ERRORLEVEL%
)

echo Done.
if "%1"=="" pause
