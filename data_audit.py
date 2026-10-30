"""Report missing factual values without filling them with guessed numbers."""
import json
from pathlib import Path


def audit(data):
    fish = data['fish']
    missing = {key: [] for key in ('distribution', 'weight_min', 'weight_max', 'trophy', 'blue', 'record')}
    for row in fish:
        name = row['name']
        if not row.get('distribution') and not row.get('map'):
            missing['distribution'].append(name)
        for key in ('min', 'max'):
            if not row.get('weight_range', {}).get(key):
                missing['weight_' + key].append(name)
        for key in ('trophy', 'blue', 'record'):
            if not row.get(key):
                missing[key].append(name)
    return {'total_fish': len(fish), 'missing_counts': {k: len(v) for k, v in missing.items()}, 'missing': missing,
            'note': '有分布仅代表至少确认一个水域，不代表该鱼完整分布已核对。空值不等于零或不存在。'}


if __name__ == '__main__':
    root = Path(__file__).resolve().parent
    result = audit(json.loads((root / 'data/fish_snapshot.json').read_text(encoding='utf-8')))
    (root / 'data/missing_fields.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result['missing_counts']))
