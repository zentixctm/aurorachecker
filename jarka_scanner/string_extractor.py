# scanner/string_extractor.py
import re
import subprocess
import os
import tempfile


def extract_strings_regex(data: bytes) -> list:
    """Извлечь читаемые строки из бинарных данных через regex (ASCII/UTF-8)."""
    if not data:
        return []
    text = data.decode('utf-8', errors='ignore')
    # Последовательности печатных символов длиной от 4
    return re.findall(r'[\x20-\x7e]{4,}', text)


def extract_strings_tool(data: bytes) -> list:
    """Извлечь строки через утилиту strings если доступна (Linux/macOS)."""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.bin') as f:
            f.write(data)
            path = f.name
        result = subprocess.run(
            ['strings', path],
            capture_output=True,
            text=True,
            timeout=10
        )
        os.unlink(path)
        if result.returncode == 0 and result.stdout:
            return [s.strip() for s in result.stdout.split('\n') if len(s.strip()) >= 4]
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        pass
    return []


def extract_strings_from_jar_file(jar_path: str, member: str, use_tool: bool = False) -> list:
    """Извлечь строки из одного файла внутри JAR (например .class)."""
    from .jar_extractor import read_file_from_jar
    data = read_file_from_jar(jar_path, member)
    strings = extract_strings_regex(data)
    if use_tool and data:
        strings_tool = extract_strings_tool(data)
        strings = list(set(strings) | set(strings_tool))
    return strings


def extract_all_strings_from_jar(jar_path: str, members: list) -> dict:
    """Извлечь строки из всех переданных членов JAR. Возвращает {member: [strings]}."""
    result = {}
    for m in members:
        result[m] = extract_strings_from_jar_file(jar_path, m, use_tool=False)
    return result
