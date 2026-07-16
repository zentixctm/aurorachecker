=== Установка AuroraChecker ===

Вариант 1 — Онлайн (из любой папки, нужен Git и Python):
  powershell -Command "iwr -Uri https://raw.githubusercontent.com/zentixctm/aurorachecker/main/install.ps1 -OutFile %TEMP%\install.ps1; powershell -ExecutionPolicy Bypass -File %TEMP%\install.ps1"

Вариант 2 — Локально (если папка с программой уже есть):
  Запусти install.bat от имени администратора

Вариант 3 — Быстрый запуск без установки:
  run.bat
