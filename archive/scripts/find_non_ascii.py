import os
import sys

def has_non_ascii(s):
    return any(ord(c) > 127 for c in s)

root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
found = []
for dirpath, dirnames, filenames in os.walk(root):
    for fn in filenames:
        if fn.endswith(('.py', '.md', '.txt', '.json')):
            path = os.path.join(dirpath, fn)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = f.read()
            except Exception as e:
                try:
                    with open(path, 'rb') as f:
                        data = f.read().decode('utf-8', errors='ignore')
                except:
                    continue
            for i, line in enumerate(data.splitlines(), start=1):
                if has_non_ascii(line):
                    found.append((path, i, line))

if not found:
    print('OK: no non-ASCII found in scanned files')
    sys.exit(0)
for p, i, line in found:
    print(f"{p}:{i}: {line}")
sys.exit(2)
