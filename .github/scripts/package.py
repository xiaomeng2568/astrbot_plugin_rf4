"""Build a release without including runtime data, credentials or git files."""
from hashlib import sha256
from pathlib import Path
import sys
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[2]
FILES = [
    'main.py', 'rf4.py', 'metadata.yaml', '_conf_schema.json',
    'README.md', 'LICENSE', 'DATA_SOURCES.md', 'data/missing_fields.json', 'data_audit.py', 'rf4_data.example.json', 'data/fish_snapshot.json',
]
version = sys.argv[1] if len(sys.argv) > 1 else 'v0.0.1-preview'
if version not in {'v0.0.1-preview', 'v0.1.0', 'v1.0.0', 'v1.0.1'} or len(sys.argv) > 2:
    raise SystemExit('unsupported version')
metadata = (ROOT / 'metadata.yaml').read_text(encoding='utf-8')
if f'version: {version}' not in metadata.splitlines():
    raise SystemExit('metadata version does not match release')
target = ROOT / 'dist' / f'astrbot_plugin_rf4-{version}.zip'
target.parent.mkdir(exist_ok=True)
with ZipFile(target, 'w', compression=ZIP_DEFLATED) as archive:
    for name in FILES:
        archive.write(ROOT / name, 'astrbot_plugin_rf4/' + name)
with ZipFile(target) as archive:
    if archive.testzip() is not None:
        raise RuntimeError('压缩包损坏')
checksum = sha256(target.read_bytes()).hexdigest()
target.with_name(target.name + '.sha256').write_text(
    f'{checksum}  {target.name}\n', encoding='ascii'
)
print(target.name, checksum)
