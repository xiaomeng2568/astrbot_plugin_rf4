from pathlib import Path

from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star
from astrbot.api import AstrBotConfig, logger
from astrbot.core.utils.astrbot_path import get_astrbot_data_path

from .rf4 import load_data, search, fish_line, spot_line, equipment_line, web_links


class RF4Plugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config
        self.data_dir = Path(get_astrbot_data_path()) / "plugin_data" / "astrbot_plugin_rf4"

    def _lookup(self, event, category, query, renderer):
        if not self.config.get("group_enabled", True) and event.get_group_id():
            return "群聊查询已关闭。"
        if not query or not query.strip():
            return "请在指令后填写鱼名、装备名或地图名。"
        try:
            path = str(self.config.get("data_file", "")).strip()
            data = load_data(Path(path) if path else self.data_dir / "rf4_data.json")
            matches = search(data, category, query)
        except (OSError, ValueError, UnicodeError):
            logger.warning("RF4 数据文件读取失败，请检查文件格式和路径。")
            return "数据文件读取失败，请管理员检查设置。"
        if not matches:
            return "本地暂无匹配数据。\n" + web_links(query)
        return "\n\n".join(renderer(row) for row in matches)

    @filter.command("鱼线")
    async def fish(self, event: AstrMessageEvent, query: str = ""):
        """查询鱼种上星与蓝冠线。"""
        yield event.plain_result(self._lookup(event, "fish", query, fish_line))

    @filter.command("鱼价")
    async def price(self, event: AstrMessageEvent, query: str = ""):
        """查询鱼市参考价。"""
        yield event.plain_result(self._lookup(event, "fish", query, lambda row: fish_line(row, price=True)))

    @filter.command("上星")
    async def spots(self, event: AstrMessageEvent, query: str = ""):
        """查询已录入的上星记录。"""
        yield event.plain_result(self._lookup(event, "spots", query, spot_line))

    @filter.command("装备")
    async def equipment(self, event: AstrMessageEvent, query: str = ""):
        """查询已录入的装备价格。"""
        yield event.plain_result(self._lookup(event, "equipment", query, equipment_line))
