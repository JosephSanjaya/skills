@echo off
:: Windows submodule updater and symlink re-installer wrapper

echo =======================================================
echo === Antigravity Submodule Updater (Windows)          ===
echo =======================================================

:: Check for git in PATH
where git >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo Error: git is not installed or not in your PATH.
    pause
    exit /b 1
)

echo Updating git submodules...
git submodule update --init --recursive --remote
if %ERRORLEVEL% neq 0 (
    echo Error: Git submodule update failed.
    pause
    exit /b %ERRORLEVEL%
)

echo Retriggering symlink installation...
call "%~dp0\install.bat" %*
if %ERRORLEVEL% neq 0 (
    echo Error: Failed to run install.bat.
    exit /b %ERRORLEVEL%
)
