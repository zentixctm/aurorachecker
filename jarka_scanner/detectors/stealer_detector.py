# detectors/stealer_detector.py
import re
import json
import os

SIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'signatures.json')
TELEGRAM_TOKEN_REGEX = re.compile(r'[0-9]{8,10}:[A-Za-z0-9_-]{35}')


def load_sigs():
    with open(SIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def check_telegram(all_strings: dict) -> dict:
    """Telegram logger: api.telegram.org, sendMessage, chat_id, bot, токен."""
    sigs = load_sigs().get('telegram', {})
    strings_to_find = sigs.get('strings', [])
    tokens = []
    combined = ' '.join(' '.join(s) for s in all_strings.values())
    for s in strings_to_find:
        if s in combined:
            pass  # будем считать по токенам и строкам
    for lst in all_strings.values():
        for s in lst:
            m = TELEGRAM_TOKEN_REGEX.search(s)
            if m:
                tokens.append(m.group(0))
    has_telegram_strings = any(
        any(x in ' '.join(lst) for x in strings_to_find)
        for lst in all_strings.values()
    )
    return {'positive': bool(tokens or has_telegram_strings), 'tokens': tokens}


def check_discord(all_strings: dict) -> dict:
    """Discord logger: webhooks."""
    sigs = load_sigs().get('discord', {})
    strings_to_find = sigs.get('strings', [])
    combined = ' '.join(' '.join(s) for s in all_strings.values())
    found = [x for x in strings_to_find if x in combined]
    return {'positive': len(found) > 0, 'matches': found}


def check_password_logger(all_strings: dict) -> dict:
    """Minecraft password logger: /reg, /register, /login, /l."""
    sigs = load_sigs().get('password_logger', {})
    strings_to_find = sigs.get('strings', [])
    combined = ' '.join(' '.join(s) for s in all_strings.values())
    found = [x for x in strings_to_find if x in combined]
    return {'positive': len(found) > 0, 'matches': found}


def check_clipboard(all_strings: dict) -> dict:
    """Clipboard stealer."""
    sigs = load_sigs().get('clipboard', {})
    strings_to_find = sigs.get('strings', [])
    combined = ' '.join(' '.join(s) for s in all_strings.values())
    found = [x for x in strings_to_find if x in combined]
    return {'positive': len(found) > 0}


def check_screenshot(all_strings: dict) -> dict:
    """Screenshot stealer."""
    sigs = load_sigs().get('screenshot', {})
    strings_to_find = sigs.get('strings', [])
    combined = ' '.join(' '.join(s) for s in all_strings.values())
    found = [x for x in strings_to_find if x in combined]
    return {'positive': len(found) > 0}


def check_keylogger(all_strings: dict) -> dict:
    """Keylogger."""
    sigs = load_sigs().get('keylogger', {})
    strings_to_find = sigs.get('strings', [])
    combined = ' '.join(' '.join(s) for s in all_strings.values())
    found = [x for x in strings_to_find if x in combined]
    return {'positive': len(found) > 0}


def check_file_system(all_strings: dict) -> dict:
    """File system access."""
    sigs = load_sigs().get('file_system', {})
    strings_to_find = sigs.get('strings', [])
    combined = ' '.join(' '.join(s) for s in all_strings.values())
    found = [x for x in strings_to_find if x in combined]
    return {'positive': len(found) > 0}


def check_file_download(all_strings: dict) -> dict:
    """File download (URL.openStream и т.д.)."""
    sigs = load_sigs().get('file_download', {})
    strings_to_find = sigs.get('strings', [])
    combined = ' '.join(' '.join(s) for s in all_strings.values())
    found = [x for x in strings_to_find if x in combined]
    return {'positive': len(found) > 0}


def check_native_loader(all_strings: dict) -> dict:
    """System.load/System.loadLibrary и т.п. (загрузка нативных библиотек)."""
    sigs = load_sigs().get('native_loader', {})
    strings_to_find = sigs.get('strings', [])
    combined = ' '.join(' '.join(s) for s in all_strings.values())
    found = [x for x in strings_to_find if x in combined]
    return {'positive': len(found) > 0, 'matches': found}


def check_dynamic_load(all_strings: dict) -> dict:
    """Динамическая загрузка классов/рефлексия."""
    sigs = load_sigs().get('dynamic_load', {})
    strings_to_find = sigs.get('strings', [])
    combined = ' '.join(' '.join(s) for s in all_strings.values())
    found = [x for x in strings_to_find if x in combined]
    return {'positive': len(found) > 0, 'matches': found}


def check_crypto_obf(all_strings: dict) -> dict:
    """Признаки шифрования/обфускации строк (Base64/Cipher/SecretKeySpec)."""
    sigs = load_sigs().get('crypto_obf', {})
    strings_to_find = sigs.get('strings', [])
    combined = ' '.join(' '.join(s) for s in all_strings.values())
    found = [x for x in strings_to_find if x in combined]
    return {'positive': len(found) > 0, 'matches': found}
