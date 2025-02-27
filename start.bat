@echo off
setlocal EnableDelayedExpansion

set "iniFile=config.ini"
set "start_keybind="
set "end_script_keybind="
set "use_bomb_identifier="

for /f "tokens=1,* delims==" %%A in (%iniFile%) do (
    set "key=%%A"
    set "value=%%B"

    if "!key!"=="start_keybind" set "start_keybind=!value!"
    if "!key!"=="end_script_keybind" set "end_script_keybind=!value!"
    if "!key!"=="use_bomb_identifier" set "use_bomb_identifier=!value!"
)


echo [91mANEURISM IV[0m auto bomb solver.
echo.
echo only works on 1080p fullscreen for now. Make sure you have python installed to work.
echo.
echo %start_keybind% to start, %end_script_keybind% to end.
echo.
echo You can use the config.ini file for more options
echo.
echo DISCORD: https://discord.gg/e8when9mwe


pause

:: Check if venv exists, if not, create it
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

:: Activate the virtual environment
call venv\Scripts\activate.bat

:: Check and install missing dependencies
echo Installing required dependencies...
pip install -r requirements.txt

:: Run the main Python script
cls
echo Script ready... %start_keybind% to activate. Hover over bombs and it will automatically open bomb screen and solve it.
python main.py

:: Keep the command prompt open after execution
echo Press Z again to exit
pause