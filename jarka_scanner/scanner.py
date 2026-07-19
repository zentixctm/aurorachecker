
import os
import re
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed

from .jar_extractor import list_extractable_paths, list_native_paths, list_nested_jars, read_file_from_jar
from .string_extractor import extract_strings_from_jar_file
from .detectors import stealer_detector
from .detectors import cheat_detector
from .utils.helpers import (
    extract_urls_regex,
    extract_suspicious_urls,
    calculate_risk_score,
    risk_level,
    MAX_JAR_BYTES,
)
from .ai.ai_classifier import ai_analysis

TELEGRAM_TOKEN_REGEX = re.compile(r'[0-9]{8,10}:[A-Za-z0-9_-]{35}')
MAX_NESTED_JARS = 10
MAX_NESTED_JAR_BYTES = 10 * 1024 * 1024  # 10 MB


def run_detectors(jar_path: str, file_paths: list, all_strings: dict, native_paths: list) -> dict:
    telegram = stealer_detector.check_telegram(all_strings)
    discord = stealer_detector.check_discord(all_strings)
    password_logger = stealer_detector.check_password_logger(all_strings)
    cheats = cheat_detector.check_cheats(all_strings)
    urls = []
    for strings in all_strings.values():
        for s in strings:
            urls.extend(extract_urls_regex(s))
    urls = list(dict.fromkeys(urls))
    suspicious_urls = extract_suspicious_urls(urls)
    all_evidence = []
    all_evidence.extend(telegram.get('evidence', []))
    all_evidence.extend(discord.get('evidence', []))
    all_evidence.extend(password_logger.get('evidence', []))
    for name, items in cheats.get('evidence', {}).items():
        all_evidence.extend(items)
    return {
        'telegram_token': telegram['positive'],
        'telegram_tokens': telegram.get('tokens', []),
        'discord_webhook': discord['positive'],
        'discord_matches': discord.get('matches', []),
        'password_logger': password_logger['positive'],
        'cheats': cheats.get('matches', {}),
        'evidence': all_evidence,
        'suspicious_urls': suspicious_urls,
        'urls': urls,
    }


def extract_strings_parallel(jar_path: str, file_paths: list, max_workers: int = 4) -> dict:
    """Извлечь строки из всех файлов (параллельно)."""
    all_strings = {}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_path = {
            executor.submit(extract_strings_from_jar_file, jar_path, p): p
            for p in file_paths
        }
        for future in as_completed(future_to_path):
            path = future_to_path[future]
            try:
                all_strings[path] = future.result()
            except Exception:
                all_strings[path] = []
    return all_strings


def find_finding_locations(all_strings: dict, file_paths: list, results: dict) -> dict:
    locations = {}
    PASSWORD_REGEX = re.compile(r'\b/register\b|\b/login\b')
    for path, strings in all_strings.items():
        combined = ' '.join(str(s) for s in strings)
        if results.get('telegram_token') and TELEGRAM_TOKEN_REGEX.search(combined):
            locations.setdefault('telegram_token', []).append(path)
        if results.get('discord_webhook') and any(x in combined for x in ['discord.com/api/webhooks', 'discordapp.com/api/webhooks']):
            locations.setdefault('discord_webhook', []).append(path)
        if results.get('password_logger') and PASSWORD_REGEX.search(combined):
            locations.setdefault('password_logger', []).append(path)
    return locations


def scan_jar(jar_path: str, file_size: int) -> dict:
    """Полный скан JAR. file_size в байтах."""
    if file_size > MAX_JAR_BYTES:
        return {'error': 'FILE_TOO_LARGE', 'max_mb': MAX_JAR_BYTES // (1024 * 1024)}
    file_paths = list_extractable_paths(jar_path)
    native_paths = list_native_paths(jar_path)
    if not file_paths and not native_paths:
        return {'error': 'NO_EXTRACTABLE_FILES'}
    all_strings = extract_strings_parallel(jar_path, file_paths) if file_paths else {}

    nested_jars = list_nested_jars(jar_path)
    nested_used = []
    nested_skipped = []
    for name, size in nested_jars[:MAX_NESTED_JARS * 5]:
        if len(nested_used) >= MAX_NESTED_JARS:
            nested_skipped.append(name)
            continue
        if size > MAX_NESTED_JAR_BYTES:
            nested_skipped.append(name)
            continue
        tmp_path = None
        try:
            data = read_file_from_jar(jar_path, name)
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.jar')
            tmp.write(data)
            tmp.close()
            tmp_path = tmp.name
            nested_used.append(name)
            nested_file_paths = list_extractable_paths(tmp_path)
            nested_native = list_native_paths(tmp_path)
            for p in nested_native:
                native_paths.append(f"{name}!{p}")
            if nested_file_paths:
                nested_strings = extract_strings_parallel(tmp_path, nested_file_paths)
                for p, strings in nested_strings.items():
                    all_strings[f"{name}!{p}"] = strings
        finally:
            if tmp_path:
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass

    results = run_detectors(jar_path, file_paths, all_strings, native_paths)
    results['nested_jars'] = nested_used
    results['nested_jars_skipped'] = nested_skipped
    results['locations'] = find_finding_locations(all_strings, file_paths, results)
    results['risk_score'] = calculate_risk_score(results)
    results['risk_level'] = risk_level(results['risk_score'])
    results['ai'] = ai_analysis(results)
    return results


def _paths_line(locations: dict, key: str, max_paths: int = 15) -> list:
    """Строки с путями в JAR для отчёта (для декомпилятора)."""
    out = []
    paths = locations.get(key)
    if not paths:
        return out
    unique = list(dict.fromkeys(paths))[:max_paths]
    for p in unique:
        out.append(f"  → {p}")
    if len(paths) > max_paths:
        out.append(f"  ... и ещё {len(paths) - max_paths}")
    return out


def format_report(results: dict, file_name: str = 'file.jar') -> str:
    if results.get('error'):
        return f"Error: {results['error']}\n\nFile: {file_name}"
    loc = results.get('locations', {})
    is_logger = results.get('telegram_token') or results.get('discord_webhook')
    cheats = results.get('cheats', {})
    lines = [
        "========== SCAN RESULT ==========",
        "",
        f"Telegram token: {'YES' if results.get('telegram_token') else 'NO'}",
    ]
    lines.extend(_paths_line(loc, 'telegram_token'))
    lines.append(f"Discord webhook: {'YES' if results.get('discord_webhook') else 'NO'}")
    lines.extend(_paths_line(loc, 'discord_webhook'))
    lines.append(f"Password logger: {'YES' if results.get('password_logger') else 'NO'}")
    lines.extend(_paths_line(loc, 'password_logger'))
    lines.append(f"Logger detected: {'YES' if is_logger else 'NO'}")
    lines.append("")
    lines.append("DETECTS")
    for k, v in cheats.items():
        lines.append(f"  {k}: {'YES' if v else 'NO'}")
    lines.extend([
        "",
        "RISK SCORE",
        f"{results.get('risk_score', 0)} ({results.get('risk_level', 'N/A')})",
        "",
        "AI ANALYSIS",
        f"malware probability: {results.get('ai', {}).get('malware_probability', 0)}%",
        "",
        "==================================",
    ])
    return "\n".join(lines)
