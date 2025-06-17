@echo off
cd /d "%~dp0"
echo Current directory is: %cd%
echo.
set /p REPORT_NUMBER=Enter report number: 

:: Call the annotation launcher with the entered report number
call execute.bat %REPORT_NUMBER%

pause
exit /b 0
