from __future__ import annotations

import ctypes
import csv
from datetime import datetime, timedelta
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import shlex
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
import uuid
from urllib.parse import urlparse
from ctypes import wintypes
import zipfile


APP_VERSION = "1.0.0-python"
APP_ROOT = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
BUNDLED_ROOT = Path(getattr(sys, "_MEIPASS", APP_ROOT))
TOOLS_DIR = APP_ROOT / "tools"
BUNDLED_TOOLS_DIR = BUNDLED_ROOT / "tools"


def hidden_subprocess_options() -> dict:
    if os.name != "nt":
        return {}
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = 0
    return {
        "creationflags": getattr(subprocess, "CREATE_NO_WINDOW", 0),
        "startupinfo": startupinfo,
    }

SUSPICIOUS_PATTERNS = {
    "AimAssist", "AutoCrystal", "AutoAnchor", "AutoTotem", "InventoryTotem",
    "TriggerBot", "SelfDestruct", "SilentAim", "FakeLag", "BlockESP",
    "AutoClicker", "AuthBypass", "BaseFinder", "NoFall", "WalskyOptimizer",
    "WalksyOptimizer", "Dqrkis", "doomsdayclient.com", "prestigeclient.vip",
    "imgui", "jnativehook", "LicenseCheckMixin", "obfuscatedAuth",
    "injgen", "injectgen", "lunarclient",
}

CHEAT_STRINGS = {
    "AutoCrystal", "autocrystal", "auto crystal", "AutoAnchor", "auto anchor",
    "AutoTotem", "auto totem", "InventoryTotem", "HoverTotem", "AutoPot",
    "AutoArmor", "AutoClicker", "AimAssist", "aim assist", "TriggerBot",
    "trigger bot", "FakeLag", "pingspoof", "selfdestruct", "self destruct",
    "AutoFirework", "NoFall", "BaseFinder", "Dqrkis Client", "Runtime.exec",
    "System.load", "setAccessible", "Vape Lite Client", "vape lite",
    "vapelite", "Vape V4 Client", "vape v4", "vapev4", "DoomsDay Client",
    "doomsday", "doomsdayclient", "Slinky Client", "slinky", "slinkyclient",
    "Sunset Client", "sunsetclient", "Karma Client", "karmaclient",
    "InjGen", "injgen", "injectgen", "Lunar Client", "lunarclient",
    "com/lunarclient", "com/lunar",
}

WHITELISTED_MODS = {
    "vmp-fabric", "vmp", "lithium", "sodium", "iris", "fabric-api",
    "modmenu", "ferrite-core", "lazydfu", "starlight", "entityculling",
    "immediatelyfast",
}

GHOST_SIGNATURES = [
    ("Vape Lite Client", ("vape lite", "vapelite", "vape_lite", "vape-lite", "vape lite client")),
    ("Vape V4 Client", ("vape v4", "vapev4", "vape_v4", "vape-v4", "vape v4 client")),
    ("DoomsDay Client", ("doomsday", "doomsdayclient", "doomsday client", "doomsdayclient.com")),
    ("Slinky Client", ("slinky", "slinkyclient", "slinky client", "slinky_client")),
    ("Sunset Client", ("sunsetclient", "sunset client", "sunset_client", "sunset-loader", "sunset.dll")),
    ("Karma Client", ("karmaclient", "karma client", "karma_client", "karma-loader", "karma.dll")),
    ("InjGen", ("injgen", "inj_gen", "injectgen", "inj-generator", "injgenerator")),
]

TRUSTED_MODULE_HINTS = (
    "\\windows\\system32\\",
    "\\windows\\syswow64\\",
    "\\program files\\",
    "\\program files (x86)\\",
    "\\appdata\\roaming\\.minecraft\\runtime\\",
    "\\appdata\\roaming\\.minecraft\\libraries\\",
    "\\appdata\\roaming\\.minecraft\\versions\\",
    "\\.minecraft\\runtime\\",
    "\\.minecraft\\libraries\\",
    "\\.minecraft\\versions\\",
)

USER_WRITABLE_MODULE_HINTS = (
    "\\appdata\\local\\temp\\",
    "\\appdata\\local\\",
    "\\appdata\\roaming\\",
    "\\downloads\\",
    "\\desktop\\",
    "\\users\\public\\",
    "\\temp\\",
)

NATIVE_INJECTION_NAME_HINTS = (
    "agent", "hook", "inject", "loader", "jvmti", "jni", "bridge", "mapper", "client"
)

PROGRAM_SIGNATURES = [
    {
        "name": "Everything",
        "process": ("everything.exe", "everything64.exe"),
        "exe": ("everything.exe", "everything64.exe"),
        "keywords": ("everything", "voidtools"),
        "download_url": "https://www.voidtools.com/Everything-1.4.1.1032.x64.zip",
        "download_type": "zip",
    },
    {
        "name": "ShellBag Analyzer",
        "process": ("shellbag_analyzer_cleaner.exe", "shellbaganalyzer_cleaner.exe", "shellbaganalyzer.exe"),
        "exe": ("shellbag_analyzer_cleaner.exe", "shellbaganalyzer_cleaner.exe", "shellbaganalyzer.exe"),
        "keywords": ("shellbag", "shellbag analyzer", "privazer"),
        "download_url": "https://privazer.com/ru/shellbag_analyzer_cleaner.exe",
        "download_type": "file",
    },
    {
        "name": "Journal Trace",
        "process": ("journaltrace.exe", "journal trace.exe"),
        "exe": ("journaltrace.exe", "journal trace.exe"),
        "keywords": ("journaltrace", "journal trace"),
        "download_url": "https://github.com/ponei/JournalTrace/releases/download/1.0/JournalTrace.exe",
        "download_type": "file",
    },
    {
        "name": "System Informer",
        "process": ("systeminformer.exe", "processhacker.exe"),
        "exe": ("systeminformer.exe", "processhacker.exe"),
        "keywords": ("system informer", "systeminformer", "process hacker", "processhacker"),
        "download_url": "https://github.com/winsiderss/systeminformer/releases/download/v3.2.25011.2103/systeminformer-3.2.25011-release-bin.zip",
        "download_type": "zip",
    },
    {
        "name": "WinPrefetchView",
        "process": ("winprefetchview.exe", "winpreftechview.exe"),
        "exe": ("winprefetchview.exe", "winpreftechview.exe"),
        "keywords": ("winprefetchview", "winpreftechview", "win prefetch view"),
        "download_url": "https://www.nirsoft.net/utils/winprefetchview-x64.zip",
        "download_type": "zip",
    },
    {
        "name": "BrowsingHistoryView",
        "process": ("browsinghistoryview.exe", "browserhistoryview.exe"),
        "exe": ("browsinghistoryview.exe", "browserhistoryview.exe"),
        "keywords": ("browsinghistoryview", "browserhistoryview", "browser history view", "browsing history view"),
        "download_url": "https://www.nirsoft.net/utils/browsinghistoryview-x64.zip",
        "download_type": "zip",
    },
    {
        "name": "BrowserDownloadsView",
        "process": ("browserdownloadsview.exe", "browser downloads view.exe"),
        "exe": ("browserdownloadsview.exe", "browser downloads view.exe"),
        "keywords": ("browserdownloadsview", "browser downloads view", "browser downloads"),
        "download_url": "https://www.nirsoft.net/utils/browserdownloadsview-x64.zip",
        "download_type": "zip",
    },
    {
        "name": "LastActivityView",
        "process": ("lastactivityview.exe",),
        "exe": ("lastactivityview.exe",),
        "keywords": ("lastactivityview", "last activity view"),
        "download_url": "https://www.nirsoft.net/utils/lastactivityview.zip",
        "download_type": "zip",
    },
    {
        "name": "USBDriveLog",
        "process": ("usbdrivelog.exe",),
        "exe": ("usbdrivelog.exe",),
        "keywords": ("usbdrivelog", "usb drive log"),
        "download_url": "https://www.nirsoft.net/utils/usbdrivelog.zip",
        "download_type": "zip",
    },
    {
        "name": "USBDeview",
        "process": ("usbdeview.exe",),
        "exe": ("usbdeview.exe",),
        "keywords": ("usbdeview", "usb deview"),
        "download_url": "https://www.nirsoft.net/utils/usbdeview-x64.zip",
        "download_type": "zip",
    },
    {
        "name": "WinDefLogView",
        "process": ("windeflogview.exe",),
        "exe": ("windeflogview.exe",),
        "keywords": ("windeflogview", "windows defender log", "defender log"),
        "download_url": "https://www.nirsoft.net/utils/windeflogview.zip",
        "download_type": "zip",
    },
    {
        "name": "BAM Parser",
        "process": ("bamparser.exe", "bam parser.exe"),
        "exe": ("bamparser.exe", "bam parser.exe"),
        "keywords": ("bamparser", "bam parser", "background activity moderator"),
        "download_url": "https://github.com/spokwn/BAM-parser/releases/download/v1.2.9/BAMParser.exe",
        "download_type": "file",
    },
    {
        "name": "InjGen",
        "process": ("injgen.exe",),
        "exe": ("injgen.exe",),
        "keywords": ("injgen", "inj gen", "inject generator"),
        "download_url": None,
        "download_type": None,
    },
    {
        "name": "WarpVersionChecker",
        "process": ("warpversionchecker.exe",),
        "exe": ("warpversionchecker.exe",),
        "keywords": ("warpversionchecker", "warp version checker", "warpversion"),
        "download_url": None,
        "download_type": None,
    },
    {
        "name": "Java",
        "process": ("java.exe", "javaw.exe"),
        "exe": ("java.exe", "javaw.exe"),
        "keywords": ("java", "openjdk", "temurin", "adoptium", "jdk", "jre"),
        "download_url": "https://api.adoptium.net/v3/binary/latest/21/ga/windows/x64/jdk/hotspot/normal/eclipse",
        "download_type": "zip",
    },
]

BETA_TOOL_NAMES = {
    "Everything",
    "ShellBag Analyzer",
    "Journal Trace",
}

OTHER_TOOL_NAMES = {
    "BAM Parser",
    "WinDefLogView",
    "InjGen",
    "WarpVersionChecker",
    "Java",
}

COMMAND_SIGNATURES = []

ALLOWED_DOWNLOAD_HOSTS = {
    "www.voidtools.com",
    "voidtools.com",
    "www.nirsoft.net",
    "nirsoft.net",
    "github.com",
    "objects.githubusercontent.com",
    "release-assets.githubusercontent.com",
    "download.ccleaner.com",
    "ccleaner.com",
    "api.adoptium.net",
    "privazer.com",
}

KNOWN_BENIGN_NATIVE_NAMES = (
    "jna",
    "libopus4j",
    "librnnoise4j",
    "libspeex4j",
    "liblame4j",
    "discordhook",
    "discord_hook",
)

KNOWN_BENIGN_NATIVE_PATHS = (
    "\\appdata\\local\\discord\\",
    "\\appdata\\local\\temp\\jna-",
    "\\appdata\\local\\temp\\libopus4j-",
    "\\appdata\\local\\temp\\librnnoise4j-",
    "\\appdata\\local\\temp\\libspeex4j-",
    "\\appdata\\local\\temp\\liblame4j-",
)

