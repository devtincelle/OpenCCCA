@echo off
REM Get the folder where this script is located (tests/)
set SCRIPT_DIR=%~dp0

REM Go to project root (one directory up from tests)
cd /d "%SCRIPT_DIR%.."

REM Activate the virtual environment
call .venv\Scripts\activate.bat 

echo.%output_folder%

REM Run the main Python entry point
python app\main.py -y 2024 -of %output_folder%

REM Deactivate the virtual environment
call deactivate

pause