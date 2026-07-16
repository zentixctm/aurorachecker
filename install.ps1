$repoUrl = "https://github.com/zentixctm/aurorachecker.git"
$installDir = "$env:LOCALAPPDATA\AuroraChecker"

Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "  AuroraChecker - Онлайн установка"
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

# Проверка прав администратора
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "Требуются права администратора!" -ForegroundColor Red
    Write-Host "Запустите PowerShell от имени администратора и попробуйте снова." -ForegroundColor Yellow
    pause
    exit 1
}

# Проверка Git
$git = Get-Command git -ErrorAction SilentlyContinue
if (-not $git) {
    Write-Host "Git не установлен. Установите Git: https://git-scm.com/" -ForegroundColor Red
    pause
    exit 1
}

# Проверка Python
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    Write-Host "Python не установлен. Установите Python: https://python.org/" -ForegroundColor Red
    pause
    exit 1
}

# Клонирование
Write-Host "Клонирование репозитория..." -ForegroundColor Yellow
if (Test-Path $installDir) { Remove-Item $installDir -Recurse -Force }
git clone $repoUrl $installDir 2>&1 | Out-Null

# Установка зависимостей
Write-Host "Установка зависимостей..." -ForegroundColor Yellow
pip install -r "$installDir\requirements.txt" 2>&1 | Out-Null

# Добавление в PATH
Write-Host "Добавление в PATH..." -ForegroundColor Yellow
$currentPath = [Environment]::GetEnvironmentVariable("Path", "Machine")
if ($currentPath -notlike "*$installDir*") {
    [Environment]::SetEnvironmentVariable("Path", "$currentPath;$installDir", "Machine")
}

# Ярлык на рабочем столе
Write-Host "Создание ярлыка..." -ForegroundColor Yellow
$wshell = New-Object -ComObject WScript.Shell
$shortcut = $wshell.CreateShortcut("$env:USERPROFILE\Desktop\AuroraChecker.lnk")
$shortcut.TargetPath = "$installDir\run.bat"
$shortcut.WorkingDirectory = $installDir
$shortcut.Save()

Write-Host ""
Write-Host "=============================================" -ForegroundColor Green
Write-Host "  Установка завершена!" -ForegroundColor Green
Write-Host "  Ярлык на рабочем столе: AuroraChecker"
Write-Host "  Запуск из cmd: cd %LOCALAPPDATA%\AuroraChecker ^&^& run.bat"
Write-Host "=============================================" -ForegroundColor Green
pause
