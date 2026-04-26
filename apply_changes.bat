@echo off
title Apply Changes - Portfile

cd /d "%~dp0"

for /f "usebackq delims=" %%T in (`powershell -NoProfile -Command "(Get-Date).ToString('yyyyMMdd_HHmmss')"`) do set "TS=%%T"
if "%TS%"=="" set "TS=%DATE%_%TIME%"

set "LOGDIR=%~dp0logs"
if not exist "%LOGDIR%" mkdir "%LOGDIR%"
set "LOGFILE=%LOGDIR%\apply_changes_%TS%.log"





















































exit /b 0pause >nulecho Press ENTER to exit...
necho.type "%LOGFILE%"echo Push completed. Log: %LOGFILE%
necho SUCCESS >> "%LOGFILE%"git push origin main >> "%LOGFILE%" 2>&1 || (echo git push failed >> "%LOGFILE%" & echo git push failed & pause & exit /b 1)
necho Pushing... >> "%LOGFILE%"git commit -m "%MSG%" >> "%LOGFILE%" 2>&1 || (echo git commit failed >> "%LOGFILE%" & echo git commit failed & pause & exit /b 1)
necho Committing... >> "%LOGFILE%"git add . >> "%LOGFILE%" 2>&1 || (echo git add failed >> "%LOGFILE%" & echo git add failed & pause & exit /b 1)
necho Staging... >> "%LOGFILE%") set "MSG=%~1") else ( set "MSG=Apply changes %DATE% %TIME%"if "%~1"=="" (
n:: Compose commit message) exit /b 0 pause echo. type "%LOGFILE%" echo No hay cambios. Revisa: %LOGFILE% echo No changes to commit. >> "%LOGFILE%"
nif "%CHANGED%"=="0" (del "%temp%\gitstatus.txt" >nul 2>&1for /f "delims=" %%i in ('type "%temp%\gitstatus.txt"') do set "CHANGED=1"set "CHANGED=0"git status --porcelain > "%temp%\gitstatus.txt"
n:: Detect local changesgit fetch origin main --quiet >> "%LOGFILE%" 2>&1
ngit pull --rebase origin main >> "%LOGFILE%" 2>&1 || echo Pull warning >> "%LOGFILE%"echo Fetching updates... >> "%LOGFILE%"
n:: Fetch & rebase (best effort)) exit /b 1 pause echo No .git directory found. Revisa: %LOGFILE% echo [ERROR] Not a git repository. >> "%LOGFILE%"if not exist .git (
n:: Check git repo) exit /b 1 pause echo Git no encontrado. Revisa: %LOGFILE% echo [ERROR] Git not found. Ensure Git is installed and in PATH. >> "%LOGFILE%"if errorlevel 1 (where git >nul 2>&1
n:: Check git availableecho Dir: %CD% >> "%LOGFILE%"necho Start: %DATE% %TIME% > "%LOGFILE%"