GENERIC_AGENT_MEMORY_MARKERS = (
    "agent_onload",
    "agent_onattach",
    "jni_onload",
    "jvmti",
    "jvmtienv",
    "classfileloadhook",
    "retransformclasses",
    "seteventnotificationmode",
    "nativemethodbind",
)

KNOWN_MEMORY_MARKERS = tuple(
    token.lower()
    for _, tokens in GHOST_SIGNATURES
    for token in tokens
    if len(token) >= 5
) + ("com/lunarclient", "com/lunar", "injgen", "injectgen")

PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_VM_READ = 0x0010
MEM_COMMIT = 0x1000
MEM_PRIVATE = 0x20000
PAGE_NOACCESS = 0x01
PAGE_GUARD = 0x100
READABLE_PROTECTIONS = {0x02, 0x04, 0x08, 0x20, 0x40, 0x80}
EXECUTABLE_PROTECTIONS = {0x10, 0x20, 0x40, 0x80}
MEMORY_CHUNK_SIZE = 1024 * 1024
MAX_MEMORY_SCAN_BYTES = 768 * 1024 * 1024
MAX_MEMORY_FINDINGS = 24


class MEMORY_BASIC_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("BaseAddress", ctypes.c_void_p),
        ("AllocationBase", ctypes.c_void_p),
        ("AllocationProtect", wintypes.DWORD),
        ("RegionSize", ctypes.c_size_t),
        ("State", wintypes.DWORD),
        ("Protect", wintypes.DWORD),
        ("Type", wintypes.DWORD),
    ]


class SYSTEM_INFO(ctypes.Structure):
    _fields_ = [
        ("wProcessorArchitecture", wintypes.WORD),
        ("wReserved", wintypes.WORD),
        ("dwPageSize", wintypes.DWORD),
        ("lpMinimumApplicationAddress", ctypes.c_void_p),
        ("lpMaximumApplicationAddress", ctypes.c_void_p),
        ("dwActiveProcessorMask", ctypes.c_size_t),
        ("dwNumberOfProcessors", wintypes.DWORD),
        ("dwProcessorType", wintypes.DWORD),
        ("dwAllocationGranularity", wintypes.DWORD),
        ("wProcessorLevel", wintypes.WORD),
        ("wProcessorRevision", wintypes.WORD),
    ]


def default_mods_path() -> str:
    appdata = os.environ.get("APPDATA")
    candidates = []
    if appdata:
        candidates.append(Path(appdata) / ".minecraft" / "mods")
    candidates.append(Path.home() / "AppData" / "Roaming" / ".minecraft" / "mods")
    for path in candidates:
        try:
            if path.is_dir():
                return str(path)
        except OSError:
            continue
    return str(candidates[0])


def format_bytes(value: int) -> str:
    size = float(value)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} B"
        size /= 1024
    return f"{value} B"


def entry(class_name: str, entry_type: str, detail: str) -> dict:
    return {"className": class_name or "archive", "type": entry_type, "detail": detail}


def result_item(name: str, path: str, size: int, modrinth: bool, suspicious: bool, source: str | None, logs: list[dict]) -> dict:
    return {
        "name": name,
        "path": path,
        "sizeBytes": size,
        "size": format_bytes(size),
        "modrinthFound": modrinth,
        "suspicious": suspicious,
        "source": "Trusted" if modrinth else (source or "Unknown"),
        "verdict": "Risk" if suspicious else "Clean",
        "analysisResults": logs,
    }


def sha1_file(path: Path) -> str:
    h = hashlib.sha1()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def check_modrinth(path: Path) -> bool:
    try:
        digest = sha1_file(path)
        url = f"https://api.modrinth.com/v2/version_file/{digest}?algorithm=sha1"
        req = urllib.request.Request(url, headers={"User-Agent": f"AuroraChecker/{APP_VERSION}"})
        with urllib.request.urlopen(req, timeout=1.2) as response:
            return response.status == 200 and "project_id" in response.read(4096).decode("utf-8", "ignore")
    except Exception:
        return False


def download_source(path: Path) -> str | None:
    try:
        with open(str(path) + ":Zone.Identifier", "r", encoding="latin-1", errors="ignore") as fh:
            text = fh.read().lower()
        match = re.search(r"HostUrl=(.*)", text, re.IGNORECASE)
        if not match:
            return None
        url = match.group(1).strip()
        known = [
            "mediafire.com", "discord", "dropbox.com", "google.com", "mega.nz",
            "github.com", "modrinth.com", "curseforge.com", "doomsdayclient.com",
            "prestigeclient.vip", "dqrkis.xyz",
        ]
        for host in known:
            if host in url:
                return host
        host = re.search(r"https?://(?:www\.)?([^/]+)", url)
        return host.group(1) if host else url
    except Exception:
        return None


def heuristic_results(path: Path) -> list[dict]:
    try:
        return process_jar_bytes(path.read_bytes(), "", True)
    except Exception:
        return []


def process_jar_bytes(data: bytes, prefix: str, is_root: bool) -> list[dict]:
    results: list[dict] = []
    classes = obfuscated = numeric = unicode_names = ultra_short = 0
    mod_id = None
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            for info in zf.infolist():
                name = info.filename
                lower_name = name.lower()
                if info.is_dir():
                    continue
                if is_root and name == "fabric.mod.json":
                    mod_id = extract_mod_id(zf.read(name))
                if name.endswith(".jar") and "META-INF/jars/" in name:
                    results.extend(process_jar_bytes(zf.read(name), name + " -> ", False))
                    continue
                for pattern in SUSPICIOUS_PATTERNS:
                    if pattern.lower() in lower_name:
                        results.append(entry(prefix + name, "Suspicious Path", pattern))
                if name.endswith(".class"):
                    classes += 1
                    class_name = Path(name).stem
                    if len(class_name) <= 2:
                        ultra_short += 1
                    if class_name.isdigit():
                        numeric += 1
                    if any(ord(ch) > 127 for ch in class_name):
                        unicode_names += 1
                    if is_obfuscated_path(name):
                        obfuscated += 1
                    raw = zf.read(name)
                    check_content(raw, prefix + name, results)
                    check_behaviors(raw.decode("latin-1", "ignore"), prefix + name, results)
    except Exception:
        return results

    if classes > 5:
        if obfuscated / classes > 0.25:
            results.append(entry(prefix, "Obfuscation", f"Rate: {int(obfuscated / classes * 100)}%"))
        if numeric:
            results.append(entry(prefix, "Obfuscation", f"Numeric classes: {numeric}"))
        if unicode_names:
            results.append(entry(prefix, "Obfuscation", f"Unicode classes: {unicode_names}"))
        if ultra_short:
            results.append(entry(prefix, "Obfuscation", f"Short names: {ultra_short}"))
    if mod_id in WHITELISTED_MODS and obfuscated:
        results.append(entry(mod_id, "CRITICAL", "Fake mod identity detected"))
    return results


def extract_mod_id(data: bytes) -> str | None:
    try:
        parsed = json.loads(data.decode("utf-8", "ignore"))
        return parsed.get("id")
    except Exception:
        text = data.decode("utf-8", "ignore")
        match = re.search(r'"id"\s*:\s*"([^"]+)"', text)
        return match.group(1) if match else None


def check_content(data: bytes, name: str, results: list[dict]) -> None:
    latin = data.decode("latin-1", "ignore")
    utf8 = data.decode("utf-8", "ignore")
    latin_lower = latin.lower()
    utf8_lower = utf8.lower()
    for marker in CHEAT_STRINGS:
        lower = marker.lower()
        if lower in latin_lower or lower in utf8_lower:
            results.append(entry(name, "Cheat String", marker))


def check_behaviors(content: str, name: str, results: list[dict]) -> None:
    if "java/lang/Runtime" in content and "exec" in content:
        results.append(entry(name, "Dangerous Behavior", "Runtime.exec()"))
    if "HttpURLConnection" in content and "FileOutputStream" in content:
        results.append(entry(name, "Dangerous Behavior", "Remote Download"))
    if "setDoOutput" in content and "getOutputStream" in content and "getProperty" in content:
        results.append(entry(name, "Dangerous Behavior", "Data Exfiltration"))
    if "java/lang/System" in content and ("loadLibrary" in content or "load" in content):
        results.append(entry(name, "Native Loading", "System.load"))
    if "getDeclaredField" in content or "getDeclaredMethod" in content or "setAccessible" in content:
        results.append(entry(name, "Reflection", "Private Access"))


def is_obfuscated_path(name: str) -> bool:
    return sum(1 for part in name.split("/") if len(part) == 1) >= 2


def high_confidence(entries: list[dict]) -> bool:
    risky = {
        "critical", "cheat string", "ghost client", "runtime signature",
        "suspicious path", "dangerous behavior", "native injection", "jvm agent",
    }
    return any((item.get("type") or "").lower() in risky for item in entries)


def scan_path(path_text: str) -> dict:
    path = Path(path_text.strip()).expanduser()
    if not path.exists():
        return error(f"Path does not exist: {path}")
    if path.is_file():
        if path.suffix.lower() != ".jar":
            return error(f"Selected file is not a jar: {path}")
        jars = [path]
    else:
        jars = sorted(p for p in path.rglob("*.jar") if p.is_file())
    if not jars:
        return error(f"No .jar files found in: {path}")

    items = []
    for jar in jars:
        modrinth = check_modrinth(jar)
        logs = [] if modrinth else heuristic_results(jar)
        items.append(result_item(
            jar.name,
            str(jar.resolve()),
            jar.stat().st_size if jar.exists() else 0,
            modrinth,
            (not modrinth) and high_confidence(logs),
            download_source(jar),
            logs,
        ))
    return ok(str(path.resolve()), items)


def powershell(command: str) -> list[str]:
    system_root = os.environ.get("SystemRoot", r"C:\Windows")
    candidates = [
        str(Path(system_root) / "System32" / "WindowsPowerShell" / "v1.0" / "powershell.exe"),
        "powershell.exe",
        "powershell",
    ]
    wrapped = "[Console]::OutputEncoding=[System.Text.Encoding]::UTF8; $OutputEncoding=[System.Text.Encoding]::UTF8; " + command
    for exe in candidates:
        if "\\" in exe and not Path(exe).is_file():
            continue
        try:
            proc = subprocess.run(
                [exe, "-NoProfile", "-NonInteractive", "-Command", wrapped],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="ignore",
                timeout=5,
                **hidden_subprocess_options(),
            )
            lines = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
            return [line for line in lines if not looks_like_error(line)]
        except Exception:
            continue
    return []


def command_lines(command: list[str], timeout: int = 5) -> list[str]:
    try:
        proc = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            timeout=timeout,
            **hidden_subprocess_options(),
        )
        return [line.strip() for line in proc.stdout.splitlines() if line.strip() and not looks_like_error(line)]
    except Exception:
        return []


def looks_like_error(line: str) -> bool:
    lower = line.lower()
    return lower.startswith("error:") or "access denied" in lower or "not recognized" in lower or "exception" in lower


