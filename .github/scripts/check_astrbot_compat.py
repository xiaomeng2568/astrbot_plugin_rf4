"""Check the exact upstream API surface used by this plugin; no dependencies installed."""
import ast
from concurrent.futures import ThreadPoolExecutor
from urllib.request import urlopen

BASE = 'https://raw.githubusercontent.com/AstrBotDevs/AstrBot/v4.11.0/'
EXPECTED = {
    'astrbot/api/__init__.py': {'AstrBotConfig', 'logger'},
    'astrbot/api/star/__init__.py': {'Context', 'Star'},
    'astrbot/api/event/__init__.py': {'AstrMessageEvent'},
    'astrbot/api/event/filter/__init__.py': {'command'},
    'astrbot/core/utils/astrbot_path.py': {'get_astrbot_data_path'},
}


def read(path):
    with urlopen(BASE + path, timeout=30) as response:
        return path, ast.parse(response.read().decode('utf-8'))


paths = list(EXPECTED) + ['astrbot/core/platform/astr_message_event.py', 'astrbot/core/star/__init__.py']
with ThreadPoolExecutor(max_workers=4) as pool:
    trees = dict(pool.map(read, paths))
for path, names in EXPECTED.items():
    declared = set()
    for node in ast.walk(trees[path]):
        if isinstance(node, ast.ImportFrom):
            declared.update(a.asname or a.name for a in node.names)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            declared.add(node.name)
    assert names <= declared, (path, names - declared)
event = next(n for n in trees['astrbot/core/platform/astr_message_event.py'].body if isinstance(n, ast.ClassDef) and n.name == 'AstrMessageEvent')
methods = {n.name: n for n in event.body if isinstance(n, ast.FunctionDef)}
assert [a.arg for a in methods['get_group_id'].args.args] == ['self']
assert [a.arg for a in methods['plain_result'].args.args] == ['self', 'text']
star = next(n for n in trees['astrbot/core/star/__init__.py'].body if isinstance(n, ast.ClassDef) and n.name == 'Star')
assert any(isinstance(n, ast.FunctionDef) and n.name == '__init_subclass__' for n in star.body)
print('AstrBot v4.11.0 API contract verified: imports, commands, auto-registration, paths and text replies.')
