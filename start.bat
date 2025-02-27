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
echo %start_keybind% to start/toggle, %end_script_keybind% to end.
echo.
echo You can use the config.ini file for more options
echo.
echo DISCORD IF NOT WORK: https://discord.gg/6EUrpzEv3T

pause

if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

call venv\Scripts\activate.bat
echo installing required dependencies...
pip install -r requirements.txt

cls
echo Script ready... %start_keybind% to activate/toggle. Hover over bombs and it will automatically open bomb screen and solve it.
python main.py

echo Press Z again to exit
pause
