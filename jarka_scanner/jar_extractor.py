# scanner/jar_extractor.py
import zipfile
import os
import tempfile
from pathlib import Path

EXTRACT_EXTENSIONS = {
    '.class', '.json', '.json5', '.cfg', '.txt', '.yml', '.yaml',
    '.properties', '.ini', '.xml', '.toml', '.mcmeta', '.lang',
    '.csv', '.tsv', '.md', '.log', '.js', '.lua', '.py', '.rb',
    '.kts', '.gradle', '.groovy', '.sql',
}
EXTRACT_DIRS = ('assets', 'META-INF')
NATIVE_EXTENSIONS = ('.dll', '.so', '.dylib')


def extract_jar(jar_path: str, out_dir: str = None) -> str:
    """Распаковать JAR (ZIP) во временную директорию. Возвращает путь к папке."""
    if out_dir is None:
        out_dir = tempfile.mkdtemp(prefix='jar_scan_')
    with zipfile.ZipFile(jar_path, 'r') as z:
        z.extractall(out_dir)
    return out_dir


def list_extractable_paths(jar_path: str) -> list:
    """Список путей внутри JAR для анализа: текстовые конфиги/скрипты, assets, META-INF."""
    paths = []
    with zipfile.ZipFile(jar_path, 'r') as z:
        for name in z.namelist():
            if z.getinfo(name).is_dir():
                continue
            p = Path(name)
            ext = p.suffix.lower()
            top = name.split('/')[0].lower() if '/' in name else p.parts[0].lower()
            if ext in EXTRACT_EXTENSIONS or top in EXTRACT_DIRS:
                paths.append(name)
            elif ext == '.class':
                paths.append(name)
    return paths


def list_nested_jars(jar_path: str) -> list:
    """Найти вложенные JAR в архиве. Возвращает список (name, size)."""
    items = []
    with zipfile.ZipFile(jar_path, 'r') as z:
        for info in z.infolist():
            if info.is_dir():
                continue
            if info.filename.lower().endswith('.jar'):
                items.append((info.filename, info.file_size))
    return items


def list_native_paths(jar_path: str) -> list:
    """Найти пути нативных библиотек внутри JAR (.dll/.so/.dylib)."""
    paths = []
    with zipfile.ZipFile(jar_path, 'r') as z:
        for name in z.namelist():
            if z.getinfo(name).is_dir():
                continue
            if name.lower().endswith(NATIVE_EXTENSIONS):
                paths.append(name)
    return paths


def read_file_from_jar(jar_path: str, member: str) -> bytes:
    """Прочитать содержимое файла из JAR."""
    with zipfile.ZipFile(jar_path, 'r') as z:
        return z.read(member)
