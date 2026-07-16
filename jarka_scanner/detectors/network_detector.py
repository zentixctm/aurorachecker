# detectors/network_detector.py
import re
import json
import os

SIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'signatures.json')


def load_sigs():
    with open(SIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def check_network(file_paths: list, all_strings: dict) -> dict:
    """Обнаружить сетевые вызовы: URL, URLConnection, OkHttp и т.д."""
    sigs = load_sigs().get('network', {})
    classes = sigs.get('classes', [])
    methods = sigs.get('methods', [])
    found = {'classes': [], 'methods': [], 'positive': False}
    combined = ' '.join(
        ' '.join(str(s) for s in strings)
        for strings in all_strings.values()
    )
    for c in classes:
        if c in combined or c.replace('/', '.') in combined:
            found['classes'].append(c)
    for m in methods:
        if m in combined:
            found['methods'].append(m)
    found['positive'] = bool(found['classes'] or found['methods'])
    return found
