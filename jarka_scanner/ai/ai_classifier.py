# ai/ai_classifier.py
"""Простой AI-анализ: извлечь признаки и рассчитать вероятность malware."""


def ai_analysis(results: dict) -> dict:
    """Признаки: network_calls, exec_calls, telegram_strings, obfuscation_score. Итог: malware_probability %."""
    network_calls = 1 if results.get('http_connection') or results.get('file_download') else 0
    exec_calls = 1 if results.get('runtime_exec') or results.get('process_builder') else 0
    telegram_strings = 1 if results.get('telegram_token') else 0
    obfuscation_score = 1 if results.get('obfuscation') else 0
    # Веса для простой формулы
    malware_probability = min(100, (
        network_calls * 15 +
        exec_calls * 25 +
        telegram_strings * 30 +
        obfuscation_score * 10 +
        (20 if results.get('discord_webhook') else 0)
    ))
    return {
        'network_calls': network_calls,
        'exec_calls': exec_calls,
        'telegram_strings': telegram_strings,
        'obfuscation_score': obfuscation_score,
        'malware_probability': malware_probability,
    }
