@echo off
setlocal enabledelayedexpansion

REM =====================================================
REM  install.bat
REM  Clean venv bootstrap (Windows / pipeline-safe)
REM =====================================================

echo.
echo [INFO] Bootstrapping virtual environment...

REM --- Neutralize pipeline pollution ---
set PYTHONPATH=
set PYTHONNOUSERSITE=1

REM --- Select Python ---
where py >nul 2>&1
if %ERRORLEVEL%==0 (
    set PYTHON=py -3
) else (
    set PYTHON=python
)

REM --- Remove existing venv ---
if exist ".venv" (
    echo [INFO] Removing existing .venv...
    rmdir /s /q .venv
    if exist ".venv" (
        echo [ERROR] Failed to remove .venv
        exit /b 1
    )
)

REM --- Create venv ---
echo [INFO] Creating .venv...
%PYTHON% -m venv .venv
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to create virtual environment
    exit /b 1
)

REM --- Activate venv ---
call .venv\Scripts\activate.bat

REM --- Ensure pip exists ---
echo [INFO] Ensuring pip...
python -m pip --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [WARN] pip missing, bootstrapping...
    python -m ensurepip --upgrade
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to bootstrap pip
        exit /b 1
    )
)

REM --- Upgrade core tooling ---
echo [INFO] Upgrading pip / setuptools / wheel...
python -m pip install --upgrade pip setuptools wheel

REM --- Install dependencies ---
if exist "requirements.txt" (
    echo [INFO] Installing requirements.txt...
    python -m pip install -r requirements.txt
) else (
    echo [INFO] No requirements.txt found
)

REM --- Editable install for local package ---
if exist "pyproject.toml" (
    echo [INFO] Installing project (editable)...
    python -m pip install -e .
) else if exist "setup.py" (
    echo [INFO] Installing project (editable)...
    python -m pip install -e .
)

echo.
echo [SUCCESS] Virtual environment rebuilt and ready
echo [INFO] Python in use:
where python
echo.

cmd /k