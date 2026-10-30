"""Exact lookup of source-backed game display names; never translate product codes."""
from functools import lru_cache
import json
from pathlib import Path
import re
import unicodedata

CATALOG = Path(__file__).parent / 'data' / 'bait_names.json'


def normalize(value):
    return ' '.join(unicodedata.normalize('NFKC', value).split()).casefold()


def build_index(catalog):
    index = {}
    for entry in catalog.get('entries', []):
        names = entry.get('names', {})
        for value in names.values():
            if isinstance(value, str) and value.strip():
                key = normalize(value)
                if key in index and index[key]['id'] != entry['id']:
                    raise ValueError('饵料名称存在歧义')
                index[key] = entry
    return index


@lru_cache(maxsize=1)
def _load_catalog(stamp):
    return build_index(json.loads(CATALOG.read_text(encoding='utf-8')))


def localize_bait(value, index=None):
    if not value or not str(value).strip():
        return '尚未明确'
    value = str(value).strip()
    if index is None:
        try:
            index = _load_catalog(CATALOG.stat().st_mtime_ns)
        except (OSError, ValueError, TypeError, KeyError):
            index = {}
    # A sandwich uses a separator. Ampersands inside product names stay intact.
    parts = re.split(r'\s+\+\s+', value)
    output = []
    for part in parts:
        entry = index.get(normalize(part))
        zh = entry.get('names', {}).get('zh') if entry else None
        output.append(zh if zh else f'{part}（尚未明确）')
    return ' + '.join(output)
