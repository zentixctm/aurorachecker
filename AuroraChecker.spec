# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['AuroraChecker.pyw'],
    pathex=[],
    binaries=[],
    datas=[('ui', 'ui'), ('assets', 'assets'), ('tools\\InjGen\\InjGen.exe', 'tools\\InjGen'), ('tools\\ShellBagAnalyzer\\shellbag_analyzer_cleaner.exe', 'tools\\ShellBagAnalyzer'), ('tools\\WarpVersionChecker\\WarpVersionChecker.exe', 'tools\\WarpVersionChecker'), ('jarka_scanner', 'jarka_scanner')],
    hiddenimports=['aurora_core', 'ctypes', 'csv', 'hashlib', 'io', 'json', 'os', 'pathlib', 're', 'shutil', 'shlex', 'subprocess', 'sys', 'tempfile', 'threading', 'time', 'urllib.request', 'uuid', 'urllib.parse', 'zipfile', 'traceback', 'winreg', 'datetime', 'jarka_scanner', 'jarka_scanner.scanner', 'jarka_scanner.jar_extractor', 'jarka_scanner.string_extractor', 'jarka_scanner.detectors', 'jarka_scanner.detectors.network_detector', 'jarka_scanner.detectors.stealer_detector', 'jarka_scanner.detectors.command_detector', 'jarka_scanner.detectors.cheat_detector', 'jarka_scanner.detectors.obfuscation_detector', 'jarka_scanner.utils', 'jarka_scanner.utils.helpers', 'jarka_scanner.ai', 'jarka_scanner.ai.ai_classifier'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='AuroraChecker',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['assets\\app.ico'],
)
