@echo off
REM Get the folder where this script is located (tests/)
set SCRIPT_DIR=%~dp0

REM Go to project root (one directory up from tests)
cd /d "%SCRIPT_DIR%.."

set year=2015

set output_folder=%SCRIPT_DIR%\output\%year%"
mkdir %output_folder%

REM Activate the virtual environment
call .venv\Scripts\activate.bat 

echo.%output_folder%

REM Run the main Python entry point
python app\main.py -y %year% -of %output_folder%

REM Deactivate the virtual environment
call deactivate

pause

%output_folder%\convention_V2015-03-01\ccfpa_jobs.json