# detectors/cheat_detector.py
import json
import os

SIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'signatures.json')


def load_sigs():
    with open(SIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def check_cheats(all_strings: dict) -> dict:
    """Hitbox, Reach, KillAura, Aimbot, ESP, Velocity, AutoClicker и т.д."""
    sigs = load_sigs().get('cheats', {})
    strings_to_find = sigs.get('strings', [])
    combined = ' '.join(' '.join(s) for s in all_strings.values())
    found = {name: name in combined for name in strings_to_find}
    return {'positive': any(found.values()), 'matches': found}
