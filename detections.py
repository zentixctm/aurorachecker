import re

TELEGRAM_TOKEN_RE = re.compile(r'[0-9]{8,10}:[A-Za-z0-9_-]{35}')

TELEGRAM_STRINGS = {
    "https://api.telegram.org", "sendMessage", "chat_id",
    "mcLogger", "mclogger", "MC LOGGER",
    "@rejavastealbot", "rejavastealbot", "skr.sh/saE3s725Lnp",
}

DISCORD_STRINGS = {
    "discord.com/api/webhooks", "discordapp.com/api/webhooks",
    "Java-DiscordWebhook",
}

PASSWORD_LOGGER_STRINGS = {"/reg", "/register", "/login", "/l"}

CLIPBOARD_STRINGS = {"Toolkit.getDefaultToolkit", "getSystemClipboard"}

SCREENSHOT_STRINGS = {"Robot.createScreenCapture"}

KEYLOGGER_STRINGS = {"KeyEvent", "Keyboard", "setKeyListener"}

FILE_SYSTEM_STRINGS = {"java/io/File", "FileWriter", "FileReader"}

FILE_DOWNLOAD_STRINGS = {"URL.openStream", "Files.copy"}

NATIVE_LOADER_STRINGS = {
    "System.loadLibrary", "loadLibrary",
    "java.lang.System.load", "java.lang.System.loadLibrary",
    "JNI_OnLoad",
}

DYNAMIC_LOAD_STRINGS = {
    "URLClassLoader", "defineClass",
    "sun/misc/Unsafe", "MethodHandles",
}

CRYPTO_OBF_STRINGS = {
    "Base64", "Cipher", "SecretKeySpec",
    "AES", "DES", "RC4",
    "PBKDF2WithHmacSHA", "MessageDigest", "MD5", "SHA-256",
}

NETWORK_CLASSES = {"OkHttp", "Apache HttpClient"}

NETWORK_METHODS = {"openConnection", "setRequestMethod", "setRequestProperty"}

CHEAT_SPECIFIC = {"KillAura", "Aimbot"}

OBFUSCATION_PATTERNS = {"lIlIlIlIl", "IIIIlll", "aAaAaAa"}

URL_RE = re.compile(r'https?://[^\s"]+')

TRUSTED_DOMAINS = (
    'github.com', 'githubusercontent.com', 'raw.githubusercontent.com',
    'minecraft.net', 'aka.ms', 'modrinth.com', 'curseforge.com',
    'mojang.com', 'modrinth.net',
    'login.live.com', 'user.auth.xboxlive.com', 'auth.xboxlive.com',
    'xsts.auth.xboxlive.com', 'api.minecraftservices.com', 'api.mojang.com',
)

SUSPICIOUS_DOMAINS = (
    'api.telegram.org', 't.me',
    'discord.com/api/webhooks', 'discordapp.com/api/webhooks',
    'pastebin.com', 'paste.ee', 'paste.rs', 'rentry.co', 'telegra.ph',
    'ntfy.sh', 'webhook.site', 'hookbin.com', 'requestbin.net',
    'anonfiles.com', 'file.io', 'gofile.io', 'mega.nz', 'mediafire.com',
    'ngrok.io', 'ngrok-free.app', 'localtunnel.me', 'serveo.net',
)


def entry(class_name: str, entry_type: str, detail: str) -> dict:
    return {"className": class_name or "archive", "type": entry_type, "detail": detail}


def _check_any(content: str, strings: set) -> str | None:
    lower = content.lower()
    for s in strings:
        if s in content or s.lower() in lower:
            return s
    return None


def detect_telegram(content: str, name: str, results: list[dict]) -> None:
    s = _check_any(content, TELEGRAM_STRINGS)
    if s:
        results.append(entry(name, "Telegram Logger", s))
    m = TELEGRAM_TOKEN_RE.search(content)
    if m:
        results.append(entry(name, "Telegram Token", m.group(0)))


def detect_discord(content: str, name: str, results: list[dict]) -> None:
    s = _check_any(content, DISCORD_STRINGS)
    if s:
        results.append(entry(name, "Discord Webhook", s))


def detect_password_logger(content: str, name: str, results: list[dict]) -> None:
    s = _check_any(content, PASSWORD_LOGGER_STRINGS)
    if s:
        results.append(entry(name, "Password Logger", s))


def detect_clipboard(content: str, name: str, results: list[dict]) -> None:
    for s in CLIPBOARD_STRINGS:
        if s in content:
            results.append(entry(name, "Clipboard Access", s))
            return


def detect_screenshot(content: str, name: str, results: list[dict]) -> None:
    for s in SCREENSHOT_STRINGS:
        if s in content:
            results.append(entry(name, "Screenshot Capture", s))
            return