def java_processes() -> list[dict]:
    processes: dict[int, dict] = {}
    collect_get_process(processes)
    collect_tasklist(processes)
    collect_jps(processes)
    collect_cim(processes)
    collect_wmic(processes)
    if not processes:
        collect_wmi(processes)
    return list(processes.values())


def all_processes() -> list[dict]:
    processes: dict[int, dict] = {}
    script = (
        "Get-CimInstance Win32_Process | "
        "ForEach-Object { \"$($_.ProcessId)`t$($_.Name)`t$($_.ExecutablePath)`t$($_.CommandLine)\" }"
    )
    parse_tabbed_processes_with_path(processes, powershell(script))
    if processes:
        return list(processes.values())

    script = (
        "Get-Process | ForEach-Object { "
        "\"$($_.Id)`t$($_.ProcessName).exe`t$($_.Path)`t$($_.MainWindowTitle)\" }"
    )
    parse_tabbed_processes_with_path(processes, powershell(script))
    return list(processes.values())


def add_process(processes: dict[int, dict], pid: int, name: str, command: str) -> None:
    if pid not in processes:
        processes[pid] = {"pid": pid, "name": name or "java", "command": compact(command or "")}
        return

    existing = processes[pid]
    new_command = compact(command or "")
    old_command = existing.get("command", "")
    if new_command and (old_command in ("", "listed by tasklist") or len(new_command) > len(old_command)):
        existing["command"] = new_command
    if name and existing.get("name") in ("", "java"):
        existing["name"] = name


def add_full_process(processes: dict[int, dict], pid: int, name: str, path: str, command: str) -> None:
    if pid not in processes:
        processes[pid] = {
            "pid": pid,
            "name": name or "process",
            "path": path or "",
            "command": compact(command or ""),
        }
        return
    existing = processes[pid]
    if path and not existing.get("path"):
        existing["path"] = path
    if command and len(command) > len(existing.get("command", "")):
        existing["command"] = compact(command)


def collect_cim(processes: dict[int, dict]) -> None:
    script = "Get-CimInstance Win32_Process | Where-Object { $_.Name -match 'java|minecraft' -or $_.CommandLine -match 'minecraft|--gameDir' } | ForEach-Object { \"$($_.ProcessId)`t$($_.Name)`t$($_.CommandLine)\" }"
    parse_tabbed_processes(processes, powershell(script))


def collect_wmi(processes: dict[int, dict]) -> None:
    script = "Get-WmiObject Win32_Process | Where-Object { $_.Name -match 'java|minecraft' -or $_.CommandLine -match 'minecraft|--gameDir' } | ForEach-Object { \"$($_.ProcessId)`t$($_.Name)`t$($_.CommandLine)\" }"
    parse_tabbed_processes(processes, powershell(script))


def collect_get_process(processes: dict[int, dict]) -> None:
    script = "Get-Process | Where-Object { $_.Name -match 'java|javaw|minecraft' -or $_.MainWindowTitle -match 'minecraft' } | ForEach-Object { \"$($_.Id)`t$($_.ProcessName)`t$($_.MainWindowTitle)\" }"
    parse_tabbed_processes(processes, powershell(script))


def collect_wmic(processes: dict[int, dict]) -> None:
    lines = command_lines(["wmic.exe", "process", "where", "(name='java.exe' or name='javaw.exe' or name='Minecraft.exe')", "get", "ProcessId,Name,CommandLine", "/FORMAT:CSV"])
    for line in lines:
        if line.startswith("Node,"):
            continue
        try:
            fields = next(csv.reader([line]))
            pid = int(fields[-1].strip())
            add_process(processes, pid, fields[-2].strip(), fields[1] if len(fields) > 3 else "")
        except Exception:
            continue


def collect_jps(processes: dict[int, dict]) -> None:
    lines = command_lines(["jps.exe", "-lv"]) or command_lines(["jps", "-lv"])
    for line in lines:
        parts = line.split(maxsplit=1)
        try:
            pid = int(parts[0])
            command = parts[1] if len(parts) > 1 else "listed by jps"
            name = "Minecraft Java" if is_minecraft_like(command) else "java"
            add_process(processes, pid, name, command)
        except Exception:
            continue


def collect_tasklist(processes: dict[int, dict]) -> None:
    for image in ("java.exe", "javaw.exe", "Minecraft.exe"):
        lines = command_lines(["tasklist.exe", "/FI", f"IMAGENAME eq {image}", "/FO", "CSV", "/NH"])
        for line in lines:
            if line.startswith("INFO:") or line.startswith("ERROR:"):
                continue
            try:
                fields = next(csv.reader([line]))
                add_process(processes, int(fields[1]), fields[0], "listed by tasklist")
            except Exception:
                continue


def parse_tabbed_processes(processes: dict[int, dict], lines: list[str]) -> None:
    for line in lines:
        parts = line.split("\t", 2)
        if len(parts) >= 2:
            try:
                add_process(processes, int(parts[0]), parts[1], parts[2] if len(parts) > 2 else "")
            except Exception:
                continue


def parse_tabbed_processes_with_path(processes: dict[int, dict], lines: list[str]) -> None:
    for line in lines:
        parts = line.split("\t", 3)
        if len(parts) >= 2:
            try:
                add_full_process(
                    processes,
                    int(parts[0]),
                    parts[1],
                    parts[2] if len(parts) > 2 else "",
                    parts[3] if len(parts) > 3 else "",
                )
            except Exception:
                continue


def get_command_line(pid: int) -> str:
    for command in (
        f"(Get-CimInstance Win32_Process -Filter \"ProcessId = {pid}\").CommandLine",
        f"(Get-WmiObject Win32_Process -Filter \"ProcessId = {pid}\").CommandLine",
    ):
        lines = powershell(command)
        if lines:
            return lines[0]
    return ""


def loaded_modules(pid: int) -> list[str]:
    return powershell(f"Get-Process -Id {pid} -Module -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FileName")


def minecraft_like_processes() -> list[dict]:
    matches = []
    for process in java_processes():
        haystack = f"{process.get('name', '')} {process.get('command', '')}"
        if is_minecraft_like(haystack) or mods_path_for_pid(process["pid"]):
            matches.append(process)
    return matches


def mods_path_for_pid(pid: int) -> str | None:
    command = get_command_line(pid)
    found = resolve_mods_from_command(command)
    if found:
        return found
    hints = [token for token in tokenize(command) if ".minecraft" in token.lower()]
    hints.extend(path for path in loaded_modules(pid) if ".minecraft" in path.lower())
    for hint in hints:
        root = minecraft_root_from(hint)
        if root:
            return str(Path(root) / "mods")
    if is_minecraft_like(command):
        return default_mods_path()
    return None


def resolve_mods_from_command(command: str) -> str | None:
    tokens = tokenize(command)
    for index, token in enumerate(tokens):
        lower = clean_token(token).lower()
        if lower in ("--gamedir", "--workingdirectory") and index + 1 < len(tokens):
            return str(Path(clean_token(tokens[index + 1])) / "mods")
        if lower.startswith("--gamedir=") or lower.startswith("--workingdirectory="):
            return str(Path(clean_token(token.split("=", 1)[1])) / "mods")
        if lower.startswith("-duser.dir="):
            return str(Path(clean_token(token[len("-Duser.dir="):])) / "mods")
        root = minecraft_root_from(token)
        if root:
            return str(Path(root) / "mods")
    return None


def tokenize(command: str) -> list[str]:
    if not command:
        return []
    try:
        return shlex.split(command, posix=False)
    except Exception:
        return command.split()


def clean_token(value: str) -> str:
    return value.strip().strip("\"'")


def minecraft_root_from(text: str) -> str | None:
    cleaned = clean_token(text)
    lower = cleaned.lower()
    index = lower.find(".minecraft")
    if index < 0:
        return None
    return cleaned[: index + len(".minecraft")]


def is_minecraft_like(text: str) -> bool:
    lower = (text or "").lower()
    return any(marker in lower for marker in ("minecraft", "--gamedir", "net.minecraft", "fabric-loader", "forge", "quilt-loader"))


def scan_ghost_process(process: dict) -> dict | None:
    logs: list[dict] = []
    seen: set[str] = set()
    pid = int(process["pid"])
    check_ghost_text(f"{process.get('name', '')} {process.get('command', '')}", "Process title", logs, seen)
    command = get_command_line(pid)
    check_ghost_text(command, "Command line", logs, seen)
    for agent in agent_arguments(command):
        check_ghost_text(agent, "JVM agent argument", logs, seen)
        add_unique_entry(logs, seen, "JVM agent argument", "JVM Agent", compact(agent, 220))
    modules = loaded_modules(pid)
    logs.extend(process_module_entries(modules, seen))
    for module in modules:
        check_ghost_text(module, "Loaded module", logs, seen)
    logs.extend(memory_scan_entries(pid, seen))
    if not logs:
        return None
    return result_item(
        f"Process PID {pid} runtime signal",
        f"PID {pid} / {process.get('name', 'java')} / {process.get('command', '')}",
        0,
        False,
        True,
        "Process",
        logs,
    )


def check_ghost_text(text: str, location: str, logs: list[dict], seen: set[str]) -> None:
    lower = (text or "").lower()
    if not lower:
        return
    for display, tokens in GHOST_SIGNATURES:
        for token in tokens:
            if token in lower:
                key = f"{location}|{display}|{token}"
                if key not in seen:
                    seen.add(key)
                    logs.append(entry(location, "Runtime Signature", f"{display} signature: {token}"))
                break


def process_module_entries(modules: list[str], seen: set[str]) -> list[dict]:
    logs: list[dict] = []
    for module in modules:
        normalized = normalize_win_path(module)
        if not normalized.endswith(".dll"):
            continue
        base = Path(normalized).name.lower()
        trusted = is_trusted_module(normalized)
        benign = is_known_benign_native(normalized, base)
        writable = is_user_writable_module(normalized)
        suspicious_name = any(marker in base for marker in NATIVE_INJECTION_NAME_HINTS)

        if writable and not trusted and not benign:
            add_unique_entry(
                logs,
                seen,
                "Loaded module",
                "Native Injection",
                "Loaded DLL from user-writable location: " + module,
            )
            continue

        if suspicious_name and not trusted and not benign:
            add_unique_entry(
                logs,
                seen,
                "Loaded module",
                "Native Injection",
                "Suspicious native module name: " + module,
            )
    return logs


def add_unique_entry(logs: list[dict], seen: set[str], class_name: str, entry_type: str, detail: str) -> None:
    key = f"{class_name}|{entry_type}|{detail}"
    if key in seen:
        return
    seen.add(key)
    logs.append(entry(class_name, entry_type, detail))


def normalize_win_path(path: str) -> str:
    return (path or "").replace("/", "\\").lower()


def is_trusted_module(path: str) -> bool:
    return any(hint in path for hint in TRUSTED_MODULE_HINTS)


def is_user_writable_module(path: str) -> bool:
    return any(hint in path for hint in USER_WRITABLE_MODULE_HINTS) and not is_trusted_module(path)


