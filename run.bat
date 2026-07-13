@echo off
setlocal
set "APP_DIR=%~dp0"
set "CODEX_PY=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
set "LOG_FILE=%APP_DIR%aurorachecker.log"
cd /d "%APP_DIR%"

set "HTTP_PROXY="
set "HTTPS_PROXY="
set "ALL_PROXY="
set "http_proxy="
set "https_proxy="
set "all_proxy="

echo Starting AuroraChecker... > "%LOG_FILE%"
echo App dir: %APP_DIR% >> "%LOG_FILE%"

if exist "%CODEX_PY%" (
  echo Python: %CODEX_PY% >> "%LOG_FILE%"
  "%CODEX_PY%" "%APP_DIR%main.py" >> "%LOG_FILE%" 2>&1
  goto finished
)

where py >nul 2>nul
if %errorlevel%==0 (
  echo Python: py launcher >> "%LOG_FILE%"
  py "%APP_DIR%main.py" >> "%LOG_FILE%" 2>&1
  goto finished
)

where python >nul 2>nul
if %errorlevel%==0 (
  echo Python: PATH python >> "%LOG_FILE%"
  python "%APP_DIR%main.py" >> "%LOG_FILE%" 2>&1
  goto finished
)

echo Python was not found. Install Python 3.10+ and run:
echo pip install -r requirements.txt
echo Python was not found. >> "%LOG_FILE%"
pause
exit /b 1

:finished
set "EXIT_CODE=%errorlevel%"
if not "%EXIT_CODE%"=="0" (
  echo.
  echo AuroraChecker crashed. Log:
  type "%LOG_FILE%"
  echo.
  pause
  exit /b %EXIT_CODE%
)

echo AuroraChecker closed.
echo Log saved to: %LOG_FILE%
pause
