from __future__ import annotations

import ctypes
import csv
from datetime import datetime, timedelta
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import shutil
import shlex
import platform
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
import ssl

try:
    ssl._create_default_https_context = ssl._create_unverified_context
except AttributeError:
    pass

import uuid
from urllib.parse import urlparse
from ctypes import wintypes
import zipfile


APP_VERSION = "1.2.4"
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
    "com/lunarclient", "com/lunar", "AnchorTweaks", "AutoDoubleHand",
    "AutoHitCrystal", "JumpReset", "LegitTotem", "ShieldBreaker", "AxeSpam",
    "WebMacro", "FastPlace", "WalskyOptimizer", "WalksyOptimizer",
    "WalksyCrystalOptimizerMod", "ShieldDisabler", "SilentAim", "Totem Hit",
    "AntiMissClick", "LagReach", "PopSwitch", "SprintReset", "ChestSteal",
    "AntiBot", "ElytraSwap", "FastXP", "FastExp", "Refill", "NoJumpDelay",
    "AirAnchor", "FakeInv", "PackSpoof", "Antiknockback", "catlean", "Argon",
    "AuthBypass", "Asteria", "Prestige", "AutoEat", "AutoMine", "MaceSwap",
    "DoubleAnchor", "AutoTPA", "Xenon", "gypsy", "AutoMace", "dontPlaceCrystal",
    "dontBreakCrystal", "canPlaceCrystalServer", "healPotSlot", "speedPotSlot",
    "strengthPotSlot", "hasGlowstone", "HasAnchor", "preventSwordBlockBreaking",
    "preventSwordBlockAttack", "swapBackToOriginalSlot", "autoCrystalPlaceClock",
    "setBlockBreakingCooldown", "getBlockBreakingCooldown", "blockBreakingCooldown",
    "onBlockBreaking", "setItemUseCooldown", "setSelectedSlot", "invokeDoAttack",
    "invokeDoItemUse", "invokeOnMouseButton", "onTickMovement", "onPushOutOfBlocks",
    "onIsGlowing", "FutureClient", "Future Client", "MeteorClient", "Meteor Client",
    "ImpactClient", "Impact Client", "WurstClient", "Wurst Client", "Phobos", "Freecam",
    "Nuker", "Chams", "Wallhack", "NoRender", "WTap", "STap", "FastBow", "Offhand",
    "Crystalaura", "Crystal Aura", "AnchorAura", "Anchor Aura", "BedAura", "Bed Aura",
    "Surround", "AutoObby", "AutoTrap", "SelfTrap", "AutoWalk", "InventoryWalk", "InvMove",
    "InvWalk", "FastFall", "Glide", "Blink", "Phase", "Clip", "VClip", "HClip", "PacketFly",
    "pfly", "BoatFly", "EntitySpeed", "Entity Speed", "ElytraFly", "Elytra Fly", "Parkour",
    "NoPush", "NoColli", "AutoTool", "Auto Tool", "InvClean", "InvCleaner", "Inventory Cleaner",
    "AutoLog", "AutoDisconnect", "FastUse", "AntiAFK", "Anti AFK", "Derp", "SpinBot", "Timer",
    "PortalGodMode", "Portal God Mode", "FakePlayer", "Fake Player", "AutoReconnect",
    "AutoRespawn", "AntiVanish", "Anti Vanish", "XCarry", "MoreInventory", "NoEntityTrace",
    "NoEntityTrees", "PacketCrasher", "ServerCrasher", "CommandSpam", "Spammer", "SignCrash",
    "BookCrash", "CoordExploit", "Coord Finder", "Nursultan", "Expensive", "ExpensiveClient",
    "Neverhook", "Celestia", "Akrien", "Excellent", "ExcellentClient", "Wexside", "Minced",
    "WildClient", "Wild Client", "Fluger", "Envy", "RiseClient", "Rise Client",
    "Elysium", "Gamble", "Phantom", "Booster", "FDPClient", "Salhack", "KamiBlue",
    "Aristois", "Pyro", "Rhack", "Gamesense", "Konas", "Seppuku", "Xulu", "Deadcode",
    "Ares", "Huzuni", "ZeroDay", "ArmorHUD", "Breadcrumbs", "Trajectories", "NoFog",
    "AntiOverlay", "AntiBlind", "AutoShield", "AntiKB", "BedAura", "ObbyBypass",
    "OffhandTotem", "AutoSneak", "AirJump", "FastLadder", "WaterSpeed", "IceSpeed",
    "SlimeJump", "AutoSell", "LootYeeter", "ItemScroller", "HWID", "AntiLeak",
    "Cracked"
}

WHITELISTED_MODS = {
    "vmp-fabric", "vmp", "lithium", "sodium", "iris", "fabric-api",
    "modmenu", "ferrite-core", "lazydfu", "starlight", "entityculling",
    "immediatelyfast",
}

BANNED_MODS = {
    "xray", "player spotlight", "auchelper", "chesttracker",
    "friend highlighter", "donut auctions", "diamondgen", "freecam",
    "basefinder", "truesight", "neat", "chunkanimator", "mobhealthbar",
    "litematica", "schematica", "block-entity-tooltip", "worldedit",
    "better pvp", "worlddownloader", "removeblindness",
    "dont heat teammates", "don't hit teammates", "cleancut",
    "autoattack", "autoaim", "autofish", "kill aura", "reach",
    "fly hacks", "auto clicker",
}

GHOST_SIGNATURES = [
    ("System Client", ("dev/mark/system", "system_client", "systemclient/module", "systemintelijready")),
    ("Wayne Client", ("ru/wayne", "selfdestructmodule", "auracombomodule", "wayne_waypoints.json")),
    ("Nursultan Client", ("net/nursultan", "nursultan/module", "nursultan/gui", "nur/client", "nursultan")),
    ("Celestial Client", ("celestial/main", "com/celestial", "celestialrecode", "celka", "celestial")),
    ("Expensive Client", ("expensive/module", "expensive/ui", "com/expensive/module", "expensive")),
    ("Excellent Client", ("excellent/client", "excellent/module", "net/excellent")),
    ("Akrien Client", ("akrien/client", "akrien/module", "net/akrien")),
    ("DeadCode Client", ("deadcode/main", "deadcode/api", "deadcode/module", "net/deadcode")),
    ("WildClient", ("wildclient/module", "wildclient/ui", "wildclient/main")),
    ("Wexside Client", ("wexside/client", "wexside/module", "wexside/ui")),
    ("Minced Client", ("minced/client", "minced/module", "net/minced")),
    ("Fluger Client", ("fluger/client", "fluger/module", "net/fluger")),
    ("NeverHook Client", ("neverhook/client", "neverhook/module", "org/neverhook")),
    ("ThunderHack", ("thunder/hack", "thunderhack/module", "thunder/gui")),
    ("Meteor Client", ("meteordevelopment/meteorclient", "meteor-client", "meteorclient/systems")),
    ("LiquidBounce", ("net/ccbluex/liquidbounce", "liquidbounce/module")),
    ("Wurst Client", ("net/wurstclient", "wurstclient/features")),
    ("Future Client", ("net/futureclient", "future/client", "future/module")),
    ("RusherHack", ("rusherhack/client", "rusherhack/module")),
    ("Baritone Pathfinder", ("baritone/api", "baritone/process", "baritone/behavior")),
    ("Vape Lite Client", ("vape lite", "vapelite", "vape_lite", "vape-lite", "vape/loader", "vape/client")),
    ("Vape V4 Client", ("vape v4", "vapev4", "vape_v4", "vape-v4", "vape.gg", "vape/loader", "vape/client", "vape")),
    ("Whiteout Ghost Client", ("whiteout/client", "whiteout_loader", "whiteout.cc", "wo_inject", "whiteout")),
    ("Entropy Ghost Client", ("entropy/client", "entropy_inject", "entropy.cc", "entropy_gui")),
    ("Drip Lite Client", ("drip/client", "drip_lite", "drip_loader", "drip.cc")),
    ("Juul Ghost Client", ("juul/client", "juul_inject", "juul.cc")),
    ("Koid Ghost Client", ("koid/client", "koid_autoclicker")),
    ("Itami Ghost Client", ("itami/client", "itami.exe")),
    ("Skilled Client", ("skilled/client", "skilled_v3")),
    ("Vec.dll / Native Hook", ("vec.dll", "gclip.dll", "hitbox.dll", "reach.dll", "velocity.dll")),
    ("DoomsDay Client", ("doomsday/", "doomsdayclient", "doomsday_client", "doomsday.vip", "doomsday.cc", "doomsday.net", "doomsday.dll", "doomsday_", "doomsday")),
    ("Liminar Injector", ("liminar_inj", "liminar.exe")),
    ("ExLoader", ("exloader.exe", "exloader/configs")),
    ("AutoClicker / Macro", ("speedautoclicker", "fastclicker", "opautoclicker", "gsautoclicker", "gclipwin64")),
    ("Slinky Client", ("slinkyclient", "slinky client", "slinky_loader", "slinky")),
    ("Sunset Client", ("sunsetclient", "sunset client", "sunset-loader", "sunset.dll")),
    ("Karma Client", ("karmaclient", "karma client", "karma.dll")),
    ("Zamorozka Client", ("zamorozka/client", "zamorozkaclient")),
    ("Sunrise Client", ("sunrise/client", "sunriseclient")),
    ("Hono Client", ("hono/client", "honoclient")),
    ("Extazyy Client", ("extazyy/client", "extazyyclient")),
    ("Ricardo Client", ("ricardo/client", "ricardoclient")),
    ("Nightware Client", ("nightware/client", "nightwareclient")),
    ("FDPClient", ("fdpclient/module", "fdpclient")),
    ("Augustus Client", ("augustus/client", "augustusclient")),
    ("Novoline Client", ("novoline/client", "novolineclient")),
    ("Tenacity Client", ("tenacity/client", "tenacityclient")),
    ("Astolfo Client", ("astolfo/client", "astolfoclient")),
    ("Rise Client", ("rise/client", "riseclient")),
    ("Lambda Client", ("lambda/client", "lambdaclient")),
    ("Earthhack", ("earthhack/client", "earthhack_client")),
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
        "name": "ExecutedProgramsList",
        "process": ("executedprogramslist.exe",),
        "exe": ("executedprogramslist.exe",),
        "keywords": ("executedprogramslist", "executed programs list"),
        "download_url": "https://www.nirsoft.net/utils/executedprogramslist.zip",
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
    {
        "name": "AnyDesk",
        "process": ("anydesk.exe",),
        "exe": ("anydesk.exe", "AnyDesk.exe"),
        "keywords": ("anydesk", "any desk", "any-desk"),
        "download_url": "https://download.anydesk.com/AnyDesk.exe",
        "download_type": "file",
    },
    {
        "name": "RuDesk",
        "process": ("rudesk.exe", "rudesktop.exe", "rudesktop-2.9.1069-x64.msi"),
        "exe": ("rudesk.exe", "rudesktop.exe", "rudesktop-2.9.1069-x64.msi"),
        "keywords": ("rudesk", "ru desk", "ru-desk", "rudesktop"),
        "download_url": "https://storage.rudesktop.ru/download/rudesktop-2.9.1069-x64.msi",
        "download_type": "file",
    },
    {
        "name": "RustDesk",
        "process": ("rustdesk.exe",),
        "exe": ("rustdesk.exe", "rustdesk-1.4.9-x86_64.exe"),
        "keywords": ("rustdesk", "rust desk", "rust-desk"),
        "download_url": "https://github.com/rustdesk/rustdesk/releases/download/1.4.9/rustdesk-1.4.9-x86_64.exe",
        "download_type": "file",
    },
]

BETA_TOOL_NAMES = {
    "Everything",
    "ShellBag Analyzer",
    "Journal Trace",
}

OTHER_TOOL_NAMES = {
    "BAM Parser",
    "InjGen",
    "WarpVersionChecker",
    "Java",
    "AnyDesk",
    "RuDesk",
    "RustDesk",
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
    "storage.rudesktop.ru",
    "download.anydesk.com",
    "www.softportal.com",
    "softportal.com",
}