def is_known_benign_native(path: str, base: str) -> bool:
    return any(base.startswith(name) for name in KNOWN_BENIGN_NATIVE_NAMES) or any(hint in path for hint in KNOWN_BENIGN_NATIVE_PATHS)


def memory_scan_entries(pid: int, seen: set[str]) -> list[dict]:
    if os.name != "nt":
        return []

    logs: list[dict] = []
    try:
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        open_process = kernel32.OpenProcess
        open_process.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        open_process.restype = wintypes.HANDLE

        virtual_query_ex = kernel32.VirtualQueryEx
        virtual_query_ex.argtypes = [wintypes.HANDLE, ctypes.c_void_p, ctypes.POINTER(MEMORY_BASIC_INFORMATION), ctypes.c_size_t]
        virtual_query_ex.restype = ctypes.c_size_t

        read_process_memory = kernel32.ReadProcessMemory
        read_process_memory.argtypes = [wintypes.HANDLE, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
        read_process_memory.restype = wintypes.BOOL

        close_handle = kernel32.CloseHandle
        close_handle.argtypes = [wintypes.HANDLE]
        close_handle.restype = wintypes.BOOL

        handle = open_process(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid)
        if not handle:
            return []

        try:
            max_address = get_max_application_address(kernel32)
            address = 0
            scanned = 0
            mbi = MEMORY_BASIC_INFORMATION()
            mbi_size = ctypes.sizeof(MEMORY_BASIC_INFORMATION)

            while address < max_address and scanned < MAX_MEMORY_SCAN_BYTES and len(logs) < MAX_MEMORY_FINDINGS:
                queried = virtual_query_ex(handle, ctypes.c_void_p(address), ctypes.byref(mbi), mbi_size)
                if not queried:
                    address += 0x10000
                    continue

                base = int(mbi.BaseAddress or address)
                region_size = int(mbi.RegionSize or 0)
                if region_size <= 0:
                    address += 0x10000
                    continue

                if is_readable_memory(mbi) and int(mbi.Type) == MEM_PRIVATE:
                    offset = 0
                    while offset < region_size and scanned < MAX_MEMORY_SCAN_BYTES and len(logs) < MAX_MEMORY_FINDINGS:
                        chunk_size = min(MEMORY_CHUNK_SIZE, region_size - offset, MAX_MEMORY_SCAN_BYTES - scanned)
                        data = read_memory_chunk(read_process_memory, handle, base + offset, chunk_size)
                        scanned += chunk_size
                        if data:
                            inspect_memory_chunk(data, base + offset, int(mbi.Type), int(mbi.Protect), logs, seen)
                        offset += chunk_size

                address = base + region_size
        finally:
            close_handle(handle)
    except Exception:
        return logs

    return logs


def get_max_application_address(kernel32) -> int:
    try:
        info = SYSTEM_INFO()
        kernel32.GetNativeSystemInfo(ctypes.byref(info))
        return int(info.lpMaximumApplicationAddress or 0x7FFFFFFFFFFF)
    except Exception:
        return 0x7FFFFFFFFFFF


def is_readable_memory(mbi: MEMORY_BASIC_INFORMATION) -> bool:
    if int(mbi.State) != MEM_COMMIT:
        return False
    protect = int(mbi.Protect)
    if protect & PAGE_GUARD or protect & PAGE_NOACCESS:
        return False
    return (protect & 0xFF) in READABLE_PROTECTIONS


def read_memory_chunk(read_process_memory, handle, address: int, size: int) -> bytes:
    if size <= 0:
        return b""
    buffer = (ctypes.c_ubyte * size)()
    read = ctypes.c_size_t(0)
    ok_read = read_process_memory(handle, ctypes.c_void_p(address), buffer, size, ctypes.byref(read))
    if not ok_read or read.value == 0:
        return b""
    return bytes(buffer[: read.value])


JVM_MODIFICATION_DWORDS = {0x00080006, 0xFCE01E99}

def inspect_memory_chunk(data: bytes, address: int, region_type: int, protect: int, logs: list[dict], seen: set[str]) -> None:
    lower = data.lower()

    for marker in KNOWN_MEMORY_MARKERS:
        if marker_in_memory(lower, marker):
            add_unique_entry(
                logs,
                seen,
                "Process memory",
                "Runtime Signature",
                "Known runtime marker in memory: " + marker,
            )
            if len(logs) >= MAX_MEMORY_FINDINGS:
                return

    if region_type == MEM_PRIVATE:
        generic_hits = [marker for marker in GENERIC_AGENT_MEMORY_MARKERS if marker_in_memory(lower, marker)]
        if len(generic_hits) >= 2:
            add_unique_entry(
                logs,
                seen,
                "Process memory",
                "Memory Injection",
                "JVMTI/JNI agent markers in private memory: " + ", ".join(generic_hits[:4]),
            )

        if is_executable_protection(protect) and has_private_pe_image(data):
            add_unique_entry(
                logs,
                seen,
                "Process memory",
                "Memory Injection",
                "PE image bytes in executable private memory at 0x" + format(address, "X"),
            )

        check_jvm_modification_dwords(data, address, logs, seen)


def check_jvm_modification_dwords(data: bytes, address: int, logs: list[dict], seen: set[str]) -> None:
    if len(logs) >= MAX_MEMORY_FINDINGS:
        return
    for i in range(0, len(data) - 3, 4):
        dword = int.from_bytes(data[i:i+4], "little")
        if dword in JVM_MODIFICATION_DWORDS:
            add_unique_entry(
                logs,
                seen,
                "Process memory",
                "JVM Modification",
                f"InjGen JVM bytecode modification marker at 0x{address + i:X}",
            )
            if len(logs) >= MAX_MEMORY_FINDINGS:
                return


def marker_in_memory(lower_data: bytes, marker: str) -> bool:
    raw = marker.encode("latin-1", "ignore")
    wide = marker.encode("utf-16le", "ignore")
    return raw in lower_data or wide in lower_data


def is_executable_protection(protect: int) -> bool:
    return (protect & 0xFF) in EXECUTABLE_PROTECTIONS


def has_private_pe_image(data: bytes) -> bool:
    index = data.find(b"MZ")
    if index < 0 or index > 4096:
        return False
    return b"PE\x00\x00" in data[index:index + 4096]


def agent_arguments(command: str) -> list[str]:
    agents = []
    tokens = tokenize(command)
    flags = ("-javaagent", "-agentpath", "-agentlib")
    for index, token in enumerate(tokens):
        lower = token.lower()
        for flag in flags:
            if lower.startswith(flag + ":") or lower.startswith(flag + "="):
                agents.append(token)
            elif lower == flag and index + 1 < len(tokens):
                agents.append(token + " " + tokens[index + 1])
    return agents


def scan_ghost(pid: int | None = None) -> dict:
    if pid is None:
        processes = minecraft_like_processes()
        target = "Process scan"
    else:
        processes = [find_process(pid)]
        target = f"Process scan: PID {pid}"
    if not processes:
        return ok(target, [summary("No Minecraft-like Java processes found.", target)])
    findings = [item for item in (scan_ghost_process(process) for process in processes) if item]
    if not findings:
        return ok(target, [summary(f"Checked {len(processes)} process(es). No runtime signatures found.", target)])
    return ok(target, findings)


def find_process(pid: int) -> dict:
    for process in java_processes():
        if int(process["pid"]) == int(pid):
            return process
    return {"pid": int(pid), "name": "java", "command": "selected process"}


def summary(detail: str, target: str) -> dict:
    return result_item(
        "Process scan summary",
        target,
        0,
        False,
        False,
        "Process",
        [entry("Process scan", "Process Scan", detail)],
    )


def list_program_tools() -> dict:
    tools = list_launchable_tools(PROGRAM_SIGNATURES)
    for tool in tools:
        if tool["name"] in BETA_TOOL_NAMES:
            tool["group"] = "beta"
        elif tool["name"] in OTHER_TOOL_NAMES:
            tool["group"] = "other"
        else:
            tool["group"] = "alpha"
    return {"ok": True, "target": "Tools", "tools": tools}


def list_command_tools() -> dict:
    return {"ok": True, "target": "Commands", "tools": list_launchable_tools(COMMAND_SIGNATURES)}


def list_launchable_tools(signatures: list[dict]) -> list[dict]:
    processes = all_processes()
    installed = installed_program_entries()
    files = candidate_program_files(signatures)
    tools = []

    for signature in signatures:
        candidates = []

        for process in processes:
            text = " ".join([
                str(process.get("name", "")),
                str(process.get("path", "")),
                str(process.get("command", "")),
            ])
            if matches_program(signature, text):
                process_path = process.get("path") or ""
                if process_path:
                    candidates.append(tool_candidate(process_path, "Running process", f"PID {process.get('pid')}"))

        for item in installed:
            text = " ".join([
                item.get("name", ""),
                item.get("publisher", ""),
                item.get("location", ""),
                item.get("icon", ""),
            ])
            if matches_program(signature, text):
                for path in install_launch_paths(signature, item):
                    candidates.append(tool_candidate(path, "Installed", item.get("name", "")))

        for file_path in files:
            if matches_program(signature, str(file_path)):
                candidates.append(tool_candidate(str(file_path), "Portable file", str(file_path)))

        candidates = dedupe_tool_candidates(candidates)
        best = first_launchable_candidate(candidates)
        tools.append({
            "name": signature["name"],
            "status": "Found" if best else "Missing",
            "path": best["path"] if best else "",
            "source": best["source"] if best else "Not found",
            "note": best["note"] if best else "No executable or shortcut found",
            "downloadAvailable": bool(signature.get("download_url")),
            "candidates": candidates,
        })

    return tools


def download_program_tool(name: str, progress=None) -> dict:
    signature = find_program_signature(name)
    if not signature:
        return error(f"Unknown tool: {name}")

    url = signature.get("download_url")
    if not url:
        return error(f"No official download URL configured for {signature['name']}. Add it manually to the tools folder.")
    if not is_allowed_download_url(str(url)):
        return error("Download URL is not in the allowed official host list.")

    target_dir = TOOLS_DIR / safe_folder_name(str(signature["name"]))
    target_dir.mkdir(parents=True, exist_ok=True)
    suffix = ".zip" if signature.get("download_type") == "zip" else Path(str(urlparse(str(url)).path)).suffix or ".download"

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            temp_path = Path(tmp.name)
        try:
            download_file(str(url), temp_path, progress)
            if signature.get("download_type") == "zip" or temp_path.suffix.lower() == ".zip":
                extract_zip_safe(temp_path, target_dir)
            else:
                final_path = target_dir / Path(str(urlparse(str(url)).path)).name
                replace_file(temp_path, final_path)
            best = find_launchable_in_dir(signature, target_dir)
            return {
                "ok": True,
                "message": "Downloaded",
                "name": signature["name"],
                "path": str(best) if best else str(target_dir),
            }
        finally:
            try:
                if temp_path.exists():
                    temp_path.unlink()
            except OSError:
                pass
    except Exception as exc:
        return error(str(exc))


def find_program_signature(name: str) -> dict | None:
    for signature in PROGRAM_SIGNATURES:
        if str(signature["name"]).lower() == str(name).lower():
            return signature
    for signature in COMMAND_SIGNATURES:
        if str(signature["name"]).lower() == str(name).lower():
            return signature
    return None


def clear_downloaded_tools() -> dict:
    try:
        if not TOOLS_DIR.exists():
            return {"ok": True, "message": "Downloaded tools folder is empty.", "deleted": 0}

        root = TOOLS_DIR.resolve()
        deleted = 0
        for child in list(TOOLS_DIR.iterdir()):
            resolved = child.resolve()
            if resolved == root or not str(resolved).lower().startswith(str(root).lower() + os.sep):
                continue
            if child.is_dir() and not child.is_symlink():
                shutil.rmtree(child)
            else:
                child.unlink()
            deleted += 1

        return {"ok": True, "message": "Deleted downloaded tools.", "deleted": deleted}
    except Exception as exc:
        return error(str(exc))


def is_allowed_download_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme == "https" and parsed.netloc.lower() in ALLOWED_DOWNLOAD_HOSTS


def download_file(url: str, destination: Path, progress=None) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": f"AuroraChecker/{APP_VERSION}"})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(request, timeout=45) as response:
        final_host = urlparse(response.geturl()).netloc.lower()
        if final_host not in ALLOWED_DOWNLOAD_HOSTS:
            raise RuntimeError(f"Redirected to non-official host: {final_host}")
        total = int(response.headers.get("Content-Length", "0") or 0)
        received = 0
        if progress:
            progress(0, total)
        with destination.open("wb") as out:
            while True:
                chunk = response.read(1024 * 256)
                if not chunk:
                    break
                out.write(chunk)
                received += len(chunk)
                if progress:
                    progress(received, total)


def extract_zip_safe(zip_path: Path, target_dir: Path) -> None:
    target_root = target_dir.resolve()
    with zipfile.ZipFile(zip_path) as zf:
        for member in zf.infolist():
            if member.is_dir():
                continue
            destination = (target_root / member.filename).resolve()
            if not str(destination).lower().startswith(str(target_root).lower() + os.sep):
                raise RuntimeError("Blocked unsafe zip entry: " + member.filename)
            destination.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(member) as src, destination.open("wb") as dst:
                while True:
                    chunk = src.read(1024 * 256)
                    if not chunk:
                        break
                    dst.write(chunk)


def replace_file(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        destination.unlink()
    source.replace(destination)


def find_launchable_in_dir(signature: dict, root: Path) -> Path | None:
    exe_names = {name.lower() for name in signature["exe"]}
    try:
        for path in root.rglob("*"):
            if path.is_file() and path.name.lower() in exe_names:
                return path
        for path in root.rglob("*.exe"):
            if matches_program(signature, str(path)):
                return path
    except OSError:
        return None
    return None


def safe_folder_name(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_. -]+", "_", name).strip(" .") or "tool"


def tool_candidate(path: str, source: str, note: str = "") -> dict:
    cleaned = clean_launch_path(path)
    return {
        "path": cleaned,
        "source": source,
        "note": note,
        "launchable": is_launchable_path(cleaned),
    }


def install_launch_paths(signature: dict, item: dict) -> list[str]:
    paths = []
    icon = clean_launch_path(item.get("icon", ""))
    if icon:
        paths.append(icon)
    location = clean_launch_path(item.get("location", ""))
    if location:
        location_path = Path(location)
        if location_path.is_file():
            paths.append(str(location_path))
        elif location_path.is_dir():
            for exe in signature["exe"]:
                direct = location_path / exe
                if direct.exists():
                    paths.append(str(direct))
            try:
                for child in location_path.rglob("*.exe"):
                    if matches_program(signature, str(child)):
                        paths.append(str(child))
                        break
            except OSError:
                pass
    return paths


def clean_launch_path(path: str) -> str:
    value = (path or "").strip().strip("\"'")
    if not value:
        return ""
    if "," in value and value.lower().endswith((".exe,0", ".dll,0")):
        value = value.rsplit(",", 1)[0]
    if value.startswith("@"):
        value = value[1:]
    return value.strip().strip("\"'")


def is_launchable_path(path: str) -> bool:
    if not path:
        return False
    try:
        p = Path(path)
        return p.exists() and p.is_file() and p.suffix.lower() in (".exe", ".lnk", ".bat", ".cmd")
    except OSError:
        return False


def dedupe_tool_candidates(candidates: list[dict]) -> list[dict]:
    seen = set()
    result = []
    for candidate in candidates:
        key = normalize_text(candidate.get("path", ""))
        if not key or key in seen:
            continue
        seen.add(key)
        result.append(candidate)
    return result


def first_launchable_candidate(candidates: list[dict]) -> dict | None:
    for candidate in candidates:
        if candidate.get("launchable"):
            return candidate
    return None


def open_program_tool(path: str) -> dict:
    cleaned = clean_launch_path(path)
    if not is_launchable_path(cleaned):
        return error(f"Tool path is not launchable: {cleaned or 'empty'}")
    try:
        os.startfile(cleaned)
        return {"ok": True, "message": "Started", "path": cleaned}
    except Exception as exc:
        return error(str(exc))


def open_command_tool(path: str) -> dict:
    return open_program_tool(path)


def installed_program_entries() -> list[dict]:
    script = (
        "$paths = 'HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*',"
        "'HKLM:\\Software\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*',"
        "'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*'; "
        "Get-ItemProperty $paths -ErrorAction SilentlyContinue | "
        "Where-Object { $_.DisplayName } | "
        "ForEach-Object { \"$($_.DisplayName)`t$($_.DisplayVersion)`t$($_.Publisher)`t$($_.InstallLocation)`t$($_.DisplayIcon)\" }"
    )
    entries = []
    for line in powershell(script):
        parts = line.split("\t", 4)
        while len(parts) < 5:
            parts.append("")
        entries.append({
            "name": parts[0],
            "version": parts[1],
            "publisher": parts[2],
            "location": parts[3],
            "icon": parts[4],
        })
    return entries


def candidate_program_files(signatures: list[dict] | None = None) -> list[Path]:
    signatures = signatures or PROGRAM_SIGNATURES
    target_names = {name.lower() for signature in signatures for name in signature["exe"]}
    roots = program_search_roots()
    hits: list[Path] = []
    seen: set[str] = set()
    for root in roots:
        max_depth = 6 if "program files" in str(root).lower() else 5
        scanned = 0
        for current, dirs, files in safe_walk(root):
            depth = depth_from(root, Path(current))
            if depth > max_depth:
                dirs[:] = []
                continue
            dirs[:] = [d for d in dirs if d.lower() not in ("node_modules", ".git", "__pycache__", "windowsapps")]
            for file_name in files:
                scanned += 1
                lower = file_name.lower()
                if scanned > 16000:
                    break
                if lower in target_names or (lower.endswith((".lnk", ".cmd", ".bat")) and matches_any_program_name(lower, signatures)):
                    path = Path(current) / file_name
                    key = str(path).lower()
                    if key not in seen:
                        seen.add(key)
                        hits.append(path)
            if scanned > 16000:
                break
    # if some tools still missing, full PC search via dir /s (everything-like)
    found_names = {p.name.lower() for p in hits}
    missing_names = target_names - found_names
    if missing_names:
        exclude_dirs = ("c:\\windows", "c:\\$recycle.bin", "c:\\system volume information",
                        "c:\\config.msi", "c:\\perflogs", "c:\\recovery", "c:\\programdata\\microsoft")
        for exe_name in sorted(missing_names)[:10]:  # limit to 10 to avoid timeout
            cmd = ["cmd.exe", "/d", "/c", f'dir /s /b /a-d "C:\\{exe_name}" 2>nul']
            try:
                proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="ignore", timeout=30, **hidden_subprocess_options())
                for line in proc.stdout.splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    p = Path(line)
                    key = str(p).lower()
                    if key in seen:
                        continue
                    if any(key.startswith(excl) for excl in exclude_dirs):
                        continue
                    seen.add(key)
                    hits.append(p)
            except Exception:
                continue
    return hits


def program_search_roots() -> list[Path]:
    candidates = []
    env_names = ("ProgramFiles", "ProgramFiles(x86)", "LOCALAPPDATA", "APPDATA", "ProgramData")
    for name in env_names:
        value = os.environ.get(name)
        if value:
            candidates.append(Path(value))
    home = Path.home()
    candidates.extend([
        TOOLS_DIR,
        BUNDLED_TOOLS_DIR,
        home / "Desktop",
        home / "Downloads",
        home / "Documents",
        Path(r"C:\Tools"),
        Path(r"C:\Portable"),
        Path(r"C:\Users\Public\Desktop"),
        Path(os.environ.get("ProgramData", r"C:\ProgramData")) / "Microsoft" / "Windows" / "Start Menu" / "Programs",
    ])

    roots = []
    seen: set[str] = set()
    for path in candidates:
        try:
            resolved = str(path.resolve()).lower()
            if resolved not in seen and path.exists() and path.is_dir():
                seen.add(resolved)
                roots.append(path)
        except OSError:
            continue
    return roots


def safe_walk(root: Path):
    try:
        yield from os.walk(root, topdown=True)
    except OSError:
        return


def depth_from(root: Path, current: Path) -> int:
    try:
        return len(current.relative_to(root).parts)
    except Exception:
        return 0


def matches_program(signature: dict, text: str) -> bool:
    lower = normalize_text(text)
    if not lower:
        return False
    if any(name.lower() in lower for name in signature["process"]):
        return True
    if any(name.lower() in lower for name in signature["exe"]):
        return True
    return any(keyword.lower() in lower for keyword in signature["keywords"])


def matches_any_program_name(text: str, signatures: list[dict] | None = None) -> bool:
    signatures = signatures or PROGRAM_SIGNATURES
    lower = normalize_text(text)
    return any(matches_program(signature, lower) for signature in signatures)


def normalize_text(value: str) -> str:
    return (value or "").replace("/", "\\").lower()


def first_existing_text(paths: list[str]) -> str:
    for path in paths:
        if path and path != "running process":
            return path
    return paths[0] if paths else "not found"


def dedupe_entries(entries: list[dict]) -> list[dict]:
    seen: set[str] = set()
    result = []
    for item in entries:
        key = f"{item.get('className')}|{item.get('type')}|{item.get('detail')}"
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def compact(value: str, max_len: int = 180) -> str:
    value = " ".join((value or "").split())
    return value if len(value) <= max_len else value[: max_len - 3] + "..."


def ok(target: str, items: list[dict]) -> dict:
    return {
        "ok": True,
        "target": target,
        "items": items,
        "stats": {
            "items": len(items),
            "risks": sum(1 for item in items if item.get("suspicious")),
            "trusted": sum(1 for item in items if item.get("modrinthFound")),
            "clean": sum(1 for item in items if not item.get("suspicious")),
        },
    }


def error(message: str) -> dict:
    return {"ok": False, "error": message, "items": [], "stats": {"items": 0, "risks": 0, "trusted": 0, "clean": 0}}


# ---------------- JAR | DLL activity backend ----------------

_USN_RAW_CACHE: dict[str, Any] = {"text": "", "ts": 0.0}

_USN_ACCESS_DENIED = False

_USN_CACHE_TTL = 300000  # 5 minutes


def _read_usn_raw(timeout: int = 120) -> str:
    global _USN_ACCESS_DENIED
    now = time.time() * 1000
    if _USN_RAW_CACHE["text"] and now - _USN_RAW_CACHE["ts"] < _USN_CACHE_TTL:
        return _USN_RAW_CACHE["text"]
    cmd = ["cmd.exe", "/d", "/c", "fsutil usn readjournal C: csv"]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout, **hidden_subprocess_options())
        stdout = proc.stdout or ""
        stderr = proc.stderr or ""
        if not stdout.strip():
            if "denied" in stderr.lower() or "error 5" in stderr.lower() or "доступ" in stderr.lower():
                _USN_ACCESS_DENIED = True
            _USN_RAW_CACHE["text"] = ""
            _USN_RAW_CACHE["ts"] = now
            return ""
        _USN_RAW_CACHE["text"] = stdout
        _USN_RAW_CACHE["ts"] = now
        return stdout
    except Exception:
        return ""


