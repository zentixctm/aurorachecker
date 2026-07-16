# detectors/command_detector.py
import json
import os

SIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'signatures.json')


def load_sigs():
    with open(SIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def check_command_execution(all_strings: dict) -> dict:
    """Runtime.getRuntime(), exec(), ProcessBuilder, cmd, powershell, wget, curl..."""
    sigs = load_sigs().get('command_exec', {})
    classes = sigs.get('classes', [])
    methods = sigs.get('methods', [])
    strings_to_find = sigs.get('strings', [])
    combined = ' '.join(' '.join(s) for s in all_strings.values())
    found_classes = [c for c in classes if c in combined or c.replace('/', '.') in combined]
    found_methods = [m for m in methods if m in combined]
    found_strings = [x for x in strings_to_find if x in combined]
    runtime_exec = 'Runtime' in combined and ('exec' in combined or 'getRuntime' in combined)
    process_builder = 'ProcessBuilder' in combined
    return {
        'positive': bool(found_classes or found_methods or found_strings or runtime_exec or process_builder),
        'runtime_exec': runtime_exec or ('exec' in combined and 'Runtime' in combined),
        'process_builder': process_builder,
    }


def check_rce(all_strings: dict) -> dict:
    """RCE: Runtime.exec, ProcessBuilder, cmd, powershell."""
    return check_command_execution(all_strings)