KNOWN_BENIGN_NATIVE_NAMES = (
    "jna",
    "libopus4j",
    "librnnoise4j",
    "libspeex4j",
    "liblame4j",
    "discordhook",
    "discord_hook",
    "discord_game_sdk",
    "discord-rpc",
    "lwjgl",
    "openal",
    "glfw",
    "jemalloc",
    "tinyfd",
    "renderdoc",
    "com_mojang",
    "awt",
    "java",
    "jli",
    "jvm",
    "jimage",
    "jsvml",
    "sunmscapi",
    "extnet",
    "net",
    "zip",
    "nio",
    "management",
    "instrument",
    "sunec",
    "attach",
    "verify",
    "freetype",
    "vulkan",
    "msvcp",
    "vcruntime",
    "tlauncher",
    "feather",
    "lunar",
    "optifine",
    "authlib",
)

KNOWN_BENIGN_NATIVE_PATHS = (
    "\\appdata\\local\\discord\\",
    "\\appdata\\local\\temp\\",
    "\\.minecraft\\",
    "\\.lunarclient\\",
    "\\.feather\\",
    "\\prismlauncher\\",
    "\\curseforge\\",
    "\\modrinth\\",
    "\\.tlauncher\\",
    "\\mojang_jre\\",
    "\\java-runtime\\",
    "\\java\\",
    "\\jre\\",
    "\\jdk\\",
)

GENERIC_AGENT_MEMORY_MARKERS = ()

KNOWN_MEMORY_MARKERS = tuple(
    token.lower()
    for display, tokens in GHOST_SIGNATURES
    if display not in ("Lunar Client", "InjGen")
    for token in tokens
    if len(token) >= 5 and token.lower() not in ("injgen", "injectgen", "javalauncher.log", "com/lunarclient", "com/lunar")
)

PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_VM_READ = 0x0010
MEM_COMMIT = 0x1000
MEM_PRIVATE = 0x20000
PAGE_NOACCESS = 0x01
PAGE_GUARD = 0x100
READABLE_PROTECTIONS = {0x02, 0x04, 0x08, 0x20, 0x40, 0x80}
EXECUTABLE_PROTECTIONS = {0x10, 0x20, 0x40, 0x80}
MEMORY_CHUNK_SIZE = 1024 * 1024
MAX_MEMORY_SCAN_BYTES = 256 * 1024 * 1024
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


def is_banned_mod(name: str) -> bool:
    lower = name.lower().replace(".jar", "").replace(" ", "")
    direct = {b.replace(" ", "") for b in BANNED_MODS}
    return lower in direct or any(b in lower for b in BANNED_MODS)


def result_item(name: str, path: str, size: int, modrinth: bool, suspicious: bool, source: str | None, logs: list[dict]) -> dict:
    banned = is_banned_mod(name)
    return {
        "name": name,
        "path": path,
        "sizeBytes": size,
        "size": format_bytes(size),
        "modrinthFound": modrinth,
        "suspicious": suspicious or banned,
        "banned": banned,
        "source": "Trusted" if modrinth else (source or "Local file"),
        "verdict": "Banned" if banned else ("Risk" if suspicious else "Clean"),
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


def calculate_entropy(data: bytes) -> float:
    if not data:
        return 0.0
    frequencies = [0] * 256
    for byte in data:
        frequencies[byte] += 1
    
    entropy = 0.0
    length = len(data)
    for count in frequencies:
        if count > 0:
            p = count / length
            entropy -= p * math.log2(p)
    return entropy


def parse_constant_pool_strings(data: bytes) -> list[str]:
    strings = []
    try:
        if len(data) < 10 or data[:4] != b'\xca\xfe\xba\xbe':
            return []
        constant_pool_count = int.from_bytes(data[8:10], "big")
        offset = 10
        i = 1
        while i < constant_pool_count:
            if offset >= len(data):
                break
            tag = data[offset]
            if tag == 1: # CONSTANT_Utf8
                if offset + 3 > len(data):
                    break
                length = int.from_bytes(data[offset+1:offset+3], "big")
                if offset + 3 + length > len(data):
                    break
                val = data[offset+3:offset+3+length].decode("utf-8", errors="ignore")
                strings.append(val)
                offset += 3 + length
            elif tag in (3, 4, 9, 10, 11, 12, 18): # Integer, Float, Fieldref, Methodref, InterfaceMethodref, NameAndType, InvokeDynamic
                offset += 5
            elif tag in (5, 6): # Long, Double
                offset += 9
                i += 1
            elif tag in (7, 8, 16, 19, 20): # Class, String, MethodType, Module, Package
                offset += 3
            elif tag == 15: # MethodHandle
                offset += 4
            else:
                break
            i += 1
    except Exception:
        pass
    return strings


def analyze_jar_entropy_and_bytecode(path: Path) -> list[dict]:
    logs = []
    try:
        with zipfile.ZipFile(path, 'r') as zf:
            for info in zf.infolist():
                if info.is_dir():
                    continue
                name = info.filename
                if name.endswith(".class"):
                    class_bytes = zf.read(info)
                    
                    # 1. Entropy Scan
                    entropy = calculate_entropy(class_bytes)
                    if len(class_bytes) > 2048 and entropy > 6.9:
                        logs.append(entry(name, "Obfuscation", f"High file entropy: {entropy:.2f} (possible encryption/packing)"))
                        
                    # 2. Constant Pool Bytecode Analysis
                    pool_strings = parse_constant_pool_strings(class_bytes)
                    has_class_loader = any("java/lang/ClassLoader" in s for s in pool_strings)
                    has_define_class = any("defineClass" in s for s in pool_strings)
                    if has_class_loader and has_define_class:
                        logs.append(entry(name, "ClassLoader Hijack", "Class dynamically loads bytecode (ClassLoader.defineClass)"))
                    if any("sun/misc/Unsafe" in s for s in pool_strings):
                        logs.append(entry(name, "Unsafe Usage", "Direct memory access reference (sun/misc/Unsafe)"))
    except Exception:
        pass
    return logs


def check_dns_cache() -> list[dict]:
    logs = []
    if os.name != "nt":
        return logs
    try:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = 0
        proc = subprocess.run(
            ["ipconfig.exe", "/displaydns"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            timeout=5,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            startupinfo=startupinfo,
        )
        output = proc.stdout or ""
        
        domains = set()
        for line in output.splitlines():
            if "Record Name" in line or "Имя записи" in line:
                parts = line.split(":")
                if len(parts) >= 2:
                    domain = parts[1].strip().lower()
                    if domain:
                        domains.add(domain)
                        
        cheat_domains = {
            "doomsdayclient.com", "prestigeclient.vip", "dqrkis.xyz", "sunsetclient.com",
            "karmaclient.co", "slinkyclient.com", "vape.gg", "intent.store", "neverlose.cc",
            "liquidbounce.net", "wurstclient.net"
        }
        
        for domain in domains:
            for cheat in cheat_domains:
                if cheat in domain:
                    logs.append(entry("DNS Cache", "Network Signature", f"Cheat domain found in DNS cache: {domain}"))
    except Exception:
        pass
    return logs


def check_drivers() -> list[dict]:
    logs = []
    if os.name != "nt":
        return logs
    try:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = 0
        proc = subprocess.run(
            ["sc.exe", "query", "type=", "driver"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            timeout=5,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            startupinfo=startupinfo
        )
        output = proc.stdout or ""
        
        suspicious_drivers = ["kprocesshacker", "kph2", "dbk64", "dbk32", "cheatengine"]
        for line in output.splitlines():
            if "SERVICE_NAME" in line or "DISPLAY_NAME" in line:
                lower = line.lower()
                for driver in suspicious_drivers:
                    if driver in lower:
                        logs.append(entry("System Drivers", "Security Bypass", f"Suspicious kernel driver active: {driver}"))
    except Exception:
        pass
    return logs


def heuristic_results(path: Path) -> list[dict]:
    logs = []
    # 1. Run original scanning method (process_jar_bytes)
    try:
        logs.extend(process_jar_bytes(path.read_bytes(), "", True))
    except Exception:
        pass

    # 2. Run jarka_scanner method
    try:
        from jarka_scanner.scanner import scan_jar
        results = scan_jar(str(path), path.stat().st_size if path.exists() else 0)
        if not results.get('error'):
            # telegram
            if results.get('telegram_token'):
                logs.append(entry("Telegram Stealer", "CRITICAL", "Telegram bot token found in class strings"))
            # discord
            if results.get('discord_webhook'):
                logs.append(entry("Discord Stealer", "CRITICAL", "Discord webhook URL found in class strings"))
            # password logger
            if results.get('password_logger'):
                logs.append(entry("Password Logger", "CRITICAL", "Suspicious authentication / password logger strings found"))
            # cheats
            cheats = results.get('cheats', {})
            for name, detected in cheats.items():
                if detected:
                    logs.append(entry("Cheat Pattern", "Cheat String", f"Detected cheat/hack keyword: {name}"))
            # evidence
            for item in results.get('evidence', []):
                filename = item.get('file', '')
                matched = item.get('matched', '')
                logs.append(entry(filename, "Detection", f"Matched signature: {matched}"))
            # suspicious urls
            urls = results.get('suspicious_urls', [])
            for url in urls:
                logs.append(entry("Suspicious Connection", "Dangerous Behavior", f"Suspicious URL found: {url}"))
    except Exception:
        pass

    # 3. Run new Entropy Scan & Constant Pool Bytecode Analysis
    try:
        logs.extend(analyze_jar_entropy_and_bytecode(path))
    except Exception:
        pass
        
    return logs


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
        "detection",
    }
    return any((item.get("type") or "").lower() in risky for item in entries)


CANCEL_SCAN_REQUESTED = False


def cancel_scan() -> dict:
    global CANCEL_SCAN_REQUESTED
    CANCEL_SCAN_REQUESTED = True
    return {"ok": True}


SCAN_PROGRESS = {"current": 0, "total": 0, "status": "", "percent": 0, "detail": ""}


def get_scan_progress() -> dict:
    global SCAN_PROGRESS
    return SCAN_PROGRESS


def update_scan_progress(current: int, total: int, status: str, detail: str = "") -> None:
    global SCAN_PROGRESS
    pct = int((current / total) * 100) if total > 0 else 100
    SCAN_PROGRESS = {
        "current": current,
        "total": total,
        "status": status,
        "detail": detail or f"checking {status}",
        "percent": min(100, max(0, pct))
    }


def reset_cancel_scan() -> dict:
    global CANCEL_SCAN_REQUESTED
    global SCAN_PROGRESS
    CANCEL_SCAN_REQUESTED = False
    SCAN_PROGRESS = {"current": 0, "total": 0, "status": "", "percent": 0, "detail": ""}
    return {"ok": True}


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
    total_jars = len(jars)
    if not jars:
        update_scan_progress(0, 0, "Done")
        return {
            "ok": True,
            "target": str(path.resolve()),
            "items": [],
            "stats": {"items": 0, "risks": 0, "trusted": 0, "clean": 0, "banned": 0},
        }

    items = []
    for idx, jar in enumerate(jars):
        if CANCEL_SCAN_REQUESTED:
            break
        update_scan_progress(idx + 1, total_jars, jar.name, f"parsing bytecode & signatures: {jar.name}")
        modrinth = check_modrinth(jar)
        logs = [] if modrinth else heuristic_results(jar)
        
        jarka_ev = []
        try:
            from jarka_scanner.scanner import scan_jar
            jres = scan_jar(str(jar), jar.stat().st_size if jar.exists() else 0)
            if jres and isinstance(jres, dict):
                ev_list = jres.get("evidence", [])
                for ev in ev_list:
                    jarka_ev.append({
                        "type": ev.get("rule", "Jarka Detection"),
                        "message": ev.get("description", str(ev)),
                        "confidence": "high" if ev.get("severity") == "high" else "medium"
                    })
        except Exception:
            pass

        all_logs = logs + jarka_ev
        items.append(result_item(
            jar.name,
            str(jar.resolve()),
            jar.stat().st_size if jar.exists() else 0,
            modrinth,
            (not modrinth) and high_confidence(all_logs),
            download_source(jar),
            all_logs,
        ))
    update_scan_progress(total_jars, total_jars, "Completed")
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
    modules = loaded_modules(pid)
    logs.extend(process_module_entries(modules, seen))
    for module in modules:
        check_ghost_text(module, "Loaded module", logs, seen)
    logs.extend(memory_scan_entries(pid, seen))
    if not logs:
        return None

    # Simplify process representation details
    cmd_line = command or process.get('command', '')
    desc = "Minecraft Java Process"
    if "fabric-loader" in cmd_line: desc = "Fabric Minecraft"
    elif "forge" in cmd_line: desc = "Forge Minecraft"
    elif "quilt-loader" in cmd_line: desc = "Quilt Minecraft"
    elif "lunar" in cmd_line: desc = "Lunar Client"
    elif "feather" in cmd_line: desc = "Feather Client"
    
    version_match = re.search(r'--version\s+([^\s]+)', cmd_line)
    version = f" ({version_match.group(1)})" if version_match else ""

    return result_item(
        f"Minecraft (PID {pid})",
        f"{desc}{version}",
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
                        if CANCEL_SCAN_REQUESTED:
                            return logs
                        chunk_size = min(MEMORY_CHUNK_SIZE, region_size - offset, MAX_MEMORY_SCAN_BYTES - scanned)
                        data = read_memory_chunk(read_process_memory, handle, base + offset, chunk_size)
                        scanned += chunk_size
                        update_scan_progress(scanned, MAX_MEMORY_SCAN_BYTES, f"RAM Scan (PID {pid})", f"analyzing RAM memory: {scanned // (1024 * 1024)}MB / {MAX_MEMORY_SCAN_BYTES // (1024 * 1024)}MB")
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


JVM_MODIFICATION_DWORDS = {0xFCE01E99}

def get_memory_protection_desc(protect: int) -> str:
    mapping = {
        0x01: "NOACCESS",
        0x02: "READONLY",
        0x04: "READWRITE",
        0x08: "WRITECOPY",
        0x10: "EXECUTE",
        0x20: "EXECUTE_READ",
        0x40: "EXECUTE_READWRITE",
        0x80: "EXECUTE_WRITECOPY",
    }
    desc = mapping.get(protect & 0xFF, "UNKNOWN")
    if protect & 0x100: desc += "+GUARD"
    if protect & 0x200: desc += "+NOCACHE"
    if protect & 0x400: desc += "+WRITECOMBINE"
    return desc

def get_memory_type_desc(mem_type: int) -> str:
    if mem_type == 0x20000: return "Private Heap/Stack"
    if mem_type == 0x1000000: return "Image (DLL/EXE)"
    if mem_type == 0x40000: return "Mapped File"
    return f"Type 0x{mem_type:X}"

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

        check_jvm_modification_dwords(data, address, protect, region_type, logs, seen)


def check_jvm_modification_dwords(data: bytes, address: int, protect: int, region_type: int, logs: list[dict], seen: set[str]) -> None:
    if len(logs) >= MAX_MEMORY_FINDINGS:
        return
    for i in range(0, len(data) - 3, 4):
        dword = int.from_bytes(data[i:i+4], "little")
        if dword in JVM_MODIFICATION_DWORDS:
            prot_desc = get_memory_protection_desc(protect)
            type_desc = get_memory_type_desc(region_type)
            add_unique_entry(
                logs,
                seen,
                "Process memory",
                "JVM Modification",
                f"InjGen JVM bytecode modification marker at 0x{address + i:X} [{type_desc}, {prot_desc}]",
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
    update_scan_progress(1, 100, "Detecting Java processes...", "searching for active Minecraft / Java processes")
    if pid is None:
        processes = minecraft_like_processes()
        target = "Process scan"
    else:
        processes = [find_process(pid)]
        target = f"Process scan: PID {pid}"
        
    update_scan_progress(5, 100, "Scanning process runtime...", f"found {len(processes)} process(es)")
    findings = []
    for process in processes:
        if CANCEL_SCAN_REQUESTED:
            break
        item = scan_ghost_process(process)
        if item:
            findings.append(item)

    if CANCEL_SCAN_REQUESTED:
        update_scan_progress(100, 100, "Cancelled", "scan stopped by user")
        return error("Scan cancelled by user")
        
    update_scan_progress(85, 100, "Checking DNS Cache & active system drivers...", "running kernel driver & DNS verification")
    dns_logs = check_dns_cache()
    driver_logs = check_drivers()
    combined_system_logs = dns_logs + driver_logs
    if combined_system_logs:
        findings.append(result_item(
            "System Forensics",
            target,
            0,
            False,
            True,
            "Process",
            combined_system_logs
        ))
        
    update_scan_progress(100, 100, "Done", "process scan complete")
    if not processes and not combined_system_logs:
        return ok(target, [summary("No Minecraft-like Java processes found.", target)])
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


def download_via_softportal(name: str, temp_path: Path, progress=None) -> bool:
    """Attempts to search for the tool on SoftPortal and download it."""
    import http.cookiejar
    import urllib.parse
    import urllib.request
    import re

    try:
        ssl_ctx = ssl.create_default_context()
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_NONE
        cj = http.cookiejar.CookieJar()
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj), urllib.request.ProxyHandler({}), urllib.request.HTTPSHandler(context=ssl_ctx))
        opener.addheaders = [('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')]

        # Step 1: Search SoftPortal
        search_query = urllib.parse.quote(name)
        search_url = f"https://www.softportal.com/search.html?str={search_query}&go=1"
        req = urllib.request.Request(search_url)
        with opener.open(req, timeout=30) as resp:
            html = resp.read().decode('cp1251', errors='ignore')

        # Find software page links like software-XXXX-YYYY.html
        links = re.findall(r'href=\x22(https://www.softportal.com/software-\d+-[^\x22]+)\x22', html)
        if not links:
            links = re.findall(r'href=\x22(https://www.softportal.com/software-\d+-[a-zA-Z0-9_-]+)\x22', html)
            if not links:
                return False

        soft_url = links[0]

        # Step 2: Load software main page (initializes session/cookies)
        req_soft = urllib.request.Request(soft_url)
        with opener.open(req_soft, timeout=30) as resp_soft:
            resp_soft.read()

        # Step 3: Load the intermediate "/get-" page
        get_url = soft_url.replace('/software-', '/get-')
        req_get = urllib.request.Request(get_url, headers={'Referer': soft_url})
        with opener.open(req_get, timeout=30) as resp_get:
            get_html = resp_get.read().decode('cp1251', errors='ignore')

        # Find direct mirror links like getsoft-XXXX-YYYY-Z.html
        dl_links = re.findall(r'href=\x22(https://www.softportal.com/getsoft-\d+-[^\x22]+)\x22', get_html)
        if not dl_links:
            return False

        dl_url = dl_links[0]

        # Step 4: Download the actual file from getsoft link with Referer set to get_url
        req_dl = urllib.request.Request(dl_url, headers={'Referer': get_url})
        with opener.open(req_dl, timeout=45) as response:
            final_host = urlparse(response.geturl()).netloc.lower()
            if final_host not in ALLOWED_DOWNLOAD_HOSTS:
                raise RuntimeError(f"Redirected to non-official host: {final_host}")
            
            total = int(response.headers.get("Content-Length", "0") or 0)
            received = 0
            if progress:
                progress(0, total)
            with temp_path.open("wb") as out:
                while True:
                    chunk = response.read(1024 * 256)
                    if not chunk:
                        break
                    out.write(chunk)
                    received += len(chunk)
                    if progress:
                        progress(received, total)
        return True
    except Exception:
        return False


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
            try:
                download_file(str(url), temp_path, progress)
            except Exception as primary_exc:
                # Fallback to SoftPortal
                if not download_via_softportal(signature["name"], temp_path, progress):
                    raise primary_exc

            if signature.get("download_type") == "zip" or temp_path.suffix.lower() == ".zip" or zipfile.is_zipfile(temp_path):
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
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE
    request = urllib.request.Request(url, headers={"User-Agent": f"AuroraChecker/{APP_VERSION}"})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), urllib.request.HTTPSHandler(context=ssl_ctx))
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
    try:
        source.replace(destination)
    except OSError:
        import shutil
        shutil.move(str(source), str(destination))


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
        return p.exists() and p.is_file() and p.suffix.lower() in (".exe", ".lnk", ".bat", ".cmd", ".msi")
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
            "banned": sum(1 for item in items if item.get("banned")),
            "trusted": sum(1 for item in items if item.get("modrinthFound")),
            "clean": sum(1 for item in items if not item.get("suspicious") and not item.get("banned")),
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


