import re
import json
import os

SIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'signatures.json')


def load_sigs():
    with open(SIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def check_obfuscation(file_paths: list, all_strings: dict) -> dict:
    return {
        'positive': False,
        'skidfuscator': False,
        'allatori': False,
        'zelix': False,
    }