def detect_keylogger(content: str, name: str, results: list[dict]) -> None:
    for s in KEYLOGGER_STRINGS:
        if s in content:
            results.append(entry(name, "Keylogger", s))
            return


def detect_file_system(content: str, name: str, results: list[dict]) -> None:
    s = _check_any(content, FILE_SYSTEM_STRINGS)
    if s:
        results.append(entry(name, "File System Access", s))


def detect_file_download(content: str, name: str, results: list[dict]) -> None:
    s = _check_any(content, FILE_DOWNLOAD_STRINGS)
    if s:
        results.append(entry(name, "File Download", s))


def detect_native_loader(content: str, name: str, results: list[dict]) -> None:
    s = _check_any(content, NATIVE_LOADER_STRINGS)
    if s:
        results.append(entry(name, "Native Loader", s))


def detect_dynamic_load(content: str, name: str, results: list[dict]) -> None:
    s = _check_any(content, DYNAMIC_LOAD_STRINGS)
    if s:
        results.append(entry(name, "Dynamic Loading", s))


def detect_crypto_obf(content: str, name: str, results: list[dict]) -> None:
    s = _check_any(content, CRYPTO_OBF_STRINGS)
    if s:
        results.append(entry(name, "Crypto/Obfuscation", s))


def detect_network_methods(content: str, name: str, results: list[dict]) -> None:
    for s in NETWORK_CLASSES:
        if s in content:
            results.append(entry(name, "Network Library", s))
            break
    for s in NETWORK_METHODS:
        if s in content:
            results.append(entry(name, "Network Call", s))
            break


def detect_cheat_specific(content: str, name: str, results: list[dict]) -> None:
    s = _check_any(content, CHEAT_SPECIFIC)
    if s:
        results.append(entry(name, "Cheat Signature", s))


def detect_obfuscation_details(content: str, name: str, results: list[dict]) -> None:
    for s in OBFUSCATION_PATTERNS:
        if s in content:
            results.append(entry(name, "Obfuscation Pattern", s))
            return
    if "encrypt" in content.lower() or "decrypt" in content.lower() or "flow" in content.lower():
        results.append(entry(name, "Obfuscation", "Skidfuscator-like (encrypt/decrypt/flow)"))
    elif "allatori" in content.lower() or ("invoke" in content and "reflect" in content.lower()):
        results.append(entry(name, "Obfuscation", "Allatori-like"))
    elif "Class.forName" in content or "Method.invoke" in content:
        results.append(entry(name, "Obfuscation", "Zelix-like (reflection)"))


def run_all_detections(content: str, name: str, results: list[dict]) -> None:
    detect_telegram(content, name, results)
    detect_discord(content, name, results)
    detect_password_logger(content, name, results)
    detect_clipboard(content, name, results)
    detect_screenshot(content, name, results)
    detect_keylogger(content, name, results)
    detect_file_system(content, name, results)
    detect_file_download(content, name, results)
    detect_native_loader(content, name, results)
    detect_dynamic_load(content, name, results)
    detect_crypto_obf(content, name, results)
    detect_network_methods(content, name, results)
    detect_cheat_specific(content, name, results)
    detect_obfuscation_details(content, name, results)


def extract_urls(content: str) -> list[str]:
    return list(dict.fromkeys(URL_RE.findall(content)))


def is_suspicious_url(url: str) -> bool:
    lower = url.lower()
    return any(d in lower for d in SUSPICIOUS_DOMAINS)


def is_trusted_url(url: str) -> bool:
    lower = url.lower()
    return any(d in lower for d in TRUSTED_DOMAINS)


def analyze_urls(urls: list[str]) -> dict:
    suspicious = [u for u in urls if is_suspicious_url(u)]
    untrusted = [u for u in urls if not is_trusted_url(u)]
    return {"suspicious_urls": suspicious, "untrusted_urls": untrusted, "total": len(urls)}


def calculate_risk_score(findings: list[dict]) -> int:
    types = {(e.get("type") or "").lower() for e in findings}
    score = 0
    if any("telegram" in t for t in types): score += 40
    if any("discord" in t for t in types): score += 30
    if any("dangerous" in t or "command execution" in t or t == "runtime.exec()" for t in types): score += 30
    if any("network" in t for t in types): score += 20
    if any("download" in t for t in types): score += 20
    if any("native" in t or "native loading" in t for t in types): score += 15
    if any("obfuscat" in t for t in types): score += 10
    if any("dynamic" in t for t in types): score += 10
    if any("crypto" in t for t in types): score += 5
    if any("cheat" in t for t in types): score += 10
    if any("clipboard" in t or "screenshot" in t or "keylog" in t for t in types): score += 25
    if any("password" in t for t in types): score += 20
    if any("suspicious" in t or "reflection" in t for t in types): score += 5
    return min(score, 100)
