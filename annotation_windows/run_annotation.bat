@echo off
:: =============================================================================
:: run_annotation.bat — Windows entry point for the annotation workflow
::
:: Double-click this file in Explorer to start an annotation session.
:: It prompts the user for a report number, then calls execute.bat
:: which finds the patient data and launches 3D Slicer.
:: =============================================================================

:: Change to the directory where this script lives (the annotation folder)
cd /d "%~dp0"
echo Current directory is: %cd%
echo.

:: Prompt the annotator for which report to work on
set /p REPORT_NUMBER=Enter report number:

:: Launch the annotation session
call execute.bat %REPORT_NUMBER%

pause
exit /b 0
