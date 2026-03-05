@echo off
REM Get the folder where this script is located (tests/)
set SCRIPT_DIR=%~dp0

REM Go to project root (one directory up from tests)
cd /d "%SCRIPT_DIR%.."

set year=all

set "output_folder=%SCRIPT_DIR%\output\%RANDOM%"
mkdir %output_folder%
set "output_folder=%output_folder%\%year%"
mkdir %output_folder%

REM Activate the virtual environment
call .venv\Scripts\activate.bat 

echo.%output_folder%

REM Run the main Python entry point
python app\main.py -y %year% -of %output_folder%

REM Deactivate the virtual environment
call deactivate

pause

%output_folder%/ccfpa_jobs.json
