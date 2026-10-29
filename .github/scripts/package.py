"""Build the preview without including runtime data, credentials or git files."""
from hashlib import sha256
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[2]
FILES = [
    'main.py', 'rf4.py', 'metadata.yaml', '_conf_schema.json',
    'README.md', 'LICENSE', 'rf4_data.example.json', 'data/fish_snapshot.json',
]
target = ROOT / 'dist' / 'astrbot_plugin_rf4-v0.0.1-preview.zip'
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
