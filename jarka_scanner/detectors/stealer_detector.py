import re
import json
import os

SIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'signatures.json')
TELEGRAM_TOKEN_REGEX = re.compile(r'[0-9]{8,10}:[A-Za-z0-9_-]{35}')


def load_sigs():
    with open(SIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def check_telegram(all_strings: dict) -> dict:
    sigs = load_sigs().get('telegram', {})
    strings_to_find = sigs.get('strings', [])
    tokens = []
    evidence = []
    for path, lst in all_strings.items():
        for i, s in enumerate(lst):
            s_str = str(s)
            m = TELEGRAM_TOKEN_REGEX.search(s_str)
            if m:
                tokens.append(m.group(0))
                start_idx = max(0, i - 5)
                end_idx = min(len(lst), i + 5)
                context_str = "\n".join(str(lst[idx]) for idx in range(start_idx, end_idx))
                evidence.append({'file': path, 'matched': m.group(0), 'context': context_str})
    for path, lst in all_strings.items():
        combined = ' '.join(str(x) for x in lst)
        for x in strings_to_find:
            if x in combined:
                context_str = "\n".join(str(item) for item in lst[:10])
                evidence.append({'file': path, 'matched': x, 'context': context_str})
    return {'positive': bool(tokens or has_telegram_strings if False else bool(tokens or evidence)), 'tokens': tokens, 'evidence': evidence}


def check_discord(all_strings: dict) -> dict:
    sigs = load_sigs().get('discord', {})
    strings_to_find = sigs.get('strings', [])
    evidence = []
    for path, lst in all_strings.items():
        combined = ' '.join(str(x) for x in lst)
        found = [x for x in strings_to_find if x in combined]
        if found:
            context_str = "\n".join(str(item) for item in lst[:10])
            for m in found:
                evidence.append({'file': path, 'matched': m, 'context': context_str})
            return {'positive': True, 'matches': found, 'evidence': evidence}
    return {'positive': False, 'matches': [], 'evidence': []}


def check_password_logger(all_strings: dict) -> dict:
    sigs = load_sigs().get('password_logger', {})
    patterns = sigs.get('regex', [])
    compiled = [re.compile(p) for p in patterns]
    evidence = []
    for path, lst in all_strings.items():
        for i, s in enumerate(lst):
            s_str = str(s)
            for pat in compiled:
                m = pat.search(s_str)
                if m:
                    start_idx = max(0, i - 5)
                    end_idx = min(len(lst), i + 5)
                    context_str = "\n".join(str(lst[idx]) for idx in range(start_idx, end_idx))
                    evidence.append({'file': path, 'matched': m.group(0), 'context': context_str})
                    return {'positive': True, 'matches': [pat.pattern], 'evidence': evidence}
    return {'positive': False, 'matches': [], 'evidence': []}


def check_clipboard(all_strings: dict) -> dict:
    return {'positive': False, 'evidence': []}


def check_screenshot(all_strings: dict) -> dict:
    return {'positive': False, 'evidence': []}


def check_keylogger(all_strings: dict) -> dict:
    return {'positive': False, 'evidence': []}


def check_file_system(all_strings: dict) -> dict:
    return {'positive': False, 'evidence': []}


def check_file_download(all_strings: dict) -> dict:
    return {'positive': False, 'evidence': []}


def check_native_loader(all_strings: dict) -> dict:
    return {'positive': False, 'matches': [], 'evidence': []}


def check_dynamic_load(all_strings: dict) -> dict:
    return {'positive': False, 'matches': [], 'evidence': []}


def check_crypto_obf(all_strings: dict) -> dict:
    return {'positive': False, 'matches': [], 'evidence': []}
