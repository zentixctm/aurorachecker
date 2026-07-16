# utils/helpers.py
import re
import os

MAX_JAR_SIZE_MB = 50
MAX_JAR_BYTES = MAX_JAR_SIZE_MB * 1024 * 1024

def is_valid_jar_filename(name: str) -> bool:
    return name.lower().endswith('.jar') if name else False


def extract_urls_regex(text: str) -> list:
    """Извлечь URL по regex https?://[^\\s\"]+"""
    if not text:
        return []
    return re.findall(r'https?://[^\s"]+', text)


# Доверенные домены (не считаем передачу файлов по ним признаком логгера)
TRUSTED_DOMAINS = (
    'github.com', 'githubusercontent.com', 'raw.githubusercontent.com',
    'minecraft.net', 'aka.ms', 'modrinth.com', 'curseforge.com',
    'mojang.com', 'modrinth.net',
    'login.live.com', 'user.auth.xboxlive.com', 'auth.xboxlive.com',
    'xsts.auth.xboxlive.com', 'api.minecraftservices.com', 'api.mojang.com',
)

# Подозрительные домены/хосты, часто используемые для эксфильтрации
SUSPICIOUS_DOMAINS = (
    'api.telegram.org', 't.me',
    'discord.com/api/webhooks', 'discordapp.com/api/webhooks',
    'pastebin.com', 'paste.ee', 'paste.rs', 'rentry.co', 'telegra.ph',
    'ntfy.sh', 'webhook.site', 'hookbin.com', 'requestbin.net',
    'anonfiles.com', 'file.io', 'gofile.io', 'mega.nz', 'mediafire.com',
    'ngrok.io', 'ngrok-free.app', 'localtunnel.me', 'serveo.net',
)


def is_trusted_url(url: str) -> bool:
    """URL с доверенного домена (GitHub и т.п.)."""
    if not url:
        return True
    lower = url.lower()
    return any(d in lower for d in TRUSTED_DOMAINS)


def has_untrusted_file_urls(urls: list, file_download_detected: bool) -> bool:
    """Есть ли передача/загрузка файлов по недоверенным ссылкам."""
    if not file_download_detected or not urls:
        return False
    return any(not is_trusted_url(u) for u in urls)


def extract_suspicious_urls(urls: list) -> list:
    """Вернуть список подозрительных URL по доменам."""
    out = []
    for u in urls or []:
        lower = u.lower()
        if any(d in lower for d in SUSPICIOUS_DOMAINS):
            out.append(u)
    # unique preserve order
    seen = set()
    uniq = []
    for u in out:
        if u not in seen:
            seen.add(u)
            uniq.append(u)
    return uniq


def is_obfuscated_class(name: str) -> bool:
    """Проверка на короткие/подозрительные имена классов."""
    if not name or '/' not in name:
        return False
    class_name = name.split('/')[-1].replace('.class', '')
    if len(class_name) <= 3 and class_name.isalpha():
        return True
    suspicious = ['lIlIlIlIl', 'IIIIlll', 'aAaAaAa']
    return any(p in class_name for p in suspicious)


def calculate_risk_score(results: dict) -> int:
    """Рассчитать риск: +40 telegram, +30 discord, +30 runtime.exec, +20 http, +20 недоверенные ссылки, +15 подозрительные URL, +10 obfuscation, +10 native libs."""
    score = 0
    if results.get('telegram_token'):
        score += 40
    if results.get('discord_webhook'):
        score += 30
    if results.get('runtime_exec'):
        score += 30
    if results.get('http_connection'):
        score += 20
    if results.get('untrusted_file_url'):
        score += 20
    if results.get('suspicious_urls'):
        score += 15
    if results.get('obfuscation'):
        score += 10
    if results.get('native_libs'):
        score += 10
    return min(score, 100)


def risk_level(score: int) -> str:
    if score <= 20:
        return 'SAFE'
    if score <= 50:
        return 'SUSPICIOUS'
    return 'MALWARE'