def _activity_line(date: str, action: str, name: str, path: str = "") -> dict:
    detail = f"{date} | {action} | {name}"
    if path:
        detail += f" | {path}"
    risk = action.lower() == "error" or "unsigned" in action.lower()
    return {
        "className": name or "activity",
        "type": action,
        "detail": detail,
        "date": date,
        "action": action,
        "name": name,
        "path": path,
        "size": "-",
        "source": "Journal",
        "verdict": "Risk" if risk else "Info",
        "suspicious": risk,
        "analysisResults": [entry(name or "activity", action, detail)],
    }


def _parse_csv_line(line: str) -> list[str]:
    try:
        return next(csv.reader([line]))
    except Exception:
        return [line]


def _extract_hex_mask(raw: str) -> int:
    m = re.search(r'0x([0-9a-fA-F]+)', raw)
    if m:
        try:
            return int(m.group(1), 16)
        except ValueError:
            pass
    return 0


def _date_from_fields(fields: list[str]) -> str:
    for f in fields:
        v = f.strip().strip('"')
        if re.search(r'\d{2,4}[./-]\d{1,2}[./-]\d{1,2}', v) and ':' in v:
            return v
    return "-"


def _name_from_line(fields: list[str], raw: str, ext: str) -> str:
    low_ext = ext.lower()
    if len(fields) > 1:
        c = fields[1].strip().strip('"')
        if c and c.lower() not in ("name", "file name", "filename"):
            return Path(c).name
    for f in fields:
        v = f.strip().strip('"')
        if v.lower().endswith(low_ext):
            return Path(v).name
    low = raw.lower()
    pos = low.find(low_ext)
    if pos < 0:
        return ""
    s = pos
    while s > 0 and raw[s - 1] not in ',|"\t\r\n ':
        s -= 1
    while s < pos and raw[s] in ' "':
        s += 1
    e = pos + len(ext)
    while e < len(raw) and raw[e] not in ',|"\t\r\n ':
        e += 1
    return Path(raw[s:e].strip().strip('"')).name


