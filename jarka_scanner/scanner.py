
import os
import re
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed

from .jar_extractor import list_extractable_paths, list_native_paths, list_nested_jars, read_file_from_jar
from .string_extractor import extract_strings_from_jar_file
from .detectors import network_detector
from .detectors import stealer_detector
from .detectors import command_detector
from .detectors import cheat_detector
from .detectors import obfuscation_detector
from .utils.helpers import (
    extract_urls_regex,
    extract_suspicious_urls,
    calculate_risk_score,
    risk_level,
    MAX_JAR_BYTES,
    has_untrusted_file_urls,
    is_obfuscated_class,
)
from .ai.ai_classifier import ai_analysis

TELEGRAM_TOKEN_REGEX = re.compile(r'[0-9]{8,10}:[A-Za-z0-9_-]{35}')
MAX_NESTED_JARS = 10
MAX_NESTED_JAR_BYTES = 10 * 1024 * 1024  # 10 MB


def run_detectors(jar_path: str, file_paths: list, all_strings: dict, native_paths: list) -> dict:
    """Запуск всех детекторов."""
    network = network_detector.check_network(file_paths, all_strings)
    telegram = stealer_detector.check_telegram(all_strings)
    discord = stealer_detector.check_discord(all_strings)
    password_logger = stealer_detector.check_password_logger(all_strings)
    cmd = command_detector.check_command_execution(all_strings)
    cheats = cheat_detector.check_cheats(all_strings)
    obf = obfuscation_detector.check_obfuscation(file_paths, all_strings)
    native_loader = stealer_detector.check_native_loader(all_strings)
    dynamic_load = stealer_detector.check_dynamic_load(all_strings)
    crypto_obf = stealer_detector.check_crypto_obf(all_strings)
    urls = []
    for strings in all_strings.values():
        for s in strings:
            urls.extend(extract_urls_regex(s))
    urls = list(dict.fromkeys(urls))  # unique
    file_download = stealer_detector.check_file_download(all_strings)['positive']
    untrusted_file_url = has_untrusted_file_urls(urls, file_download)
    suspicious_urls = extract_suspicious_urls(urls)
    native_found = len(native_paths) > 0
    return {
        'telegram_token': telegram['positive'],
        'telegram_tokens': telegram.get('tokens', []),
        'discord_webhook': discord['positive'],
        'discord_matches': discord.get('matches', []),
        'password_logger': password_logger['positive'],
        'http_connection': network['positive'],
        'runtime_exec': cmd.get('runtime_exec', False),
        'process_builder': cmd.get('process_builder', False),
        'command_execution': cmd['positive'],
        'cheats': cheats.get('matches', {}),
        'obfuscation': obf['positive'],
        'native_loader': native_loader['positive'],
        'native_loader_matches': native_loader.get('matches', []),
        'dynamic_load': dynamic_load['positive'],
        'dynamic_load_matches': dynamic_load.get('matches', []),
        'crypto_obf': crypto_obf['positive'],
        'crypto_obf_matches': crypto_obf.get('matches', []),
        'file_system': stealer_detector.check_file_system(all_strings)['positive'],
        'file_download': file_download,
        'untrusted_file_url': untrusted_file_url,
        'suspicious_urls': suspicious_urls,
        'clipboard': stealer_detector.check_clipboard(all_strings)['positive'],
        'screenshot': stealer_detector.check_screenshot(all_strings)['positive'],
        'keylogger': stealer_detector.check_keylogger(all_strings)['positive'],
        'native_libs': native_found,
        'native_libs_paths': native_paths,
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
    """Для каждой находки — список путей в JAR (класс/файл для декомпилятора)."""
    locations = {}
    telegram_strs = [
        'https://api.telegram.org',
        'sendMessage',
        'chat_id',
        'mcLogger',
        'mclogger',
        'MC LOGGER',
        '@rejavastealbot',
        'rejavastealbot',
        'skr.sh/saE3s725Lnp',
    ]
    discord_strs = ['discord.com/api/webhooks', 'discordapp.com/api/webhooks', 'Java-DiscordWebhook']
    network_strs = ['openConnection', 'setRequestMethod', 'HttpURLConnection', 'URLConnection', 'java/net/URL', 'getOutputStream']
    runtime_strs = ['getRuntime', 'exec', 'Runtime', 'ProcessBuilder']
    file_download_strs = ['URL.openStream', 'FileOutputStream', 'Files.copy']
    file_system_strs = ['java/io/File', 'FileWriter', 'FileReader']
    cheat_strs = ['Hitbox', 'AxisAlignedBB', 'Reach', 'KillAura', 'Aimbot', 'ESP', 'Velocity', 'AutoClicker']
    obf_suspicious = ['lIlIlIlIl', 'IIIIlll', 'aAaAaAa']
    native_loader_strs = ['System.load', 'System.loadLibrary', 'loadLibrary', 'JNI_OnLoad']
    dynamic_load_strs = ['Class.forName', 'URLClassLoader', 'defineClass', 'Method.invoke', 'setAccessible', 'java/lang/reflect', 'sun/misc/Unsafe', 'MethodHandles']
    crypto_obf_strs = ['Base64', 'Cipher', 'SecretKeySpec', 'AES', 'DES', 'RC4', 'PBKDF2WithHmacSHA', 'MessageDigest', 'MD5', 'SHA-256']

    for path, strings in all_strings.items():
        combined = ' '.join(str(s) for s in strings)
        if results.get('telegram_token') and (any(x in combined for x in telegram_strs) or TELEGRAM_TOKEN_REGEX.search(combined)):
            locations.setdefault('telegram_token', []).append(path)
        if results.get('discord_webhook') and any(x in combined for x in discord_strs):
            locations.setdefault('discord_webhook', []).append(path)
        if results.get('http_connection') and any(x in combined for x in network_strs):
            locations.setdefault('http_connection', []).append(path)
        if results.get('runtime_exec') and any(x in combined for x in runtime_strs):
            locations.setdefault('runtime_exec', []).append(path)
        if results.get('process_builder') and 'ProcessBuilder' in combined:
            locations.setdefault('process_builder', []).append(path)
        if results.get('file_download') and any(x in combined for x in file_download_strs):
            locations.setdefault('file_download', []).append(path)
        if results.get('file_system') and any(x in combined for x in file_system_strs):
            locations.setdefault('file_system', []).append(path)
        for name in cheat_strs:
            if results.get('cheats', {}).get(name) and name in combined:
                locations.setdefault('cheats', {}).setdefault(name, []).append(path)
        if results.get('native_loader') and any(x in combined for x in native_loader_strs):
            locations.setdefault('native_loader', []).append(path)
        if results.get('dynamic_load') and any(x in combined for x in dynamic_load_strs):
            locations.setdefault('dynamic_load', []).append(path)
        if results.get('crypto_obf') and any(x in combined for x in crypto_obf_strs):
            locations.setdefault('crypto_obf', []).append(path)
    if results.get('obfuscation'):
        obf_paths = [p for p in file_paths if is_obfuscated_class(p)]
        combined_all = ' '.join(' '.join(str(s) for s in ss) for ss in all_strings.values())
        if obf_paths:
            locations['obfuscation'] = obf_paths[:50]
        elif any(x in combined_all for x in obf_suspicious):
            for path, strings in all_strings.items():
                if any(x in ' '.join(str(s) for s in strings) for x in obf_suspicious):
                    locations.setdefault('obfuscation', []).append(path)
                    if len(locations.get('obfuscation', [])) >= 50:
                        break
    if results.get('native_libs'):
        native_paths = results.get('native_libs_paths') or []
        if native_paths:
            locations['native_libs'] = native_paths[:50]
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
    """Единый отчёт для сообщения и .txt. Найден логгер — только при явных признаках. Указываются пути в JAR для декомпилятора."""
    if results.get('error'):
        return f"Ошибка: {results['error']}\n\nФайл: {file_name}"
    loc = results.get('locations', {})

    is_logger = (
        results.get('telegram_token')
        or results.get('discord_webhook')
        or results.get('untrusted_file_url')
    )
    cheats = results.get('cheats', {})
    lines = [
        "========== SCAN RESULT ==========",
        "Пути (→) — класс/файл в JAR для открытия в декомпиляторе.",
        "",
        "LOGGER",
        f"Найден логгер: {'да' if is_logger else 'нет'}",
        f"Telegram token: {'да' if results.get('telegram_token') else 'нет'}",
    ]
    lines.extend(_paths_line(loc, 'telegram_token'))
    lines.append(f"Discord webhook: {'да' if results.get('discord_webhook') else 'нет'}")
    lines.extend(_paths_line(loc, 'discord_webhook'))
    lines.append(f"Передача файлов по недоверенным ссылкам (не GitHub и т.п.): {'да' if results.get('untrusted_file_url') else 'нет'}")
    lines.extend(_paths_line(loc, 'file_download'))
    lines.extend([
        "",
        "NETWORK",
        f"HTTP requests: {'да' if results.get('http_connection') else 'нет'}",
    ])
    lines.extend(_paths_line(loc, 'http_connection'))
    lines.extend([
        "",
        "COMMAND EXECUTION",
        f"Runtime.exec: {'да' if results.get('runtime_exec') else 'нет'}",
    ])
    lines.extend(_paths_line(loc, 'runtime_exec'))
    lines.append(f"ProcessBuilder: {'да' if results.get('process_builder') else 'нет'}")
    lines.extend(_paths_line(loc, 'process_builder'))
    lines.extend([
        "",
        "CHEATS",
    ])
    for k, v in cheats.items():
        lines.append(f"- {k}: {'да' if v else 'нет'}")
        if v and isinstance(loc.get('cheats'), dict):
            for p in (loc['cheats'].get(k) or [])[:10]:
                lines.append(f"  → {p}")
    lines.extend([
        "",
        "FILESYSTEM",
        f"File access: {'да' if results.get('file_system') else 'нет'}",
    ])
    lines.extend(_paths_line(loc, 'file_system'))
    lines.extend([
        "",
        "NATIVE LIBS",
        f"Найдены нативки: {'да' if results.get('native_libs') else 'нет'}",
        "⚠ Нативные библиотеки могут скрывать вредоносный код."
    ])
    lines.extend(_paths_line(loc, 'native_libs'))
    lines.extend([
        "",
        "NATIVE LOADER",
        f"System.load/System.loadLibrary: {'да' if results.get('native_loader') else 'нет'}",
    ])
    lines.extend(_paths_line(loc, 'native_loader'))
    lines.extend([
        "",
        "DYNAMIC LOADING",
        f"ClassLoader/Reflection: {'да' if results.get('dynamic_load') else 'нет'}",
    ])
    lines.extend(_paths_line(loc, 'dynamic_load'))
    lines.extend([
        "",
        "CRYPTO / OBFUSCATION",
        f"Base64/Cipher/SecretKeySpec: {'да' if results.get('crypto_obf') else 'нет'}",
    ])
    lines.extend(_paths_line(loc, 'crypto_obf'))
    lines.extend([
        "",
        "OBFUSCATION",
        f"{'да' if results.get('obfuscation') else 'нет'}",
    ])
    lines.extend(_paths_line(loc, 'obfuscation'))
    lines.extend([
        "",
        "NESTED JARS",
        "\n".join(results.get('nested_jars', [])[:20]) or "нет",
    ])
    if results.get('nested_jars_skipped'):
        lines.extend([
            "Пропущены (слишком большие/лимит):",
            "\n".join(results.get('nested_jars_skipped', [])[:20])
        ])
    lines.extend([
        "",
        "SUSPICIOUS URLS",
        "\n".join(results.get('suspicious_urls', [])[:20]) or "нет",
        "",
        "URLS FOUND",
        "\n".join(results.get('urls', [])[:30]) or "нет",
        "",
        "AI ANALYSIS",
        f"malware probability: {results.get('ai', {}).get('malware_probability', 0)}%",
        "",
        "RISK SCORE",
        f"{results.get('risk_score', 0)} ({results.get('risk_level', 'N/A')})",
        "",
        "==================================",
    ])
    return "\n".join(lines)
