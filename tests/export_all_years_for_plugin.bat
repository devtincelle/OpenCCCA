@echo off
REM Get the folder where this script is located (tests/)
set SCRIPT_DIR=%~dp0

REM Go to project root (one directory up from tests)
cd /d "%SCRIPT_DIR%.."

set year=all

REM Build timestamp: YYYYMMDD_HHMM
for /f "tokens=1-3 delims=/ " %%a in ("%date%") do (
    set dd=%%a
    set mm=%%b
    set yyyy=%%c
)
for /f "tokens=1-2 delims=: " %%a in ("%time%") do (
    set hh=%%a
    set mn=%%b
)
REM Remove leading space from hour if needed (single digit hour)
set hh=%hh: =%

set "timestamp=%yyyy%%mm%%dd%_%hh%%mn%"

set "output_folder=%SCRIPT_DIR%output\%timestamp%"
mkdir "%output_folder%"
set "output_folder=%output_folder%\%year%"
mkdir "%output_folder%"

REM Activate the virtual environment
call .venv\Scripts\activate.bat

echo.%output_folder%

REM Run the main Python entry point
python app\main.py -of "%output_folder%"

REM Deactivate the virtual environment
call deactivate

pause

start "" "%output_folder%"