def _resolve_path(file_ref: str, parent_ref: str, name: str, cache: dict | None = None) -> str:
    if cache is not None:
        key = f"{file_ref}|{parent_ref}"
        if key in cache:
            cached = cache[key]
            return f"{cached}\\{name}" if cached else name
    for ref in (file_ref, parent_ref):
        if not ref:
            continue
        try:
            rid = f"0x{ref}" if not ref.startswith("0x") else ref
            r = subprocess.run(
                ["cmd.exe", "/d", "/c", f"fsutil file queryfilenamebyid C: {rid} 2>nul"],
                capture_output=True, text=True, encoding="utf-8", errors="ignore",
                timeout=15, **hidden_subprocess_options(),
            )
            for line in r.stdout.splitlines():
                m = re.search(r'([A-Za-z]:\\.+)', line)
                if m:
                    p = m.group(1).strip().rstrip("\\")
                    resolved = f"{p}\\{name}" if ref == parent_ref else p
                    if cache is not None:
                        cache[key] = p
                    return resolved
        except Exception:
            continue
    if cache is not None:
        cache[key] = ""
    return name


_SYSTEM_FILE_RE = re.compile(
    r'^(api-ms-win-|ext-ms-win-|wow64|ntdll|kernel32|kernelbase|user32|gdi32|shell32|'
    r'ole32|oleaut32|comctl32|comdlg32|advapi32|secur32|crypt32|bcrypt|rpcrt4|shlwapi|shcore|'
    r'msvcrt|msvcp|concrt|vcruntime|mscoree|clr|diasymreader|sos|culture\.|system\..*\.dll|'
    r'windows\..*\.dll|twinapi|taskbarlib|authz|wkscli|srvcli|netapi32|samlib|dnsapi|'
    r'winhttp|wininet|urlmon|ieframe|browseui|vbscript|jscript|scrobj|scrrun|wshext|'
    r'wshom|mshtml|iertutil|win32k|dxg|d3d|opengl32|glu32|ddraw|dsound|dmusic|dmsynth|dmloader|'
    r'msctf|uxtheme|dwmapi|mlang|imjpmig|imkr|chsbrkr|chtbrkr|dayi|cangjie|quick|'
    r'pinyin|wubi|chaos|array|codex|phon|corim|da_api)' + r'\.(dll|exe|ocx)$',
    re.I
)

_SYSTEM_DIR_PREFIXES = (
    "c:\\windows",
    "c:\\program files",
    "c:\\program files (x86)",
    "c:\\programdata",
    "c:\\$recycle.bin",
    "c:\\system volume information",
    "c:\\config.msi",
    "c:\\perflogs",
    "c:\\intel",
    "c:\\amd",
    "c:\\nvidia",
    "c:\\drivers",
    "c:\\boot",
    "c:\\recovery",
)

_SYSTEM_PATH_RE = re.compile(
    r'^(' + '|'.join(re.escape(p) for p in _SYSTEM_DIR_PREFIXES) + r')',
    re.I
)


def _is_system_file(fname: str) -> bool:
    if _SYSTEM_FILE_RE.match(fname):
        return True
    low = fname.lower()
    # GUID-like filenames (common in WinSxS)
    if len(low) > 30 and re.search(r'[0-9a-f]{8}[-_][0-9a-f]{4}', low):
        return True
    return False


def _is_system_path(path: str) -> bool:
    return bool(_SYSTEM_PATH_RE.search(path))


def _batch_resolve_paths(entries: list[dict]) -> dict[str, str]:
    """Resolve paths for unique (frn, prn) combos using fsutil, return {key: path}."""
    uniq: dict[str, tuple[str, str]] = {}
    for e in entries:
        frn, prn = e.get("file_ref", ""), e.get("parent_ref", "")
        if frn and prn:
            uniq[f"{frn}|{prn}"] = (frn, prn)
    cache: dict[str, str] = {}
    for key, (frn, prn) in uniq.items():
        if key in cache:
            continue
        rid = f"0x{prn}" if not prn.startswith("0x") else prn
        try:
            r = subprocess.run(
                ["cmd.exe", "/d", "/c", f"fsutil file queryfilenamebyid C: {rid} 2>nul"],
                capture_output=True, text=True, encoding="utf-8", errors="ignore",
                timeout=10, **hidden_subprocess_options(),
            )
            for line in r.stdout.splitlines():
                m = re.search(r'([A-Za-z]:\\.+)', line)
                if m:
                    cache[key] = m.group(1).strip().rstrip("\\")
                    break
        except Exception:
            pass
        if key not in cache:
            cache[key] = ""
    return cache

def _reason_to_action(mask: int) -> str:
    parts = []
    if mask & 0x00000001: parts.append("overwrite")
    if mask & 0x00000002: parts.append("extend")
    if mask & 0x00000004: parts.append("truncation")
    if mask & 0x00000010: parts.append("named_overwrite")
    if mask & 0x00000020: parts.append("named_extend")
    if mask & 0x00000040: parts.append("named_truncation")
    if mask & 0x00000100: parts.append("create")
    if mask & 0x00000200: parts.append("delete")
    if mask & 0x00000400: parts.append("ea_change")
    if mask & 0x00000800: parts.append("sec_change")
    if mask & 0x00001000: parts.append("rename_old")
    if mask & 0x00002000: parts.append("rename_new")
    if mask & 0x00004000: parts.append("indexable")
    if mask & 0x00008000: parts.append("info_change")
    if mask & 0x00010000: parts.append("hardlink")
    if mask & 0x00020000: parts.append("compress")
    if mask & 0x00040000: parts.append("encrypt")
    if mask & 0x00080000: parts.append("object_id")
    if mask & 0x00100000: parts.append("reparse")
    if mask & 0x00200000: parts.append("stream")
    if mask & 0x00400000: parts.append("transacted")
    if mask & 0x80000000: parts.append("close")
    return "+".join(parts) if parts else f"0x{mask:08x}"


