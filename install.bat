@echo off
chcp 65001 >nul
title AuroraChecker Installer

echo =============================================
echo   AuroraChecker - Установка
echo =============================================
echo.

:: Проверка прав администратора
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Требуются права администратора.
    echo Запустите install.bat от имени администратора.
    pause
    exit /b 1
)

:: Определяем папку установки
set "INSTALL_DIR=%LOCALAPPDATA%\AuroraChecker"

:: Создаём папку
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

:: Копируем файлы
echo Копирование файлов...
xcopy /E /I /Y "%~dp0*" "%INSTALL_DIR%" >nul

:: Добавляем в PATH
echo Добавление в PATH...
setx /M PATH "%PATH%;%INSTALL_DIR%" >nul

:: Создаём ярлык на рабочем столе
echo Создание ярлыка...
powershell -Command "$s=(New-Object -COM WScript.Shell).CreateShortcut('%USERPROFILE%\Desktop\AuroraChecker.lnk');$s.TargetPath='%INSTALL_DIR%\AuroraChecker.exe';$s.WorkingDirectory='%INSTALL_DIR%';$s.Save()" >nul

echo.
echo =============================================
echo   Установка завершена!
echo   Ярлык на рабочем столе: AuroraChecker
echo   Запуск из cmd: AuroraChecker
echo =============================================
pause
