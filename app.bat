@echo off
set directoryPath=%~dp0
set ARGUMENTS=
:loop1
if "%1"=="" goto after_loop
set ARGUMENTS=%ARGUMENTS% %1
shift
goto loop1
:after_loop
python dockertool.py App %ARGUMENTS% fromScript