def _scan_usn(ext: str, valid_names: set[str] | None = None, timeout: int = 120) -> tuple[list[dict], list[dict], str]:
    raw = _read_usn_raw(timeout)
    if not raw:
        if _USN_ACCESS_DENIED:
            msg = "run as admin for USN journal"
            return [_activity_line("-", "error", msg, "")], [_activity_line("-", "error", msg, "")], msg
        return [], [], ""
    cutoff = time.time() - 14 * 86400
    activity_rows: list[dict] = []
    deleted_rows: list[dict] = []
    for line in raw.splitlines():
        if not line.strip():
            continue
        if ext.lower() not in line.lower():
            continue
        try:
            row = next(csv.reader([line]))
        except Exception:
            continue
        if len(row) < 7:
            continue
        fname = row[1].strip() if len(row) > 1 else ""
        if not fname.lower().endswith(ext.lower()):
            continue
        # skip files not in user directories
        if valid_names is not None and fname.lower() not in valid_names:
            continue
        reason_hex = row[3].strip() if len(row) > 3 else ""
        ts = row[5].strip().strip('"') if len(row) > 5 else ""
        if ts:
            _pass = False
            for fmt in ("%d.%m.%y %H:%M:%S", "%d.%m.%Y %H:%M:%S"):
                try:
                    dt = datetime.strptime(ts, fmt)
                    if dt.timestamp() >= cutoff:
                        _pass = True
                    break
                except ValueError:
                    continue
            if not _pass:
                continue
        if reason_hex.startswith("0x"):
            try:
                mask = int(reason_hex, 16)
            except ValueError:
                mask = 0
        else:
            mask = 0
        action = _reason_to_action(mask)
        e = _activity_line(ts, action, fname, "")
        if mask & 0x00000200:
            deleted_rows.append(e)
        else:
            activity_rows.append(e)
    def _sort_key(row: dict) -> tuple:
        d = (row.get("date") or "").strip()
        if not d or d in ("", "-"):
            return (0, 0)
        for fmt in ("%d.%m.%y %H:%M:%S", "%d.%m.%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try:
                return (1, datetime.strptime(d, fmt).timestamp())
            except ValueError:
                continue
        return (0, 0)
    activity_rows.sort(key=_sort_key, reverse=True)
    deleted_rows.sort(key=_sort_key, reverse=True)
    return activity_rows, deleted_rows, ""


def _scan_roots() -> list[Path]:
    roots: list[Path] = []
    user = os.environ.get("USERPROFILE")
    appdata = os.environ.get("APPDATA")
    if user:
        roots.extend([Path(user) / "Downloads", Path(user) / "Desktop"])
    if appdata:
        roots.extend([
            Path(appdata) / ".minecraft",
            Path(appdata) / ".tlauncher" / "legacy" / "Minecraft" / "game",
        ])
    result: list[Path] = []
    seen: set[str] = set()
    for root in roots:
        try:
            k = str(root.resolve()).lower()
            if k not in seen and root.is_dir():
                seen.add(k)
                result.append(root)
        except OSError:
            continue
    return result


def _skip_path(p: Path) -> bool:
    low = str(p).replace("/", "\\").lower()
    blocked = (
        "\\windows\\", "\\program files\\", "\\program files (x86)\\",
        "\\node_modules\\", "\\python\\", "\\python3\\", "\\jdk\\", "\\jre\\",
        "\\java\\", "\\libraries\\", "\\assets\\", "\\runtime\\", "\\versions\\",
        "\\site-packages\\", "\\venv\\", "\\.gradle\\", "\\.m2\\",
    )
    return any(item in low for item in blocked)


def _scan_user_files(ext: str, max_files: int = 8000, max_rows: int = 300) -> list[dict]:
    if os.name != "nt":
        return [_activity_line("-", "error", "scan works only on Windows", "")]
    rows: list[dict] = []
    seen: set[str] = set()
    scanned = 0
    for root in _scan_roots():
        try:
            for f in root.rglob(f"*{ext}"):
                scanned += 1
                if scanned > max_files:
                    break
                if not f.is_file() or _skip_path(f):
                    continue
                k = str(f).lower()
                if k in seen:
                    continue
                seen.add(k)
                try:
                    st = f.stat()
                    if st.st_size <= 0:
                        continue
                except OSError:
                    continue
                try:
                    ct = datetime.fromtimestamp(st.st_ctime).strftime("%Y-%m-%d %H:%M:%S")
                except Exception:
                    ct = "-"
                rows.append(_activity_line(ct, "created", f.name, str(f)))
                if len(rows) >= max_rows:
                    return rows
        except Exception:
            continue
    if not rows:
        rows.append(_activity_line("-", "not found", f"{ext} not found", ""))
    return rows


def _scan_bam_deleted(ext: str, max_rows: int = 100) -> list[dict]:
    """Read BAM registry entries for executed files that no longer exist.
    Same approach as HolyCheck's ScanUnsignedDlls()."""
    if os.name != "nt":
        return [_activity_line("-", "error", "BAM scan works only on Windows", "")]
    import winreg
    bam_paths = [
        r"SYSTEM\CurrentControlSet\Services\bam\State\UserSettings",
        r"SYSTEM\CurrentControlSet\Services\dam\State\UserSettings",
    ]
    low_ext = ext.lower()
    seen_targets: set[str] = set()
    rows: list[dict] = []
    for sub_key in bam_paths:
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, sub_key)
        except OSError:
            continue
        try:
            sid_count = winreg.QueryInfoKey(key)[0]
            for i in range(sid_count):
                try:
                    sid_name = winreg.EnumKey(key, i)
                except OSError:
                    continue
                try:
                    sid_key = winreg.OpenKey(key, sid_name)
                except OSError:
                    continue
                try:
                    val_count = winreg.QueryInfoKey(sid_key)[1]
                    for j in range(val_count):
                        try:
                            val_name, val_data, _ = winreg.EnumValue(sid_key, j)
                        except OSError:
                            continue
                        if not val_name or not isinstance(val_data, bytes):
                            continue
                        device_path = val_name
                        try:
                            ft_raw = val_data[:8]
                            ft_low = int.from_bytes(ft_raw[:4], "little")
                            ft_high = int.from_bytes(ft_raw[4:8], "little")
                            ft_val = (ft_high << 32) | ft_low
                            if ft_val == 0:
                                continue
                        except Exception:
                            continue
                        if not device_path.lower().endswith(low_ext):
                            continue
                        dos_path = _device_to_dos(device_path)
                        if not dos_path:
                            dos_path = device_path
                        if os.path.exists(dos_path):
                            continue
                        key_name = dos_path.lower()
                        if key_name in seen_targets:
                            continue
                        seen_targets.add(key_name)
                        try:
                            ft_s = datetime(1601, 1, 1) + timedelta(microseconds=ft_val // 10)
                            date_str = ft_s.strftime("%Y-%m-%d %H:%M:%S")
                        except Exception:
                            date_str = "-"
                        rows.append(_activity_line(date_str, "deleted", os.path.basename(dos_path), dos_path))
                        if len(rows) >= max_rows:
                            return rows
                finally:
                    try:
                        sid_key.Close()
                    except Exception:
                        pass
        finally:
            try:
                key.Close()
            except Exception:
                pass
    if not rows:
        rows.append(_activity_line("-", "not found", f"no deleted {ext} found via bam", ""))
    return rows


def _device_to_dos(device_path: str) -> str:
    """Convert \Device\HarddiskVolume2\path\to\file to C:\path\to\file"""
    if not device_path.startswith("\\"):
        return device_path
    try:
        drives = []
        for d in range(26):
            letter = chr(ord("A") + d)
            drive = f"{letter}:\\"
            import ctypes
            buf = ctypes.create_unicode_buffer(1024)
            if ctypes.windll.kernel32.QueryDosDeviceW(letter + ":", buf, 1024):
                dev = buf.value
                if dev and device_path.lower().startswith(dev.lower()):
                    relative = device_path[len(dev):]
                    return drive.rstrip("\\") + relative
    except Exception:
        pass
    return device_path


def _scan_lnk_deleted(ext: str, max_rows: int = 100) -> list[dict]:
    if os.name != "nt":
        return [_activity_line("-", "error", "LNK scan works only on Windows", "")]
    lnk_dirs: list[str] = []
    user = os.environ.get("USERPROFILE", "")
    appdata = os.environ.get("APPDATA", "")
    if user:
        lnk_dirs.append(os.path.join(user, "AppData", "Roaming", "Microsoft", "Windows", "Recent"))
    if appdata:
        lnk_dirs.append(os.path.join(appdata, "Microsoft", "Windows", "Recent", "AutomaticDestinations"))

    all_lnks: list[str] = []
    for d in lnk_dirs:
        if os.path.isdir(d):
            try:
                for entry in os.listdir(d):
                    if entry.lower().endswith((".lnk", ".customdestinations-ms")):
                        all_lnks.append(os.path.join(d, entry))
            except OSError:
                continue

    if not all_lnks:
        return []

    lnk_list_path = os.path.join(tempfile.gettempdir(), f"aurora_lnk_{os.getpid()}.txt")
    ps_script_path = os.path.join(tempfile.gettempdir(), f"aurora_lnk_{os.getpid()}.ps1")
    try:
        with open(lnk_list_path, "w", encoding="utf-8") as f:
            for p in all_lnks:
                f.write(p + "\n")
        low_ext = ext.lower()
        ps_code = f"""param([string]$listPath,[string]$ext)
    $sh = New-Object -ComObject WScript.Shell
    Get-Content $listPath | ForEach-Object {{
        try {{
            $sc = $sh.CreateShortcut($_)
            if ($sc.TargetPath -and $sc.TargetPath.ToLower().EndsWith($ext)) {{
                "$($sc.TargetPath),$($sc.LastWriteTime.ToString('yyyy-MM-dd HH:mm:ss'))"
            }}
        }} catch {{}}
    }}"""
        with open(ps_script_path, "w", encoding="utf-8") as f:
            f.write(ps_code)
        proc = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ps_script_path, lnk_list_path, low_ext],
            capture_output=True, text=True, encoding="utf-8", errors="ignore",
            timeout=60, **hidden_subprocess_options(),
        )
    finally:
        try:
            os.unlink(lnk_list_path)
        except OSError:
            pass
        try:
            os.unlink(ps_script_path)
        except OSError:
            pass

    seen_targets: set[str] = set()
    rows: list[dict] = []
    if 'proc' in dir() and proc and proc.stdout:
        for line in proc.stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            parts = line.split(",", 1)
            target = parts[0].strip()
            if not target or not os.path.exists(target):
                key = target.lower() if target else ""
                if not key or key in seen_targets:
                    continue
                seen_targets.add(key)
                date = parts[1].strip() if len(parts) > 1 else "-"
                rows.append(_activity_line(date, "deleted", os.path.basename(target), target))
                if len(rows) >= max_rows:
                    break
    if not rows:
        rows.append(_activity_line("-", "not found", f"no deleted {ext} found via lnk", ""))
    return rows


def _enable_services():
    """Start services needed for BAM/USN scanning (same as HolyCheck's OpenCmdEnableServices)."""
    if os.name != "nt":
        return
    try:
        import ctypes
        if not ctypes.windll.shell32.IsUserAnAdmin():
            return
    except Exception:
        return
    services = [
        ("PcaSvc", "auto"),
        ("DPS", "auto"),
        ("SysMain", "auto"),
        ("EventLog", "auto"),
        ("bam", "auto"),
    ]
    for srv, mode in services:
        try:
            subprocess.run(
                ["cmd.exe", "/d", "/c", f"sc config {srv} start= {mode} >nul 2>&1 & sc start {srv} >nul 2>&1"],
                capture_output=True, timeout=10,
            )
        except Exception:
            pass


