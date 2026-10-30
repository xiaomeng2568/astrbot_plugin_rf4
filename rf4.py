"""Offline RF4 lookups: data is user supplied, never silently invented."""
from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import quote

MAX_DATA_BYTES = 4 * 1024 * 1024
MAX_RESULTS = 5


def clean(value, limit=160):
    if value is None:
        return ""
    return " ".join(str(value).split())[:limit]


def load_data(path: Path):
    if not path.exists():
        return {"fish": [], "spots": [], "equipment": []}
    if path.stat().st_size > MAX_DATA_BYTES:
        raise ValueError("数据文件过大")
    with path.open("r", encoding="utf-8-sig") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("数据文件格式不正确")
    for key in ("fish", "spots", "equipment"):
        if not isinstance(data.get(key, []), list):
            raise ValueError("数据文件格式不正确")
    return data


def search(data, category, query):
    query = clean(query, 80).casefold()
    if not query:
        return []
    results = []
    for row in data.get(category, []):
        if not isinstance(row, dict):
            continue
        candidates = [row.get("name", ""), row.get("map", "")]
        distribution = row.get('distribution', [])
        if isinstance(distribution, list):
            candidates.extend(item.get('water', '') for item in distribution if isinstance(item, dict))
        aliases = row.get("aliases", [])
        if isinstance(aliases, list):
            candidates.extend(aliases)
        values = [clean(v, 100).casefold() for v in candidates]
        if any(query in value for value in values):
            results.append(row)
    results.sort(key=lambda row: clean(row.get("name")).casefold() != query)
    return results[:MAX_RESULTS]


def source_line(row):
    source = clean(row.get("source")) or "用户维护"
    updated = clean(row.get("updated_at"), 40) or "尚未明确"
    return f"来源：{source}；更新时间：{updated}"


def fish_line(row, price=False):
    name = clean(row.get("name")) or "未命名"
    if price:
        prices = row.get("prices", [])
        lines = [f"{name} 鱼价参考"]
        if isinstance(prices, list):
            for p in prices[:5]:
                if isinstance(p, dict):
                    lines.append(f"{clean(p.get('map')) or '未指定水域'}：{clean(p.get('price')) or '尚未明确'} {clean(p.get('unit')) or '银币/公斤'}")
        if len(lines) == 1:
            lines.append("价格：尚未明确")
        lines.extend(["价格仅供参考，实际售价以游戏内为准。", source_line(row)])
        return "\n".join(lines)
    lines = [f"{name}  ⭐上星 {clean(row.get('trophy')) or '尚未明确'}  ✨蓝冠 {clean(row.get('blue')) or '尚未明确'}"]
    weight = row.get('weight_range')
    weight = weight if isinstance(weight, dict) else {}
    minimum, maximum = clean(weight.get('min')), clean(weight.get('max'))
    weight_label = '重量（参考）' if weight.get('source') else '重量'
    lines.append(f"{weight_label}：{minimum or '尚未明确'}～{maximum or '尚未明确'}")
    distribution = row.get('distribution')
    distribution = distribution if isinstance(distribution, list) else []
    waters = []
    for item in distribution:
        if isinstance(item, dict) and clean(item.get('water')):
            waters.append(f"{clean(item.get('water'))}（最大 {clean(item.get('max_weight')) or '尚未明确'}）")
    if not waters and clean(row.get('map')):
        waters.append(f"{clean(row.get('map'))}（最大 尚未明确）")
    if waters:
        lines.append(f"分布：{waters[0]}")
        lines.extend(f"　　　{water}" for water in waters[1:])
    else:
        lines.append('分布：尚未明确')
    record = row.get('record')
    if isinstance(record, dict) and any(clean(record.get(k)) for k in ('weight', 'water', 'bait')):
        scope = clean(record.get('scope')) or '范围尚未明确'
        checked = clean(record.get('snapshot_at') or record.get('checked_at')) or '核对日期尚未明确'
        lines.append(f"榜单记录（{scope}，{checked}）：{clean(record.get('weight')) or '尚未明确'}，来自 {clean(record.get('water')) or '尚未明确'}，饵料：{clean(record.get('bait')) or '尚未明确'}")
    else:
        lines.append('榜单记录：尚未明确')
    return "\n".join(lines)


def spot_line(row):
    lines = [f"{clean(row.get('map')) or '尚未明确'} · {clean(row.get('name')) or '尚未明确鱼种'}"]
    for key, label in (("time", "记录时间"), ("bait", "饵料"), ("spot", "点位"), ("note", "说明")):
        if clean(row.get(key)):
            lines.append(f"{label}：{clean(row.get(key))}")
    lines.extend(["社区记录仅供参考，鱼情可能变化。", source_line(row)])
    return "\n".join(lines)


def equipment_line(row):
    return "\n".join([clean(row.get("name")) or "未命名装备", f"价格：{clean(row.get('price')) or '尚未明确'}", source_line(row)])


def web_links(query):
    q = quote(clean(query, 80), safe="")
    return ("数据目录： https://rf4db.com/zh/fishes\n"
            f"钓钓星蓝搜索： https://rf4.lilishare.com/index.html?search={q}\n"
            "请在网站确认当前数据。")
