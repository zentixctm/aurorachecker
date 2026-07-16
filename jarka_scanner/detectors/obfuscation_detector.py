# detectors/obfuscation_detector.py
import re
import json
import os
from ..utils.helpers import is_obfuscated_class

SIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'signatures.json')


def load_sigs():
    with open(SIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def check_obfuscation(file_paths: list, all_strings: dict) -> dict:
    """Короткие имена классов, подозрительные паттерны, признаки Skidfuscator/Allatori/Zelix."""
    sigs = load_sigs().get('obfuscation', {})
    suspicious = sigs.get('suspicious_patterns', [])
    combined = ' '.join(' '.join(s) for s in all_strings.values())
    short_or_suspicious = any(is_obfuscated_class(p) for p in file_paths)
    suspicious_strings = [x for x in suspicious if x in combined]
    # Skidfuscator: random class names, string encryption, control flow
    skid = 'encrypt' in combined.lower() or 'decrypt' in combined.lower() or 'flow' in combined.lower()
    # Allatori: encrypted strings, short method names
    allatori = 'allatori' in combined.lower() or ('invoke' in combined and 'reflect' in combined.lower())
    # Zelix: heavy string encryption, Class.forName, Method.invoke
    zelix = 'Class.forName' in combined or 'Method.invoke' in combined
    return {
        'positive': short_or_suspicious or len(suspicious_strings) > 0 or skid or allatori or zelix,
        'skidfuscator': skid,
        'allatori': allatori,
        'zelix': zelix,
    }