def scan_jar_dll_activity() -> dict:
    _enable_services()
    # scan user directories first (these are the only files we care about)
    jar_user = _scan_user_files(".jar")
    dll_user = _scan_user_files(".dll")
    user_fnames: set[str] = set()
    for r in jar_user + dll_user:
        n = r.get("name", "")
        if n:
            user_fnames.add(n.lower())
    # USN: only show files that match user directories (no system files)
    jar_activity, jar_deleted, jar_note = _scan_usn(".jar", user_fnames)
    dll_activity, dll_deleted, dll_note = _scan_usn(".dll", user_fnames)
    # BAM + LNK for deleted files
    jar_bam = _scan_bam_deleted(".jar")
    dll_bam = _scan_bam_deleted(".dll")
    jar_lnk_del = _scan_lnk_deleted(".jar")
    dll_lnk_del = _scan_lnk_deleted(".dll")
    deleted_rows = jar_deleted + dll_deleted + jar_bam + dll_bam + jar_lnk_del + dll_lnk_del
    items = []
    items.extend({**row, "section": "jar"} for row in jar_activity)
    items.extend({**row, "section": "dll"} for row in dll_activity)
    items.extend({**row, "section": "jar"} for row in jar_user)
    items.extend({**row, "section": "dll"} for row in dll_user)
    items.extend({**row, "section": "deleted"} for row in deleted_rows)
    jar_combined = jar_activity + jar_user
    dll_combined = dll_activity + dll_user
    def _sort_key(row: dict) -> tuple:
        d = (row.get("date") or "").strip()
        if not d or d == "-":
            return (0, 0)
        for fmt in ("%d.%m.%y %H:%M:%S", "%d.%m.%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try:
                dt = datetime.strptime(d, fmt)
                return (1, dt.timestamp())
            except ValueError:
                continue
        return (0, 0)
    jar_combined.sort(key=_sort_key, reverse=True)
    dll_combined.sort(key=_sort_key, reverse=True)
    deleted_rows.sort(key=_sort_key, reverse=True)
    note = jar_note or dll_note
    if not deleted_rows and not note:
        deleted_rows = [_activity_line("-", "not found", "no deleted jar/dll found", "")]
    return {
        "ok": True,
        "target": "JAR | DLL",
        "jarActivity": jar_combined,
        "dllActivity": dll_combined,
        "unsignedDll": [],
        "deletedActivity": deleted_rows,
        "note": note,
        "items": items,
        "stats": {
            "items": len(items),
            "jar": len(jar_combined),
            "dll": len(dll_combined),
            "deleted": len(deleted_rows),
            "risks": sum(1 for row in items if row.get("suspicious")),
            "trusted": 0,
            "clean": sum(1 for row in items if not row.get("suspicious")),
        },
    }


class AuroraApi:
    __slots__ = ("_window", "_injgen_lock", "_injgen_process", "_injgen_output", "_download_lock", "_downloads")

    def __init__(self) -> None:
        self._window = None
        self._injgen_lock = threading.Lock()
        self._injgen_process = None
        self._injgen_output: list[str] = []
        self._download_lock = threading.Lock()
        self._downloads: dict[str, dict] = {}

    def app_info(self) -> dict:
        return {"name": "AuroraChecker", "author": "zentixctm", "version": APP_VERSION}

    def default_mods_path(self) -> str:
        return default_mods_path()

    def choose_folder(self) -> str:
        try:
            import webview
            if not self._window:
                return ""
            result = self._window.create_file_dialog(webview.FOLDER_DIALOG)
            return result[0] if result else ""
        except Exception:
            return ""

    def choose_jar(self) -> str:
        try:
            import webview
            if not self._window:
                return ""
            result = self._window.create_file_dialog(webview.OPEN_DIALOG, file_types=("Jar files (*.jar)", "All files (*.*)"))
            return result[0] if result else ""
        except Exception:
            return ""

    def scan_path(self, path: str) -> dict:
        return scan_path(path)

    def list_processes(self) -> list[dict]:
        return java_processes()

    def scan_ghost(self, pid=None) -> dict:
        try:
            value = None if pid in (None, "", "auto") else int(pid)
            return scan_ghost(value)
        except Exception as exc:
            return error(str(exc))

    def launch_injgen_console(self) -> dict:
        try:
            exe_path = self._find_injgen()
            if not exe_path:
                return error("InjGen.exe not found in the bundled tools.")
            os.startfile(str(exe_path))
            return {"ok": True, "message": "Started"}
        except Exception as exc:
            return error(str(exc))

    def list_program_tools(self) -> dict:
        try:
            return list_program_tools()
        except Exception as exc:
            return error(str(exc))

    def list_command_tools(self) -> dict:
        try:
            return list_command_tools()
        except Exception as exc:
            return error(str(exc))

    def open_program_tool(self, path: str) -> dict:
        try:
            return open_program_tool(path)
        except Exception as exc:
            return error(str(exc))

    def open_command_tool(self, path: str) -> dict:
        try:
            return open_command_tool(path)
        except Exception as exc:
            return error(str(exc))

    def download_program_tool(self, name: str) -> dict:
        try:
            return download_program_tool(name)
        except Exception as exc:
            return error(str(exc))

    def start_program_download(self, name: str) -> dict:
        if not find_program_signature(name):
            return error(f"Unknown tool: {name}")
        job_id = uuid.uuid4().hex
        with self._download_lock:
            self._downloads[job_id] = {"name": name, "running": True, "received": 0, "total": 0, "result": None}

        def worker() -> None:
            def update(received: int, total: int) -> None:
                with self._download_lock:
                    job = self._downloads.get(job_id)
                    if job:
                        job.update({"received": received, "total": total})

            result = download_program_tool(name, update)
            with self._download_lock:
                job = self._downloads.get(job_id)
                if job:
                    job.update({"running": False, "result": result})

        threading.Thread(target=worker, daemon=True).start()
        return {"ok": True, "id": job_id}

    def download_status(self, job_id: str) -> dict:
        with self._download_lock:
            job = self._downloads.get(job_id)
            if not job:
                return error("Download task not found")
            total = int(job["total"])
            received = int(job["received"])
            if total > 0:
                percent = round(received * 100 / total)
            else:
                percent = -1  # unknown
            return {"ok": True, "running": bool(job["running"]), "percent": percent, "total": total, "received": received, "result": job["result"]}

    def clear_downloaded_tools(self) -> dict:
        try:
            return clear_downloaded_tools()
        except Exception as exc:
            return error(str(exc))

    def _find_injgen(self) -> Path | None:
        user = os.environ.get("USERPROFILE", "")
        injgen_paths = [
            BUNDLED_TOOLS_DIR / "InjGen" / "InjGen.exe",
            TOOLS_DIR / "InjGen" / "InjGen.exe",
            TOOLS_DIR / "injgen" / "InjGen.exe",
            APP_ROOT / "InjGen.exe",
            Path(user) / "Desktop" / "InjGen.exe",
            Path(user) / "Downloads" / "InjGen-main" / "x64" / "Release" / "InjGen.exe",
        ]
        for path in injgen_paths:
            try:
                if path.is_file():
                    return path
            except OSError:
                continue
        return None

    def _read_injgen_output(self, process: subprocess.Popen) -> None:
        assert process.stdout is not None
        for line in iter(process.stdout.readline, ""):
            with self._injgen_lock:
                self._injgen_output.append(line.rstrip("\r\n"))
        process.stdout.close()

    def start_injgen(self) -> dict:
        try:
            exe_path = self._find_injgen()
            if not exe_path:
                return error("InjGen.exe not found. Build it to x64/Release or place it in tools/InjGen/.")
            with self._injgen_lock:
                if self._injgen_process and self._injgen_process.poll() is None:
                    return {"ok": True, "started": False, "running": True}
                self._injgen_output = [f"Starting: {exe_path}"]
                self._injgen_process = subprocess.Popen(
                [str(exe_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                **hidden_subprocess_options(),
                )
                threading.Thread(target=self._read_injgen_output, args=(self._injgen_process,), daemon=True).start()
            return {"ok": True, "started": True, "running": True}
        except Exception as exc:
            return error(str(exc))

    def injgen_status(self) -> dict:
        with self._injgen_lock:
            process = self._injgen_process
            running = bool(process and process.poll() is None)
            output = "\n".join(self._injgen_output)
            if not running and not output:
                output = "InjGen: no output (no Minecraft Java process found)"
            return {"ok": True, "running": running, "output": output}

    def scan_jar_dll_activity(self) -> dict:
        try:
            return scan_jar_dll_activity()
        except Exception as exc:
            return error(str(exc))

    def usn_debug(self) -> dict:
        try:
            result = {"admin": False, "jarLines": 0, "dllLines": 0, "rawPreview": "",
                      "totalCsvLines": 0, "csvPath": ""}
            import ctypes
            result["admin"] = bool(ctypes.windll.shell32.IsUserAnAdmin())
        except:
            pass
        # dump ALL raw CSV to a temp file for inspection
        try:
            tmp = Path(tempfile.gettempdir()) / f"usn_dump_{os.getpid()}.csv"
            cmd = ["cmd.exe", "/d", "/c", "fsutil usn readjournal C: csv 2>&1"]
            proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="ignore", timeout=120, **hidden_subprocess_options())
            raw = proc.stdout
            tmp.write_text(raw, encoding="utf-8")
            lines = [l for l in raw.splitlines() if l.strip()]
            result["totalCsvLines"] = len(lines)
            result["rawPreview"] = raw[:2000]
            result["csvPath"] = str(tmp)
            # count jar/dll lines manually from raw
            jar_count = 0
            dll_count = 0
            for line in lines:
                if ".jar" in line.lower():
                    jar_count += 1
                if ".dll" in line.lower():
                    dll_count += 1
            result["jarLines"] = jar_count
            result["dllLines"] = dll_count
            result["jarPreview"] = "\n".join(l for l in lines if ".jar" in l.lower())[:2000]
            result["dllPreview"] = "\n".join(l for l in lines if ".dll" in l.lower())[:2000]
            # also write specific lines to separate files
            jar_path = Path(tempfile.gettempdir()) / f"usn_jar_{os.getpid()}.txt"
            dll_path = Path(tempfile.gettempdir()) / f"usn_dll_{os.getpid()}.txt"
            jar_path.write_text("\n".join(l for l in lines if ".jar" in l.lower()), encoding="utf-8")
            dll_path.write_text("\n".join(l for l in lines if ".dll" in l.lower()), encoding="utf-8")
            result["jarPath"] = str(jar_path)
            result["dllPath"] = str(dll_path)
        except Exception as exc:
            result["error"] = str(exc)
        return {"ok": True, **result}

    def ensure_admin(self) -> dict:
        try:
            import ctypes
            if ctypes.windll.shell32.IsUserAnAdmin():
                return {"ok": True, "restarted": False}
            exe = sys.executable
            script = Path(__file__).resolve()
            if getattr(sys, "frozen", False):
                args = [exe, "--auto-scan"]
            else:
                args = [exe, str(script.parent / "main.py"), "--auto-scan"]
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", args[0], " ".join(f'"{a}"' for a in args[1:]), None, 1
            )
            if self._window:
                self._window.destroy()
            return {"ok": True, "restarted": True}
        except Exception as exc:
            return error(str(exc))

    def self_destruct(self) -> dict:
        try:
            clear_downloaded_tools()
            log = APP_ROOT / "aurorachecker.log"
            if log.exists():
                log.unlink()
            pid = os.getpid()
            bat_path = Path(tempfile.gettempdir()) / f"cleanup_{pid}.bat"
            bat_content = f"""@echo off
title AuroraChecker Cleanup
:loop
tasklist /FI "PID eq {pid}" 2>nul | find "{pid}" >nul
if not errorlevel 1 (
    ping -n 2 127.0.0.1 >nul
    goto loop
)
ping -n 1 127.0.0.1 >nul
rd /s /q "{APP_ROOT}"
del "%~f0"
"""
            bat_path.write_text(bat_content, encoding="utf-8")
            subprocess.Popen(
                ["cmd.exe", "/c", str(bat_path)],
                **hidden_subprocess_options(),
            )
            if self._window:
                self._window.destroy()
            return {"ok": True, "message": "AuroraChecker будет полностью удалён после закрытия."}
        except Exception as exc:
            return error(str(exc))