def _activity_line(date: str, action: str, name: str, path: str = "", size: str = "-") -> dict:
    if size == "-" and path and os.path.exists(path):
        try:
            sz = os.path.getsize(path)
            if sz < 1024:
                size = f"{sz} B"
            elif sz < 1024 * 1024:
                size = f"{sz / 1024:.1f} KB"
            else:
                size = f"{sz / (1024 * 1024):.1f} MB"
        except Exception:
            pass
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
        "size": size,
        "source": "Journal",
        "verdict": "Risk" if risk else "Info",
        "suspicious": risk,
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
        is_wiped = bool(mask & 0x00000008) or bool(mask & 0x00000002)
        if mask & 0x00000200:
            status = "wiped / self-destruct" if is_wiped else action
            display_name = f"[SELF-DESTRUCT WIPING] {fname}" if is_wiped else fname
            e = _activity_line(ts, status, display_name, "")
            deleted_rows.append(e)
        else:
            e = _activity_line(ts, action, fname, "")
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


def _scan_muicache(max_rows: int = 100) -> list[dict]:
    """Scans Windows MuiCache in registry for executed application paths and titles (HolyCheck method)."""
    if os.name != "nt":
        return []
    import winreg
    rows = []
    mui_keys = [
        (winreg.HKEY_CURRENT_USER, r"Software\Classes\Local Settings\Software\Microsoft\Windows\Shell\MuiCache"),
        (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\ShellNoRoam\MUICache"),
    ]
    seen = set()
    for root_hkey, sub_key in mui_keys:
        try:
            key = winreg.OpenKey(root_hkey, sub_key)
            val_count = winreg.QueryInfoKey(key)[1]
            for i in range(val_count):
                try:
                    val_name, val_data, _ = winreg.EnumValue(key, i)
                    if not val_name or not isinstance(val_name, str):
                        continue
                    clean_path = val_name.rsplit(".", 1)[0] if val_name.endswith((".FriendlyName", ".ApplicationCompany")) else val_name
                    if not clean_path.lower().endswith((".exe", ".jar")):
                        continue
                    if clean_path.lower() in seen:
                        continue
                    seen.add(clean_path.lower())

                    title = str(val_data) if isinstance(val_data, str) else os.path.basename(clean_path)
                    is_deleted = not os.path.exists(clean_path)
                    status = "deleted" if is_deleted else "active"
                    
                    path_low = clean_path.lower()
                    is_suspicious = any(p in path_low for p in ["temp", "downloads", "appdata\\local\\temp", "desktop"]) or (len(clean_path) > 2 and clean_path[1:3] == ":\\" and clean_path[0].lower() not in ["c", "d"])
                    
                    rows.append(_activity_line(
                        "-",
                        "risk" if is_suspicious else status,
                        f"MuiCache: {title} ({os.path.basename(clean_path)})",
                        clean_path
                    ))
                except Exception:
                    continue
            key.Close()
        except Exception:
            pass
    return rows[:max_rows]


def _scan_event_logs(max_rows: int = 50) -> list[dict]:
    """Fast native scan of Windows Event Logs for Log Clearing (104, 1102) and Driver Installation (7045)."""
    if os.name != "nt":
        return []
    import xml.etree.ElementTree as ET
    rows = []

    def parse_iso_time(ts_str: str) -> str:
        if not ts_str: return "-"
        try:
            dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            return dt.strftime("%d.%m.%Y %H:%M:%S")
        except Exception:
            return ts_str[:19].replace("T", " ")

    # 1. System log query (104 = Log Cleared, 7045 = New Service/Driver)
    cmd_sys = ["wevtutil.exe", "qe", "System", "/q:*[System[(EventID=104 or EventID=7045)]]", "/f:RenderedXml", f"/c:{max_rows}", "/rd:true"]
    try:
        proc = subprocess.run(cmd_sys, capture_output=True, text=True, errors="ignore", **hidden_subprocess_options())
        out = proc.stdout or ""
        if "<Event" in out:
            root = ET.fromstring("<Events>" + out + "</Events>")
            for ev in root.findall("{http://schemas.microsoft.com/win/2004/08/events/event}Event"):
                sys_elem = ev.find("{http://schemas.microsoft.com/win/2004/08/events/event}System")
                if sys_elem is not None:
                    eid_elem = sys_elem.find("{http://schemas.microsoft.com/win/2004/08/events/event}EventID")
                    eid = eid_elem.text if eid_elem is not None else ""
                    tc_elem = sys_elem.find("{http://schemas.microsoft.com/win/2004/08/events/event}TimeCreated")
                    ts = tc_elem.attrib.get("SystemTime", "") if tc_elem is not None else ""
                    t_str = parse_iso_time(ts)
                    if eid == "104":
                        rows.append(_activity_line(t_str, "[LOG CLEARING DETECTED]", "System Event Log Cleared (Event 104)", "System EventLog"))
                    elif eid == "7045":
                        rows.append(_activity_line(t_str, "[SERVICE INSTALLED]", "New Service/Kernel Driver Installed (Event 7045)", "System Service"))
    except Exception:
        pass

    # 2. Security log query (1102 = Audit Log Cleared)
    cmd_sec = ["wevtutil.exe", "qe", "Security", "/q:*[System[(EventID=1102)]]", "/f:RenderedXml", f"/c:{max_rows}", "/rd:true"]
    try:
        proc = subprocess.run(cmd_sec, capture_output=True, text=True, errors="ignore", **hidden_subprocess_options())
        out = proc.stdout or ""
        if "<Event" in out:
            root = ET.fromstring("<Events>" + out + "</Events>")
            for ev in root.findall("{http://schemas.microsoft.com/win/2004/08/events/event}Event"):
                sys_elem = ev.find("{http://schemas.microsoft.com/win/2004/08/events/event}System")
                if sys_elem is not None:
                    eid_elem = sys_elem.find("{http://schemas.microsoft.com/win/2004/08/events/event}EventID")
                    eid = eid_elem.text if eid_elem is not None else ""
                    tc_elem = sys_elem.find("{http://schemas.microsoft.com/win/2004/08/events/event}TimeCreated")
                    ts = tc_elem.attrib.get("SystemTime", "") if tc_elem is not None else ""
                    t_str = parse_iso_time(ts)
                    if eid == "1102":
                        rows.append(_activity_line(t_str, "[LOG CLEARING DETECTED]", "Security Audit Log Cleared (Event 1102)", "Security EventLog"))
    except Exception:
        pass

    return rows


def _scan_userassist(max_rows: int = 100) -> list[dict]:
    """Decodes HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\UserAssist entries."""
    if os.name != "nt":
        return []
    import winreg
    rows = []
    base_key = r"Software\Microsoft\Windows\CurrentVersion\Explorer\UserAssist"
    trans = str.maketrans(
        "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
        "NOPQRSTUVWXYZABCDEFGHIJKLMnopqrstuvwxyzabcdefghijklm"
    )
    try:
        ua_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, base_key)
        count = winreg.QueryInfoKey(ua_key)[0]
        for i in range(count):
            sub_name = winreg.EnumKey(ua_key, i)
            try:
                sub_key = winreg.OpenKey(ua_key, sub_name + r"\Count")
                val_count = winreg.QueryInfoKey(sub_key)[1]
                for j in range(val_count):
                    try:
                        val_name, val_data, _ = winreg.EnumValue(sub_key, j)
                        decoded_path = val_name.translate(trans)
                        if not decoded_path.lower().endswith((".exe", ".jar", ".bat", ".cmd", ".vbs")):
                            continue
                        
                        run_count = 0
                        date_str = "-"
                        if isinstance(val_data, bytes) and len(val_data) >= 68:
                            run_count = int.from_bytes(val_data[4:8], "little")
                            ft_val = int.from_bytes(val_data[60:68], "little")
                            if ft_val > 0:
                                try:
                                    ft_s = datetime(1601, 1, 1) + timedelta(microseconds=ft_val // 10)
                                    date_str = ft_s.strftime("%Y-%m-%d %H:%M:%S")
                                except Exception:
                                    pass
                        
                        is_deleted = not os.path.exists(decoded_path)
                        path_low = decoded_path.lower()
                        is_suspicious = any(p in path_low for p in ["temp", "downloads", "appdata\\local\\temp", "desktop"]) or (len(decoded_path) > 2 and decoded_path[1:3] == ":\\" and decoded_path[0].lower() not in ["c", "d"])
                        
                        status = "deleted" if is_deleted else ("risk" if is_suspicious else "active")
                        label = f"{os.path.basename(decoded_path)} (runs: {run_count})"
                        rows.append(_activity_line(
                            date_str,
                            status,
                            label,
                            decoded_path
                        ))
                    except Exception:
                        continue
                sub_key.Close()
            except Exception:
                continue
        ua_key.Close()
    except Exception:
        pass
    return rows[:max_rows]


def _scan_prefetch(max_rows: int = 50) -> list[dict]:
    """Scans Prefetch directory for recently run executables."""
    prefetch_dir = r"C:\Windows\Prefetch"
    if not os.path.exists(prefetch_dir):
        return []
    rows = []
    try:
        entries = sorted(
            [os.path.join(prefetch_dir, f) for f in os.listdir(prefetch_dir) if f.lower().endswith(".pf")],
            key=lambda x: os.path.getmtime(x),
            reverse=True
        )
        for pf in entries[:max_rows]:
            mtime = datetime.fromtimestamp(os.path.getmtime(pf)).strftime("%Y-%m-%d %H:%M:%S")
            exe_name = os.path.basename(pf).split("-")[0] + ".exe"
            rows.append(_activity_line(mtime, "prefetch", exe_name, pf))
    except Exception:
        pass
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
    update_scan_progress(10, 100, "Scanning User Directories", "scanning user folders for JAR and DLL files...")
    jar_user = _scan_user_files(".jar")
    dll_user = _scan_user_files(".dll")
    user_fnames: set[str] = set()
    for r in jar_user + dll_user:
        n = r.get("name", "")
        if n:
            user_fnames.add(n.lower())
    update_scan_progress(35, 100, "Scanning USN Journal", "reading USN Change Journal records...")
    jar_activity, jar_deleted, jar_note = _scan_usn(".jar", user_fnames)
    dll_activity, dll_deleted, dll_note = _scan_usn(".dll", user_fnames)
    update_scan_progress(60, 100, "Scanning BAM & Registry Forensics", "analyzing BAM, UserAssist ROT13 & MuiCache...")
    jar_bam = _scan_bam_deleted(".jar")
    dll_bam = _scan_bam_deleted(".dll")
    exe_bam = _scan_bam_deleted(".exe")
    userassist_rows = _scan_userassist()
    prefetch_rows = _scan_prefetch()
    mui_rows = _scan_muicache()
    update_scan_progress(85, 100, "Analyzing EventLogs & Shortcut Activity", "checking EventLog history & LNK files...")
    event_rows = _scan_event_logs()
    jar_lnk_del = _scan_lnk_deleted(".jar")
    dll_lnk_del = _scan_lnk_deleted(".dll")
    update_scan_progress(100, 100, "Done", "activity scan complete")
    deleted_rows = jar_deleted + dll_deleted + jar_bam + dll_bam + exe_bam + jar_lnk_del + dll_lnk_del + userassist_rows + mui_rows + event_rows
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


def _service_status(srv_name: str) -> str:
    try:
        proc = subprocess.run(['sc.exe', 'query', srv_name], capture_output=True, text=True, errors='ignore', **hidden_subprocess_options())
        out = proc.stdout or ''
        if 'RUNNING' in out: return 'Running'
        if 'STOPPED' in out: return 'Stopped'
        return 'Not Found'
    except Exception:
        return 'Unknown'

def get_system_info_summary() -> dict:
    class SHQUERYRBINFO(ctypes.Structure):
        _fields_ = [('cbSize', wintypes.DWORD), ('i64Size', ctypes.c_int64), ('i64NumItems', ctypes.c_int64)]

    rb_info = SHQUERYRBINFO()
    rb_info.cbSize = ctypes.sizeof(SHQUERYRBINFO)
    res = ctypes.windll.shell32.SHQueryRecycleBinW(None, ctypes.byref(rb_info))
    num_items = rb_info.i64NumItems if res == 0 else 0
    size_bytes = rb_info.i64Size if res == 0 else 0
    size_formatted = format_bytes(size_bytes)

    latest_del_date = "Корзина пуста" if num_items == 0 else "Неизвестно"
    if num_items > 0:
        try:
            import win32com.client
            sh = win32com.client.Dispatch('Shell.Application')
            rb = sh.Namespace(10)
            items = rb.Items()
            dates = []
            for i in range(min(items.Count, 100)):
                it = items.Item(i)
                d = rb.GetDetailsOf(it, 2).replace('\u200e', '').replace('\u200f', '').strip()
                if d:
                    dates.append(d)
            if dates:
                latest_del_date = dates[0]
        except Exception:
            pass

    uptime_ms = ctypes.windll.kernel32.GetTickCount64()
    uptime_sec = int(uptime_ms / 1000)
    days = uptime_sec // 86400
    hours = (uptime_sec % 86400) // 3600
    minutes = (uptime_sec % 3600) // 60
    boot_dt = datetime.now() - timedelta(seconds=uptime_sec)

    usbs_count = 0
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'SYSTEM\CurrentControlSet\Enum\USBSTOR')
        usbs_count = winreg.QueryInfoKey(key)[0]
    except Exception:
        pass

    def _service_status(srv_name: str) -> str:
        try:
            proc = subprocess.run(['sc.exe', 'query', srv_name], capture_output=True, text=True, errors='ignore', **hidden_subprocess_options())
            out = proc.stdout or ''
            if 'RUNNING' in out: return 'Running'
            if 'STOPPED' in out: return 'Stopped'
            return 'Not Found'
        except Exception:
            return 'Unknown'

    # Temp Folder Analysis
    temp_path = Path(os.environ.get("TEMP", r"C:\Users\Admin\AppData\Local\Temp"))
    temp_files_count = 0
    temp_total_bytes = 0
    valid_mtimes = []
    if temp_path.exists():
        try:
            for root, dirs, filenames in os.walk(temp_path):
                for f in filenames:
                    fp = os.path.join(root, f)
                    try:
                        st = os.stat(fp)
                        if st.st_mtime > 946684800:
                            valid_mtimes.append(st.st_mtime)
                            temp_total_bytes += st.st_size
                    except Exception:
                        pass
        except Exception:
            pass

    valid_mtimes.sort()
    oldest_ts = valid_mtimes[0] if valid_mtimes else None
    newest_ts = valid_mtimes[-1] if valid_mtimes else None
    oldest_str = datetime.fromtimestamp(oldest_ts).strftime("%d.%m.%Y %H:%M:%S") if oldest_ts else "Неизвестно"
    newest_str = datetime.fromtimestamp(newest_ts).strftime("%d.%m.%Y %H:%M:%S") if newest_ts else "Неизвестно"
    now_ts = time.time()
    diff_hours = (now_ts - oldest_ts) / 3600 if oldest_ts else 999

    if len(valid_mtimes) < 50 or diff_hours < 2:
        temp_status = "Очищалась недавно (менее 2 часов назад)"
    elif diff_hours < 24:
        temp_status = f"Очищалась сегодня ({oldest_str})"
    else:
        temp_status = f"Старые файлы от {oldest_str} (не очищалась)"

    # Minecraft Roots Search
    appdata = Path(os.environ.get("APPDATA", ""))
    localappdata = Path(os.environ.get("LOCALAPPDATA", ""))
    userprofile = Path(os.environ.get("USERPROFILE", ""))

    candidate_paths = [
        (appdata / ".minecraft", "Official / Standard Minecraft"),
        (appdata / ".tlauncher", "TLauncher"),
        (appdata / ".tla", "Legacy Launcher"),
        (userprofile / ".lunarclient", "Lunar Client"),
        (appdata / ".feather", "Feather Client"),
        (appdata / "PrismLauncher", "Prism Launcher"),
        (localappdata / "PrismLauncher", "Prism Launcher"),
        (appdata / "ModrinthApp", "Modrinth App"),
        (localappdata / "ModrinthApp", "Modrinth App"),
        (localappdata / "CurseForge", "CurseForge"),
        (appdata / ".atlauncher", "ATLauncher"),
        (appdata / ".koksik", "Koksik Launcher"),
    ]

    found_roots = []
    seen_paths = set()
    for p, name in candidate_paths:
        str_p = str(p).lower()
        if str_p not in seen_paths and p.exists() and p.is_dir():
            seen_paths.add(str_p)
            try:
                mtime = datetime.fromtimestamp(p.stat().st_mtime).strftime("%d.%m.%Y %H:%M:%S")
                found_roots.append({"name": name, "path": str(p), "last_modified": mtime})
            except Exception:
                pass

    return {
        "ok": True,
        "recycle_bin": {
            "num_items": num_items,
            "size_formatted": size_formatted,
            "latest_delete_date": latest_del_date,
            "status": "Очищена" if num_items == 0 else f"Файлов в корзине: {num_items}"
        },
        "temp_folder": {
            "status": temp_status,
            "files_count": len(valid_mtimes),
            "size_formatted": format_bytes(temp_total_bytes),
            "oldest_file": oldest_str,
            "newest_file": newest_str
        },
        "minecraft_roots": found_roots,
        "uptime": {
            "uptime_str": f"{days}д {hours}ч {minutes}мин",
            "boot_time": boot_dt.strftime("%d.%m.%Y %H:%M:%S")
        },
        "identity": {
            "computer_name": os.environ.get("COMPUTERNAME", "Unknown"),
            "user_name": os.environ.get("USERNAME", "Unknown"),
            "os_version": f"{platform.system()} {platform.release()} (Build {platform.version()})",
            "arch": platform.architecture()[0]
        },
        "timezone": {
            "current_time": datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
            "timezone_name": time.tzname[0] if time.tzname else "UTC"
        },
        "usb_history": {
            "total_count": usbs_count
        },
        "services": {
            "pcasvc": _service_status("PcaSvc"),
            "dps": _service_status("DPS"),
            "sysmain": _service_status("SysMain"),
            "eventlog": _service_status("EventLog")
        }
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

    def get_system_info_summary(self) -> dict:
        try:
            return get_system_info_summary()
        except Exception as exc:
            return error(str(exc))

    def open_folder_path(self, path: str) -> dict:
        try:
            target = Path(path).expanduser()
            if target.exists():
                os.startfile(str(target))
                return {"ok": True}
            return error(f"Folder does not exist: {path}")
        except Exception as exc:
            return error(str(exc))

    def default_mods_path(self) -> str:
        return default_mods_path()

    def get_usb_and_drive_footprints(self) -> dict:
        try:
            import winreg
            import string
            import re
            import os

            # 1. USB Storage History from USBSTOR
            usb_devices = []
            try:
                usbstor = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Enum\USBSTOR")
                num_devices = winreg.QueryInfoKey(usbstor)[0]
                for i in range(num_devices):
                    try:
                        device_id = winreg.EnumKey(usbstor, i)
                        device_key = winreg.OpenKey(usbstor, device_id)
                        num_serials = winreg.QueryInfoKey(device_key)[0]
                        for j in range(num_serials):
                            try:
                                serial = winreg.EnumKey(device_key, j)
                                serial_key = winreg.OpenKey(device_key, serial)
                                try:
                                    friendly_name, _ = winreg.QueryValueEx(serial_key, "FriendlyName")
                                except Exception:
                                    try:
                                        friendly_name, _ = winreg.QueryValueEx(serial_key, "DeviceDesc")
                                        if ";" in friendly_name:
                                            friendly_name = friendly_name.split(";")[-1]
                                    except Exception:
                                        friendly_name = device_id
                                try:
                                    info = winreg.QueryInfoKey(serial_key)
                                    ft = info[2]
                                    ts = (ft - 116444736000000000) / 10000000
                                    last_conn = datetime.fromtimestamp(ts).strftime("%d.%m.%Y %H:%M:%S")
                                except Exception:
                                    last_conn = "Unknown"

                                usb_devices.append({
                                    "name": friendly_name,
                                    "serial": serial,
                                    "device_id": device_id,
                                    "last_connected": last_conn
                                })
                            except Exception:
                                pass
                    except Exception:
                        pass
            except Exception:
                pass

            # 2. Get Mounted Drive Letters
            mounted_drives = set()
            for letter in string.ascii_uppercase:
                if os.path.exists(f"{letter}:\\"):
                    mounted_drives.add(letter)

            # 3. Parse ShellBags recursively to find drive footprints
            shellbag_paths = []
            
            def decode_shell_item(data):
                strings = []
                i = 0
                while i < len(data) - 1:
                    val = int.from_bytes(data[i:i+2], byteorder='little')
                    if (0x20 <= val <= 0x7E) or (0x400 <= val <= 0x4FF) or val in (0x5f, 0x2d, 0x2e, 0x5c, 0x2f, 0x3a):
                        s = ""
                        while i < len(data) - 1:
                            val = int.from_bytes(data[i:i+2], byteorder='little')
                            if val == 0:
                                i += 2
                                break
                            if (0x20 <= val <= 0x7E) or (0x400 <= val <= 0x4FF) or val in (0x5f, 0x2d, 0x2e, 0x5c, 0x2f, 0x3a):
                                s += chr(val)
                                i += 2
                            else:
                                i += 2
                                break
                        if len(s) >= 2:
                            strings.append(s)
                    else:
                        i += 1
                for a in re.findall(b'[a-zA-Z0-9_.-]{3,}', data):
                    try:
                        strings.append(a.decode('ascii'))
                    except Exception:
                        pass
                cleaned = []
                for s in strings:
                    s = s.strip()
                    if not s or s.lower() in ('autolist', 'autolistcachetime', 'autolistcachekey', 'nodecode', 'nodeslot', 'item', 'sps', 'shell'):
                        continue
                    cleaned.append(s)
                if cleaned:
                    candidates = [s for s in cleaned if not (s.startswith('{') and s.endswith('}'))]
                    if candidates:
                        return max(candidates, key=len)
                    return max(cleaned, key=len)
                return None

            def traverse(key_path, current_path):
                try:
                    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path)
                except Exception:
                    return
                try:
                    info = winreg.QueryInfoKey(key)
                    parent_ft = info[2]
                    parent_ts = (parent_ft - 116444736000000000) / 10000000
                    parent_time = datetime.fromtimestamp(parent_ts).strftime("%d.%m.%Y %H:%M:%S")
                except Exception:
                    parent_time = "Unknown"

                num_values = winreg.QueryInfoKey(key)[1]
                values_dict = {}
                for idx_val in range(num_values):
                    try:
                        name, data, val_type = winreg.EnumValue(key, idx_val)
                        if name.isdigit() and val_type == winreg.REG_BINARY:
                            decoded = decode_shell_item(data)
                            if decoded:
                                values_dict[int(name)] = decoded
                    except Exception:
                        pass
                num_subkeys = winreg.QueryInfoKey(key)[0]
                for idx_sub in range(num_subkeys):
                    try:
                        subkey_name = winreg.EnumKey(key, idx_sub)
                        if subkey_name.isdigit():
                            idx = int(subkey_name)
                            item_name = values_dict.get(idx, subkey_name)
                            if current_path:
                                if current_path.endswith('\\'):
                                    next_path = current_path + item_name
                                else:
                                    next_path = current_path + '\\' + item_name
                            else:
                                next_path = item_name

                            sub_time = parent_time
                            try:
                                sub_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, f"{key_path}\\{subkey_name}")
                                sub_info = winreg.QueryInfoKey(sub_key)
                                sub_ft = sub_info[2]
                                sub_ts = (sub_ft - 116444736000000000) / 10000000
                                sub_time = datetime.fromtimestamp(sub_ts).strftime("%d.%m.%Y %H:%M:%S")
                                winreg.CloseKey(sub_key)
                            except Exception:
                                pass

                            shellbag_paths.append((next_path, sub_time))
                            traverse(f"{key_path}\\{subkey_name}", next_path)
                    except Exception:
                        pass

            traverse(r"Software\Classes\Local Settings\Software\Microsoft\Windows\Shell\BagMRU", "")

            # 4. Parse OpenSavePidlMRU for files opened/saved
            mru_files = []
            try:
                mru_path = r"Software\Microsoft\Windows\CurrentVersion\Explorer\ComDlg32\OpenSavePidlMRU"
                mru_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, mru_path)
                num_subkeys = winreg.QueryInfoKey(mru_key)[0]
                for i in range(num_subkeys):
                    try:
                        ext = winreg.EnumKey(mru_key, i)
                        ext_key = winreg.OpenKey(mru_key, ext)
                        
                        try:
                            ext_info = winreg.QueryInfoKey(ext_key)
                            ext_ft = ext_info[2]
                            ext_ts = (ext_ft - 116444736000000000) / 10000000
                            ext_time = datetime.fromtimestamp(ext_ts).strftime("%d.%m.%Y %H:%M:%S")
                        except Exception:
                            ext_time = "Unknown"

                        num_values = winreg.QueryInfoKey(ext_key)[1]
                        for j in range(num_values):
                            try:
                                name, data, val_type = winreg.EnumValue(ext_key, j)
                                if name.isdigit() and val_type == winreg.REG_BINARY:
                                    decoded = decode_shell_item(data)
                                    if decoded:
                                        mru_files.append((decoded, ext_time))
                            except Exception:
                                pass
                        winreg.CloseKey(ext_key)
                    except Exception:
                        pass
                winreg.CloseKey(mru_key)
            except Exception:
                pass

            # Combine all footprints
            drive_footprints = []
            
            # Folders from ShellBags
            for path, last_visited in shellbag_paths:
                if len(path) >= 2 and path[0].isalpha() and path[1] == ':':
                    drive_letter = path[0].upper()
                    if "windows" in path.lower() or "program files" in path.lower():
                        continue
                    is_exists = os.path.exists(path)
                    parts = path.split('\\')
                    name = parts[-1] if parts else path
                    drive_footprints.append({
                        "name": name,
                        "path": path,
                        "status": "available" if is_exists else "missing",
                        "time": last_visited
                    })
                    
            # Files from OpenSavePidlMRU
            user_profile = Path(os.environ.get("USERPROFILE", ""))
            search_roots = [
                user_profile / "Downloads",
                user_profile / "Desktop",
                user_profile / "Documents",
                user_profile / "AppData" / "Roaming" / ".minecraft",
                Path(os.environ.get("TEMP", ""))
            ]
            
            import string
            available_drives = [f"{d}:\\" for d in string.ascii_uppercase if os.path.exists(f"{d}:\\")]
            
            search_cache = {}
            
            def find_file_everywhere(filename):
                if filename in search_cache:
                    return search_cache[filename]
                
                # Check user profile roots first (recursive)
                for root in search_roots:
                    if root.exists():
                        try:
                            # Using rglob to find the filename recursively
                            for p in root.rglob(filename):
                                if p.is_file():
                                    search_cache[filename] = str(p)
                                    return str(p)
                        except Exception:
                            pass
                
                # Check other drives recursively
                for drive in available_drives:
                    if drive.upper().startswith("C:"):
                        continue
                    try:
                        for root_dir, dirs, files in os.walk(drive):
                            # Skip system/trash dirs to avoid lag
                            dirs[:] = [d for d in dirs if d.lower() not in ('$recycle.bin', 'system volume information', 'program files', 'program files (x86)', 'windows')]
                            if filename in files:
                                full_path = os.path.join(root_dir, filename)
                                search_cache[filename] = full_path
                                return full_path
                    except Exception:
                        pass
                
                search_cache[filename] = None
                return None

            for path, last_visited in mru_files:
                # If it's a full path
                if len(path) >= 2 and path[0].isalpha() and path[1] == ':':
                    drive_letter = path[0].upper()
                    if "windows" in path.lower() or "program files" in path.lower():
                        continue
                    is_exists = os.path.exists(path)
                    parts = path.split('\\')
                    name = parts[-1] if parts else path
                    drive_footprints.append({
                        "name": name,
                        "path": path,
                        "status": "available" if is_exists else "missing",
                        "time": last_visited
                    })
                # If it's just a filename
                elif any(path.lower().endswith(ext) for ext in ('.jar', '.exe', '.zip', '.dll', '.rar', '.7z')):
                    if "windows" in path.lower() or "program files" in path.lower():
                        continue
                    
                    found_full_path = find_file_everywhere(path)
                    
                    if found_full_path:
                        drive_footprints.append({
                            "name": path,
                            "path": found_full_path,
                            "status": "available",
                            "time": last_visited
                        })
                    else:
                        drive_footprints.append({
                            "name": path,
                            "path": f"(filename only: {path})",
                            "status": "missing",
                            "time": last_visited
                        })

            # TypedPaths
            try:
                typed_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\TypedPaths")
                try:
                    t_info = winreg.QueryInfoKey(typed_key)
                    t_ft = t_info[2]
                    t_ts = (t_ft - 116444736000000000) / 10000000
                    typed_time = datetime.fromtimestamp(t_ts).strftime("%d.%m.%Y %H:%M:%S")
                except Exception:
                    typed_time = "Unknown"

                num_typed = winreg.QueryInfoKey(typed_key)[1]
                for i in range(num_typed):
                    try:
                        _, val, val_type = winreg.EnumValue(typed_key, i)
                        if val_type == winreg.REG_SZ:
                            path = val
                            if len(path) >= 2 and path[0].isalpha() and path[1] == ':':
                                is_exists = os.path.exists(path)
                                parts = path.split('\\')
                                name = parts[-1] if parts else path
                                if not name:
                                    name = path
                                drive_footprints.append({
                                    "name": name,
                                    "path": path,
                                    "status": "available" if is_exists else "missing",
                                    "time": typed_time
                                })
                    except Exception:
                        pass
                winreg.CloseKey(typed_key)
            except Exception:
                pass

            seen_paths = set()
            unique_footprints = []
            for fp in drive_footprints:
                if fp["path"] not in seen_paths:
                    seen_paths.add(fp["path"])
                    p_str = fp.get("path", "")
                    fp["size"] = "-"
                    if p_str and os.path.exists(p_str):
                        try:
                            if os.path.isfile(p_str):
                                sz = os.path.getsize(p_str)
                                if sz < 1024: fp["size"] = f"{sz} B"
                                elif sz < 1024*1024: fp["size"] = f"{sz/1024:.1f} KB"
                                else: fp["size"] = f"{sz/(1024*1024):.1f} MB"
                            elif os.path.isdir(p_str):
                                fp["size"] = "Папка"
                        except Exception:
                            pass
                    unique_footprints.append(fp)

            return {
                "ok": True,
                "usb_devices": usb_devices,
                "footprints": unique_footprints
            }
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    def scan_browser_history(self) -> dict:
        try:
            import os
            import sqlite3
            import tempfile
            import shutil
            from pathlib import Path
            from datetime import datetime
            import re

            local_app_data = os.environ.get("LOCALAPPDATA", "")
            app_data = os.environ.get("APPDATA", "")

            paths = []

            # Chrome
            chrome_user_data = Path(local_app_data) / "Google" / "Chrome" / "User Data"
            if chrome_user_data.exists():
                for p in ["Default", "Profile 1", "Profile 2", "Profile 3", "Profile 4", "Profile 5"]:
                    hist = chrome_user_data / p / "History"
                    if hist.exists():
                        paths.append(("Chrome (" + p + ")", hist))

            # Yandex
            yandex_user_data = Path(local_app_data) / "Yandex" / "YandexBrowser" / "User Data"
            if yandex_user_data.exists():
                for p in ["Default", "Profile 1", "Profile 2", "Profile 3", "Profile 4", "Profile 5"]:
                    hist = yandex_user_data / p / "History"
                    if hist.exists():
                        paths.append(("Yandex (" + p + ")", hist))

            # Edge
            edge_user_data = Path(local_app_data) / "Microsoft" / "Edge" / "User Data"
            if edge_user_data.exists():
                for p in ["Default", "Profile 1", "Profile 2", "Profile 3", "Profile 4", "Profile 5"]:
                    hist = edge_user_data / p / "History"
                    if hist.exists():
                        paths.append(("Edge (" + p + ")", hist))

            # Opera Stable
            opera_stable = Path(app_data) / "Opera Software" / "Opera Stable" / "History"
            if opera_stable.exists():
                paths.append(("Opera Stable", opera_stable))

            # Opera GX
            opera_gx = Path(app_data) / "Opera Software" / "Opera GX Stable" / "History"
            if opera_gx.exists():
                paths.append(("Opera GX", opera_gx))

            # Firefox
            firefox_profiles = Path(app_data) / "Mozilla" / "Firefox" / "Profiles"
            if firefox_profiles.exists():
                for p in firefox_profiles.iterdir():
                    places = p / "places.sqlite"
                    if places.exists():
                        paths.append(("Firefox (" + p.name + ")", places))

            results = []

            def is_cheat_match(text: str) -> bool:
                t = text.lower()
                patterns = [
                    r'(?:^|[^a-zA-Z])(?:vape|drip|entropy|whiteout|juul|skilled|itami|koid|wurst|impact|sigma|liquidbounce|meteor|aristois|salhack|future|rusherhack|phobos|pyro|bleachhack|inertia|huzuni|celestial|sunrise|akrien|zamorozka|hono|nurik|excellent|expensive|fluger|deadcode|exore|byster|spook|rudo|boze|fdpclient|nightx|augustus|exhibition|remix|novoline|tenacity|dortware|azura|lime|zeroday|meteorclient|forgehax|seppuku|lambda|earthhack|catalyst|kami|wurstplus|wurstplusthree|wurstplustwo|weepcraft|wolfram|nodus|metro|kronos|saint|xenon|obsidian|skillclient|icarus|lucid|matmos|darklight|pandora|jigsaw|flux|moon|astolfo|rise|phantom|kangaroo|keystrokes|hitbox|velocity|doubleclick|doubleclicker|fastplace|safewalk|freecam|autoarmor|bowaimbot|fastbow|antiafk|autorespawn|autodisconnect|autoleave|antibot|nametags|tracers|xray|fullbright|breadcrumbs|baritone|ventos|neoware|viafriend|viaforge|blackberry|viamcp|viaversion|neat|pivo|sight|itemscroller|external|violetta|autofish|rasty|niobiom|legion|matix|rockstar|autobuy|sevenmyst|bloodymyst|boberware|legacylauncher|ezz|nursultan|aura|exloader|elysium|silentclient|voxelmap|celka|nur|akr|plusinv|armorhotswap|winstore|elytra|fabritone|ponos|nova|nextgen|moonhack|expa|wexside|zeta|topka|minced|bleach|basefinder|shit|kion|wisend|blazehack|nightmare|sonar|wintware|delta|aboba|nullhack|develor|sapwhire|kazah|bypass|recode|avalone|miner|neverhook|stardust|norule|norules|oxygen|dreampool|topkamods|keaz|konas|goprone|airplace|eternity|noslow|caballeta|clowdy|cetramoon|duper|extra|scritps|gothaj|easyfrags|easyanticheat|celestialrecode|autotool|newlauncher|deltaloader|wildclient|jessica|thunderhack|doomsday|nightware|ricardo|extazyy|troxill|antileak|arbuz|dauntiblyat|rename_me_please|editme|takker|fuzeclient|wisefolder|flauncher|feather|venus|spambot|cleancut|spam_bot|inventory_walk|player_highlighter|bedrock_breaker_mode|double_hotbar|elytra_swap|smart_moving|chest|savesearcher|topkautobuy|topkaautobuy|tweakeroo|mob_hitbox|librarian_trade_finder|sacurachorusfind|autoattack|entity_outliner|invmove|viabackwards|viarewind|viafabric|viaproxy|vialoader|elytrahack|diamondsim|control-tweaks|swingthroughgrass|cutthrough|haruka|blade|hachclient|catlean)(?:$|[^a-zA-Z])',
                    r'(?:^|\b|_)(?:crypt|rich|mint|ares|reach|fly|fdp|wex|vec)(?:\b|_|$)',
                    r'(?:autoclicker|cheatengine|processhacker|systeminformer|extremeinjector|extreme[-_\s]injector|hackedclient|hacked[-_\s]client|cheat[-_\s]mod|cheat[-_\s]client|cheat[-_\s]pack|cheat[-_\s]launcher|cheatlauncher|cheatpack|reallyworld[-_\s]cheat|holyworld[-_\s]cheat|vime[-_\s]cheat|vimeworld[-_\s]cheat|wellmore[-_\s]cheat|usboblivion)'
                ]
                for p in patterns:
                    if re.search(p, t):
                        return True
                return False

            def from_webkit_time(timestamp):
                try:
                    if timestamp > 10000000000000000:
                        timestamp = timestamp // 1000000
                    elif timestamp > 10000000000000:
                        timestamp = timestamp // 1000
                    return datetime.fromtimestamp(timestamp - 11644473600).strftime("%Y-%m-%d %H:%M:%S")
                except Exception:
                    return "-"

            def from_firefox_time(timestamp):
                try:
                    return datetime.fromtimestamp(timestamp // 1000000).strftime("%Y-%m-%d %H:%M:%S")
                except Exception:
                    return "-"

            for browser_name, db_path in paths:
                temp_file = tempfile.NamedTemporaryFile(delete=False)
                temp_path = Path(temp_file.name)
                temp_file.close()

                try:
                    shutil.copy2(db_path, temp_path)
                    conn = sqlite3.connect(str(temp_path))
                    cursor = conn.cursor()

                    if "Firefox" in browser_name:
                        try:
                            cursor.execute("SELECT url, title, last_visit_date FROM moz_places WHERE last_visit_date IS NOT NULL")
                            for url, title, date in cursor.fetchall():
                                url_str = url or ""
                                title_str = title or ""
                                match_text = f"{url_str} {title_str}"
                                if is_cheat_match(match_text):
                                    results.append({
                                        "browser": browser_name,
                                        "type": "visit",
                                        "name": title_str or url_str,
                                        "url": url_str,
                                        "time": from_firefox_time(date)
                                    })
                        except Exception:
                            pass
                    else:
                        try:
                            cursor.execute("SELECT url, title, last_visit_time FROM urls")
                            for url, title, date in cursor.fetchall():
                                url_str = url or ""
                                title_str = title or ""
                                match_text = f"{url_str} {title_str}"
                                if is_cheat_match(match_text):
                                    results.append({
                                        "browser": browser_name,
                                        "type": "visit",
                                        "name": title_str or url_str,
                                        "url": url_str,
                                        "time": from_webkit_time(date)
                                    })
                        except Exception:
                            pass

                        try:
                            cursor.execute("SELECT target_path, start_time, referrer FROM downloads")
                            for path, date, referrer in cursor.fetchall():
                                path_str = path or ""
                                ref_str = referrer or ""
                                match_text = f"{path_str} {ref_str}"
                                if is_cheat_match(match_text):
                                    filename = Path(path_str).name
                                    results.append({
                                        "browser": browser_name,
                                        "type": "download",
                                        "name": filename or path_str,
                                        "url": ref_str or "N/A",
                                        "time": from_webkit_time(date)
                                    })
                        except Exception:
                            pass

                    conn.close()
                except Exception:
                    pass
                finally:
                    try:
                        temp_path.unlink()
                    except OSError:
                        pass

            valid_results = [r for r in results if r["time"] != "-"]
            invalid_results = [r for r in results if r["time"] == "-"]
            valid_results.sort(key=lambda x: x["time"], reverse=True)
            sorted_results = valid_results + invalid_results
            return {"ok": True, "items": sorted_results}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

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

    def choose_jars(self) -> list:
        try:
            import webview
            if not self._window:
                return []
            result = self._window.create_file_dialog(webview.OPEN_DIALOG, allow_multiple=True, file_types=("Jar files (*.jar)", "All files (*.*)"))
            return list(result) if result else []
        except Exception:
            return []

    def choose_image(self) -> str:
        try:
            import webview
            if not self._window:
                return ""
            result = self._window.create_file_dialog(webview.OPEN_DIALOG, file_types=("Image files (*.png;*.jpg;*.jpeg)", "All files (*.*)"))
            return result[0] if result else ""
        except Exception:
            return ""

    def open_url(self, url: str) -> dict:
        import webbrowser
        try:
            webbrowser.open(url)
            return {"ok": True}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    def cancel_scan(self) -> dict:
        return cancel_scan()

    def reset_cancel_scan(self) -> dict:
        return reset_cancel_scan()

    def get_scan_progress(self) -> dict:
        return get_scan_progress()

    def scan_usb_footprints(self) -> dict:
        return self.get_usb_and_drive_footprints()

    def scan_path(self, path: str) -> dict:
        return scan_path(path)

    def scan_jar_jarka(self, jar_path: str) -> dict:
        if CANCEL_SCAN_REQUESTED:
            return error("Scan stopped by user")
        try:
            from jarka_scanner.scanner import scan_jar
            path = Path(jar_path.strip().strip('"'))
            if not path.exists():
                return error(f"File not found: {path}")
            
            # Calculate hashes
            h_md5 = hashlib.md5()
            h_sha1 = hashlib.sha1()
            h_sha256 = hashlib.sha256()
            with path.open("rb") as f:
                for chunk in iter(lambda: f.read(1024 * 1024), b""):
                    h_md5.update(chunk)
                    h_sha1.update(chunk)
                    h_sha256.update(chunk)
            
            hashes = {
                "md5": h_md5.hexdigest(),
                "sha1": h_sha1.hexdigest(),
                "sha256": h_sha256.hexdigest(),
            }
            
            if not path.suffix.lower() == ".jar":
                # For non-jar files, we just return the hashes
                return {
                    "ok": True,
                    "target": str(path),
                    "is_jar": False,
                    "hashes": hashes,
                    "results": {
                        "risk_score": 0,
                        "risk_level": "N/A",
                        "ai": {"malware_probability": 0},
                        "cheats": {},
                        "evidence": []
                    }
                }
            
            # Run Modrinth check, Heuristics, Download source, AND Jarka scanner!
            modrinth = check_modrinth(path)
            heuristics = [] if modrinth else heuristic_results(path)
            source = download_source(path)
            results = scan_jar(str(path), path.stat().st_size if path.exists() else 0)
            if results.get('error'):
                return error(results['error'])
            
            # Enrich Jarka evidence with heuristic logs and Modrinth status
            evidence = results.get("evidence", [])
            if modrinth:
                evidence.insert(0, {
                    "rule": "Modrinth Verified",
                    "severity": "info",
                    "description": f"Verified Modrinth release ({modrinth.get('project', '')} v{modrinth.get('version', '')})"
                })
            else:
                for h in heuristics:
                    evidence.append({
                        "rule": h.get("type", "Heuristic Match"),
                        "severity": "high" if h.get("confidence") == "high" or h.get("risk") == "high" else "warning",
                        "description": h.get("details", h.get("message", str(h)))
                    })

            if source and source.get("url"):
                evidence.append({
                    "rule": "Download Source (ADS)",
                    "severity": "info",
                    "description": f"Downloaded from: {source.get('url')}"
                })

            results["evidence"] = evidence
            results["modrinth"] = modrinth
            results["download_source"] = source
            results["heuristics"] = heuristics
                
            return {
                "ok": True,
                "target": str(path),
                "is_jar": True,
                "hashes": hashes,
                "results": results,
            }
        except ImportError:
            return error("JarkaScanner module not available")
        except Exception as exc:
            return error(str(exc))

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
            return scan_ghost()
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
            pid = os.getpid()
            exe_path = Path(sys.executable).resolve() if getattr(sys, "frozen", False) else None
            tools_dir = (APP_ROOT / "tools").resolve()
            pid_file = (APP_ROOT / "aurorachecker.pid").resolve()
            
            bat_path = Path(tempfile.gettempdir()) / f"cleanup_{pid}.bat"
            
            lines = [
                "@echo off",
                "title AuroraChecker Cleanup",
                ":loop",
                f'tasklist /FI "PID eq {pid}" 2>nul | find "{pid}" >nul',
                "if not errorlevel 1 (",
                "    ping -n 2 127.0.0.1 >nul",
                "    goto loop",
                ")",
                "ping -n 1 127.0.0.1 >nul",
            ]
            
            if exe_path:
                lines.extend([
                    ":del_exe",
                    f'if exist "{exe_path}" (',
                    f'    del /f /q "{exe_path}"',
                    f'    if exist "{exe_path}" (',
                    "        ping -n 2 127.0.0.1 >nul",
                    "        goto del_exe",
                    "    )",
                    ")"
                ])
            if tools_dir.exists():
                lines.extend([
                    ":del_tools",
                    f'if exist "{tools_dir}" (',
                    f'    rd /s /q "{tools_dir}"',
                    f'    if exist "{tools_dir}" (',
                    "        ping -n 2 127.0.0.1 >nul",
                    "        goto del_tools",
                    "    )",
                    ")"
                ])
            if pid_file.exists():
                lines.extend([
                    ":del_pid",
                    f'if exist "{pid_file}" (',
                    f'    del /f /q "{pid_file}"',
                    f'    if exist "{pid_file}" (',
                    "        ping -n 2 127.0.0.1 >nul",
                    "        goto del_pid",
                    "    )",
                    ")"
                ])
                
            lines.append('del "%~f0"')
            bat_content = "\n".join(lines) + "\n"
            
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

    def delete_files(self, paths: list[str]) -> dict:
        try:
            deleted = 0
            errors = []
            for path_str in paths:
                p = Path(path_str.strip().strip('"'))
                if p.is_file():
                    try:
                        p.unlink()
                        deleted += 1
                    except Exception as e:
                        errors.append(f"Failed to delete {p.name}: {str(e)}")
            if errors:
                return {"ok": False, "error": "; ".join(errors), "deleted": deleted}
            return {"ok": True, "deleted": deleted}
        except Exception as exc:
            return error(str(exc))

    def launch_jar(self, jar_path: str) -> dict:
        try:
            path = Path(jar_path.strip().strip('"'))
            if not path.exists():
                return error(f"File not found: {path}")
            if not path.suffix.lower() == ".jar":
                return error("Selected file is not a .jar archive")
            
            java_exes = ["javaw", "java", "javaw.exe", "java.exe"]
            tools_java = TOOLS_DIR / "Java"
            if tools_java.is_dir():
                for candidate in tools_java.rglob("javaw.exe"):
                    if candidate.is_file():
                        java_exes.insert(0, str(candidate))
                for candidate in tools_java.rglob("java.exe"):
                    if candidate.is_file():
                        java_exes.insert(1, str(candidate))
            
            success = False
            err_msg = ""
            for java_exe in java_exes:
                try:
                    subprocess.Popen(
                        [java_exe, "-jar", str(path)],
                        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0,
                        close_fds=True
                    )
                    success = True
                    break
                except Exception as e:
                    err_msg = str(e)
                    continue
            
            if success:
                return {"ok": True, "message": f"Successfully launched via {java_exe}"}
            return error(f"Could not launch Java: {err_msg}. Verify that Java is installed on your system.")
        except Exception as exc:
            return error(str(exc))

    def list_all_processes(self) -> dict:
        try:
            processes = minecraft_like_processes()
            return {"ok": True, "processes": processes}
        except Exception as exc:
            return error(str(exc))

    def terminate_process(self, pid: int) -> dict:
        try:
            import ctypes
            PROCESS_TERMINATE = 0x0001
            handle = ctypes.windll.kernel32.OpenProcess(PROCESS_TERMINATE, False, int(pid))
            if handle:
                success = ctypes.windll.kernel32.TerminateProcess(handle, 0)
                ctypes.windll.kernel32.CloseHandle(handle)
                if success:
                    return {"ok": True, "message": f"PID {pid} terminated"}
            return error(f"Failed to terminate PID {pid}: Access denied or process not found")
        except Exception as exc:
            return error(str(exc))

    def scan_anti_bypass(self) -> dict:
        try:
            cleaners_keywords = ["usboblivion", "bleachbit", "ccleaner", "privazer", "regcleaner", "filewipe", "shredder"]
            findings = []
            
            # Check services
            disabled_services = []
            for srv_name in ["PcaSvc", "DPS", "SysMain", "EventLog"]:
                st = _service_status(srv_name)
                if "stopped" in st.lower() or "disabled" in st.lower() or "not found" in st.lower():
                    disabled_services.append(f"{srv_name} ({st})")
            if disabled_services:
                findings.append({
                    "category": "Disabled Forensic Services",
                    "detail": "Disabled/Stopped: " + ", ".join(disabled_services),
                    "risk": "HIGH"
                })
                
            # Check EventLog Event ID 104 / 1102 (Log Cleared)
            try:
                cmd = ["powershell", "-NoProfile", "-NonInteractive", "-Command",
                       "Get-WinEvent -ListLog System,Security -ErrorAction SilentlyContinue | Get-WinEvent -FilterHashtable @{Id=104,1102} -ErrorAction SilentlyContinue | Select-Object TimeCreated,Id,Message | ConvertTo-Json"]
                proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="ignore", timeout=12, **hidden_subprocess_options())
                if proc.returncode == 0 and proc.stdout.strip():
                    ev_data = json.loads(proc.stdout)
                    if isinstance(ev_data, dict): ev_data = [ev_data]
                    for ev in ev_data:
                        findings.append({
                            "category": "System Log Cleared (Event ID 104/1102)",
                            "detail": f"Log cleared at {ev.get('TimeCreated')} (ID {ev.get('Id')})",
                            "risk": "CRITICAL"
                        })
            except Exception:
                pass

            # Search cleaner traces in Prefetch / Temp / Downloads
            user = os.environ.get("USERPROFILE", "")
            search_paths = [
                Path(user) / "Downloads",
                Path(user) / "Desktop",
                Path(user) / "AppData" / "Local" / "Temp",
                Path(r"C:\Windows\Prefetch")
            ]
            for sp in search_paths:
                if sp.exists():
                    try:
                        for p in sp.iterdir():
                            name_lower = p.name.lower()
                            for kw in cleaners_keywords:
                                if kw in name_lower:
                                    findings.append({
                                        "category": "Cleaner / Anti-Forensic Tool Found",
                                        "detail": f"Trace in {sp.name}: {p.name}",
                                        "risk": "HIGH"
                                    })
                                    break
                    except Exception:
                        pass

            return {"ok": True, "findings": findings, "cleaners_detected": len(findings)}
        except Exception as exc:
            return error(str(exc))

    def scan_all_launchers(self) -> dict:
        try:
            user = Path(os.environ.get("USERPROFILE", ""))
            appdata = Path(os.environ.get("APPDATA", ""))
            
            launcher_dirs = [
                ("Official / Vanilla", appdata / ".minecraft"),
                ("TLauncher", appdata / ".tlauncher"),
                ("Legacy Launcher", appdata / "LegacyLauncher"),
                ("TLauncher Legacy", appdata / ".tlauncher" / "legacy"),
                ("Prism Launcher", appdata / "PrismLauncher"),
                ("PolyMC", appdata / "PolyMC"),
                ("MultiMC", appdata / "MultiMC"),
                ("Lunar Client", user / ".lunarclient"),
                ("Feather Client", user / ".feather"),
                ("CurseForge", appdata / "CurseForge"),
                ("ATLauncher", appdata / "ATLauncher")
            ]
            
            scanned_launchers = []
            found_suspicious_mods = []
            cheat_keywords = ["expensive", "nursultan", "celestial", "akrien", "wexside", "zamorozka", "rich", "doomsday", "liminar", "vec.dll", "skid", "wild", "minced", "freecam", "killaura"]

            for l_name, l_path in launcher_dirs:
                if l_path.exists():
                    mods_count = 0
                    suspicious_in_launcher = []
                    try:
                        for jar_file in l_path.rglob("*.jar"):
                            mods_count += 1
                            fname = jar_file.name.lower()
                            for kw in cheat_keywords:
                                if kw in fname:
                                    suspicious_in_launcher.append(jar_file.name)
                                    found_suspicious_mods.append({
                                        "launcher": l_name,
                                        "mod": jar_file.name,
                                        "path": str(jar_file)
                                    })
                                    break
                    except Exception:
                        pass
                        
                    scanned_launchers.append({
                        "name": l_name,
                        "path": str(l_path),
                        "installed": True,
                        "jar_count": mods_count,
                        "suspicious_count": len(suspicious_in_launcher)
                    })
                else:
                    scanned_launchers.append({
                        "name": l_name,
                        "path": str(l_path),
                        "installed": False,
                        "jar_count": 0,
                        "suspicious_count": 0
                    })

            return {
                "ok": True,
                "launchers": scanned_launchers,
                "suspicious_mods": found_suspicious_mods
            }
        except Exception as exc:
            return error(str(exc))

    def generate_ban_verdict(self, player_name: str) -> dict:
        try:
            p_name = player_name.strip() or "Player"
            
            # Simple check of traces
            reasons = []
            # Check USN deleted
            try:
                cmd = ["cmd.exe", "/d", "/c", "fsutil usn readjournal C: csv 2>&1"]
                proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="ignore", timeout=15, **hidden_subprocess_options())
                for line in proc.stdout.splitlines():
                    if ".jar" in line.lower() or ".dll" in line.lower():
                        parts = [p.strip('" ') for p in line.split(",")]
                        if len(parts) >= 4 and ("DELETE" in parts[3].upper() or "0x00000200" in parts[3]):
                            reasons.append(f"USN Deleted File: {parts[0]}")
                            break
            except Exception:
                pass
                
            ban_reason = " | ".join(reasons) if reasons else "Cheat Signatures / Forensic Evidence Found"
            ban_command = f"/ban {p_name} 30d 2.4 ({ban_reason})"
            
            verdict_card = f"""==================================================
           AURORACHECKER MODERATION VERDICT
==================================================
Target Player: {p_name}
Date & Time: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}
Status: {'CHEATS DETECTED ❌' if reasons else 'CLEAN / UNVERIFIED ⚠️'}

REASON DETAILS:
{chr(10).join('• ' + r for r in reasons) if reasons else '• No high-risk automated detections triggered.'}

COPYABLE BAN COMMAND:
{ban_command}
=================================================="""

            return {"ok": True, "ban_command": ban_command, "verdict_card": verdict_card}
        except Exception as exc:
            return error(str(exc))

    def send_webhook_report(self, webhook_url: str, content_text: str) -> dict:
        try:
            target = webhook_url.strip()
            if not target:
                return error("Webhook / Chat ID is empty")
                
            bot_token = "8932014258:AAErJRhe3qycIhW6ugGyen-zcTrYQ5avHOU"
            
            # Check if it's a Discord Webhook URL
            if "discord.com" in target or "discordapp.com" in target:
                payload = json.dumps({"content": f"```\n{content_text[:1900]}\n```"}).encode("utf-8")
                req = urllib.request.Request(target, data=payload, headers={"Content-Type": "application/json"}, method="POST")
                with urllib.request.urlopen(req, timeout=8.0) as resp:
                    return {"ok": True, "message": "Report sent to Discord Webhook"}
                    
            # Check if target is a Telegram Chat ID or Channel (e.g. -100..., @channel, or digits)
            is_chat_id = target.startswith("-") or target.startswith("@") or target.isdigit()
            if is_chat_id:
                tg_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                payload = json.dumps({"chat_id": target, "text": content_text[:4000]}).encode("utf-8")
                req = urllib.request.Request(tg_url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
                with urllib.request.urlopen(req, timeout=8.0) as resp:
                    return {"ok": True, "message": f"Report sent to Telegram Chat ({target})"}

            # Check if target is a full Telegram API URL
            if "api.telegram.org" in target:
                payload = json.dumps({"text": content_text[:4000]}).encode("utf-8")
                req = urllib.request.Request(target, data=payload, headers={"Content-Type": "application/json"}, method="POST")
                with urllib.request.urlopen(req, timeout=8.0) as resp:
                    return {"ok": True, "message": "Report sent to Telegram"}

            # Default HTTP POST
            payload = json.dumps({"text": content_text}).encode("utf-8")
            req = urllib.request.Request(target, data=payload, headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=8.0) as resp:
                return {"ok": True, "message": "Report sent to Webhook"}
        except Exception as exc:
            return error(str(exc))

    def send_image_report(self, target: str, player: str, reason: str, duration: str, report_num: str, image_path: str = "") -> dict:
        try:
            target = target.strip()
            if not target:
                return error("Webhook URL or Telegram Chat ID is empty")
                
            p_name = player.strip() or "Unknown"
            p_reason = reason.strip() or "Использование запрещенного ПО / читов"
            p_dur = duration.strip() or "30 дней"
            p_num = report_num.strip() or str(random.randint(100000, 999999))
            
            # Read license info
            lic_mod = "Unknown"
            lic_srv = "AuroraChecker"
            lic_file = Path(os.environ.get("LOCALAPPDATA", "")) / "AuroraChecker" / "license.json"
            if lic_file.exists():
                try:
                    lic_d = json.loads(lic_file.read_text(encoding="utf-8"))
                    lic_mod = lic_d.get("moderator", "Moderator")
                    lic_srv = lic_d.get("server", "Server")
                except Exception:
                    pass
            
            bot_token = "8932014258:AAErJRhe3qycIhW6ugGyen-zcTrYQ5avHOU"
            img_file = Path(image_path.strip().strip('"')) if image_path else None
            
            # Send to Discord Webhook
            if "discord.com" in target or "discordapp.com" in target:
                import uuid
                boundary = "----WebKitFormBoundary" + uuid.uuid4().hex
                
                embed = {
                    "title": f"🚨 Отчет о нарушении №{p_num}",
                    "color": 15158332,
                    "fields": [
                        {"name": "1. Ник нарушителя", "value": f"`{p_name}`", "inline": True},
                        {"name": "2. Причина", "value": f"`{p_reason}`", "inline": True},
                        {"name": "3. Срок наказания", "value": f"`{p_dur}`", "inline": True},
                        {"name": "4. Номер отчета", "value": f"`#{p_num}`", "inline": True},
                        {"name": "Модератор", "value": f"`{lic_mod}`", "inline": True},
                        {"name": "Проект / Сервер", "value": f"`{lic_srv}`", "inline": True}
                    ],
                    "footer": {"text": f"AuroraChecker Forensics • {lic_srv}"}
                }
                
                if img_file and img_file.is_file():
                    embed["image"] = {"url": f"attachment://{img_file.name}"}
                    
                payload_json = json.dumps({"embeds": [embed]})
                
                body = bytearray()
                body.extend(f"--{boundary}\r\nContent-Disposition: form-data; name=\"payload_json\"\r\nContent-Type: application/json\r\n\r\n{payload_json}\r\n".encode("utf-8"))
                
                if img_file and img_file.is_file():
                    img_bytes = img_file.read_bytes()
                    body.extend(f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{img_file.name}\"\r\nContent-Type: image/png\r\n\r\n".encode("utf-8"))
                    body.extend(img_bytes)
                    body.extend(b"\r\n")
                    
                body.extend(f"--{boundary}--\r\n".encode("utf-8"))
                
                req = urllib.request.Request(
                    target,
                    data=bytes(body),
                    headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=15.0) as resp:
                    return {"ok": True, "message": f"Отчет №{p_num} со скриншотом успешно отправлен в Discord!"}

            # Send to Telegram
            is_chat_id = target.startswith("-") or target.startswith("@") or target.isdigit()
            if is_chat_id or "api.telegram.org" in target:
                caption = f"🚨 *Отчет о нарушении №{p_num}*\n\n1. *Ник:* `{p_name}`\n2. *Причина:* `{p_reason}`\n3. *Срок наказания:* `{p_dur}`\n4. *Номер отчета:* `#{p_num}`"
                
                if img_file and img_file.is_file():
                    tg_url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
                    import uuid
                    boundary = "----WebKitFormBoundary" + uuid.uuid4().hex
                    body = bytearray()
                    
                    chat_id_val = target if is_chat_id else target.split("chat_id=")[-1]
                    body.extend(f"--{boundary}\r\nContent-Disposition: form-data; name=\"chat_id\"\r\n\r\n{chat_id_val}\r\n".encode("utf-8"))
                    body.extend(f"--{boundary}\r\nContent-Disposition: form-data; name=\"caption\"\r\n\r\n{caption}\r\n".encode("utf-8"))
                    body.extend(f"--{boundary}\r\nContent-Disposition: form-data; name=\"parse_mode\"\r\n\r\nMarkdown\r\n".encode("utf-8"))
                    
                    img_bytes = img_file.read_bytes()
                    body.extend(f"--{boundary}\r\nContent-Disposition: form-data; name=\"photo\"; filename=\"{img_file.name}\"\r\nContent-Type: image/png\r\n\r\n".encode("utf-8"))
                    body.extend(img_bytes)
                    body.extend(b"\r\n")
                    body.extend(f"--{boundary}--\r\n".encode("utf-8"))
                    
                    req = urllib.request.Request(
                        tg_url,
                        data=bytes(body),
                        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
                        method="POST"
                    )
                    with urllib.request.urlopen(req, timeout=15.0) as resp:
                        return {"ok": True, "message": f"Отчет №{p_num} со скриншотом отправлен в Telegram!"}
                else:
                    tg_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                    payload = json.dumps({"chat_id": target, "text": caption, "parse_mode": "Markdown"}).encode("utf-8")
                    req = urllib.request.Request(tg_url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
                    with urllib.request.urlopen(req, timeout=10.0) as resp:
                        return {"ok": True, "message": f"Отчет №{p_num} отправлен в Telegram!"}
                        
            return error("Некорректный URL вебхука или ID чата")
        except Exception as exc:
            return error(str(exc))

    def get_license_info(self) -> dict:
        try:
            lic_file = Path(os.environ.get("LOCALAPPDATA", "")) / "AuroraChecker" / "license.json"
            if lic_file.exists():
                data = json.loads(lic_file.read_text(encoding="utf-8"))
                return {"ok": True, "active": True, "data": data}
            return {"ok": True, "active": False}
        except Exception as exc:
            return {"ok": False, "active": False, "error": str(exc)}

    def activate_license_key(self, key: str, mod_name: str, server_name: str) -> dict:
        try:
            k = key.strip().upper()
            m = mod_name.strip() or "Moderator"
            s = server_name.strip() or "Minecraft Server"
            
            if not k:
                return error("Введите ключ доступа")
                
            valid_master = ["AURORA-ADMIN-KEY", "AURORA-VIP-2026", "AURORA-FREE-KEY", "AURORA-MOD-2026"]
            is_valid_format = k.startswith("AURORA-") and len(k) >= 10
            
            if k not in valid_master and not is_valid_format:
                return error("Недействительный ключ доступа! Формат: AURORA-XXXX-XXXX-XXXX")
                
            lic_dir = Path(os.environ.get("LOCALAPPDATA", "")) / "AuroraChecker"
            lic_dir.mkdir(parents=True, exist_ok=True)
            lic_file = lic_dir / "license.json"
            
            role = "Administrator" if "ADMIN" in k else "Moderator"
            data = {
                "key": k,
                "moderator": m,
                "server": s,
                "role": role,
                "activated_at": datetime.now().strftime("%d.%m.%Y %H:%M:%S")
            }
            lic_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            return {"ok": True, "message": f"Ключ успешно активирован! Роль: {role}", "data": data}
        except Exception as exc:
            return error(str(exc))

    def generate_license_key(self, role: str = "MOD") -> dict:
        try:
            import uuid
            part1 = uuid.uuid4().hex[:4].upper()
            part2 = uuid.uuid4().hex[:4].upper()
            new_key = f"AURORA-{role.upper()}-{part1}-{part2}"
            return {"ok": True, "key": new_key}
        except Exception as exc:
            return error(str(exc))

    def deactivate_license(self) -> dict:
        try:
            lic_file = Path(os.environ.get("LOCALAPPDATA", "")) / "AuroraChecker" / "license.json"
            if lic_file.exists():
                lic_file.unlink()
            return {"ok": True, "message": "Лицензия деактивирована"}
        except Exception as exc:
            return error(str(exc))
        try:
            p = Path(jar_path.strip().strip('"'))
            if not p.is_file() or p.suffix.lower() != ".jar":
                return error("Invalid .jar file")
                
            import zipfile
            with zipfile.ZipFile(str(p), "r") as z:
                all_entries = z.namelist()
                class_entries = [e for e in all_entries if e.endswith(".class")]
                
                if not member_name:
                    return {
                        "ok": True,
                        "total_entries": len(all_entries),
                        "class_count": len(class_entries),
                        "classes": class_entries[:150]
                    }
                    
                if member_name not in all_entries:
                    return error(f"Entry {member_name} not found in JAR")
                    
                content_bytes = z.read(member_name)
                printable_strings = re.findall(r"[A-Za-z0-9_\-\.\:\/\@\$\<\>]{4,}", content_bytes.decode("latin-1", errors="ignore"))
                unique_strings = list(dict.fromkeys(printable_strings))[:200]
                
                return {
                    "ok": True,
                    "entry": member_name,
                    "size_bytes": len(content_bytes),
                    "extracted_strings": unique_strings
                }
        except Exception as exc:
            return error(str(exc))
