import json
import os

SIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'signatures.json')


def load_sigs():
    with open(SIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def check_command_execution(all_strings: dict) -> dict:
    sigs = load_sigs().get('command_exec', {})
    strings_to_find = sigs.get('strings', [])
    combined = ' '.join(' '.join(str(s) for s in strings) for strings in all_strings.values())
    found_strings = [x for x in strings_to_find if x in combined]
    return {
        'positive': bool(found_strings),
        'runtime_exec': False,
        'process_builder': False,
    }


def check_rce(all_strings: dict) -> dict:
    return check_command_execution(all_strings)
