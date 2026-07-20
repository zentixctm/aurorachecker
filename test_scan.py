import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from jarka_scanner.scanner import scan_jar
import os

jar_path = r'C:\Users\Admin\Downloads\phantom-4.0.4.jar'
size = os.path.getsize(jar_path)
results = scan_jar(jar_path, size)

cheats = results.get('cheats', {})
found = {k: v for k, v in cheats.items() if v}
print(f'cheats found: {found}')
print(f'evidence:')
for item in results.get('evidence', []):
    print(f'  {item["file"]} -> {item["matched"]}: {item.get("context", "")[:120]}')
print(f'risk_score: {results.get("risk_score")} ({results.get("risk_level")})')
