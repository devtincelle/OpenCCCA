@echo off
REM Get the folder where this script is located (tests/)
set SCRIPT_DIR=%~dp0

REM Go to project root (one directory up from tests)
cd /d "%SCRIPT_DIR%.."

set pdf="resources/la-convention-collective-nationale-de-lanimation-et-la-grille-des-minima.pdf"
set output_folder="D:\1_TRAVAIL\WEB\wamp64\www\CCCA\wp-content\plugins\CCPFA\data\source"

REM Activate the virtual environment
call .venv\Scripts\activate.bat 

echo.%pdf%
echo.%output_folder%

REM Run the main Python entry point
python app\main.py -i %pdf% -of %output_folder%

REM Deactivate the virtual environment
call deactivate

pause