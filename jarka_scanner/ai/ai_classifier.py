def ai_analysis(results: dict) -> dict:
    telegram = 1 if results.get('telegram_token') else 0
    discord = 1 if results.get('discord_webhook') else 0
    password = 1 if results.get('password_logger') else 0
    cheats = sum(1 for v in results.get('cheats', {}).values() if v)
    malware_probability = min(100, telegram * 50 + discord * 40 + password * 35 + cheats * 10)
    return {
        'telegram': telegram,
        'discord': discord,
        'password': password,
        'cheats': cheats,
        'malware_probability': malware_probability,
    }
