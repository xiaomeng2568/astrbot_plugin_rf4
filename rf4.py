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
    updated = clean(row.get("updated_at"), 40) or "未填写"
    return f"来源：{source}；更新时间：{updated}"


def fish_line(row, price=False):
    name = clean(row.get("name")) or "未命名"
    if price:
        prices = row.get("prices", [])
        lines = [f"{name} 鱼价参考"]
        if isinstance(prices, list):
            for p in prices[:5]:
                if isinstance(p, dict):
                    lines.append(f"{clean(p.get('map')) or '未指定水域'}：{clean(p.get('price')) or '未知'} {clean(p.get('unit')) or '银币/公斤'}")
        if len(lines) == 1:
            lines.append("暂无价格数据")
        lines.extend(["价格仅供参考，实际售价以游戏内为准。", source_line(row)])
        return "\n".join(lines)
    lines = [name, f"上星：{clean(row.get('trophy')) or '未知'}", f"蓝冠：{clean(row.get('blue')) or '未知'}"]
    if clean(row.get('map')):
        lines.append(f"水域：{clean(row.get('map'))}")
    lines.append(source_line(row))
    return "\n".join(lines)


def spot_line(row):
    lines = [f"{clean(row.get('map')) or '未知水域'} · {clean(row.get('name')) or '未知鱼种'}"]
    for key, label in (("time", "记录时间"), ("bait", "饵料"), ("spot", "点位"), ("note", "说明")):
        if clean(row.get(key)):
            lines.append(f"{label}：{clean(row.get(key))}")
    lines.extend(["社区记录仅供参考，鱼情可能变化。", source_line(row)])
    return "\n".join(lines)


def equipment_line(row):
    return "\n".join([clean(row.get("name")) or "未命名装备", f"价格：{clean(row.get('price')) or '未知'}", source_line(row)])


def web_links(query):
    q = quote(clean(query, 80), safe="")
    return ("数据目录： https://rf4db.com/zh/fishes\n"
            f"钓钓星蓝搜索： https://rf4.lilishare.com/index.html?search={q}\n"
            "请在网站确认当前数据。")
