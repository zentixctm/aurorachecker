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
  set "PYEXE=%CODEX_PY%"
) else (
  where pythonw >nul 2>nul
  if %errorlevel%==0 (
    set "PYEXE=pythonw"
  ) else (
    where python >nul 2>nul
    if %errorlevel%==0 (
      set "PYEXE=python"
    ) else (
      echo Python was not found. Install Python 3.10+ and run:
      echo pip install -r requirements.txt
      pause
      exit /b 1
    )
  )
)

echo Python: %PYEXE% >> "%LOG_FILE%"
start "" /B "%PYEXE%" "%APP_DIR%AuroraChecker.pyw"

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
