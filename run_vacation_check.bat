@echo off
REM Activate virtualenv if you have one (optional)
REM call C:\projects\vacation-playwright\venv\Scripts\activate.bat

REM Run the script and append output to log
"C:\Program Files\Python312\python.exe" "C:\projects\vacation-playwright\main.py" >> "C:\projects\vacation-playwright\log.txt" 2>&1

exit /b
