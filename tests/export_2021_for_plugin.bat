@echo off
REM Get the folder where this script is located (tests/)
set SCRIPT_DIR=%~dp0

REM Go to project root (one directory up from tests)
cd /d "%SCRIPT_DIR%.."

set year=2024

set output_folder="D:\1_TRAVAIL\WEB\wamp64\www\CCCA\wp-content\plugins\CCPFA\data\source\%year%"

REM Activate the virtual environment
call .venv\Scripts\activate.bat 

echo.%output_folder%

REM Run the main Python entry point
python app\main.py -y %year% -of %output_folder%

REM Deactivate the virtual environment
call deactivate

pause