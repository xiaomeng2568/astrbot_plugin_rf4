import importlib.util
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def load_plugin(data_dir):
    modules = {name: types.ModuleType(name) for name in (
        'astrbot', 'astrbot.api', 'astrbot.api.event', 'astrbot.api.star',
        'astrbot.core', 'astrbot.core.utils', 'astrbot.core.utils.astrbot_path', 'rf4_plugin')}
    modules['rf4_plugin'].__path__ = [str(ROOT)]
    api = modules['astrbot.api']
    api.AstrBotConfig = dict
    api.logger = types.SimpleNamespace(warning=lambda *args, **kw: None)
    event = modules['astrbot.api.event']
    event.AstrMessageEvent = object
    event.filter = types.SimpleNamespace(command=lambda name: lambda fn: fn)
    star = modules['astrbot.api.star']
    star.Context = object
    star.Star = type('Star', (), {'__init__': lambda self, context: None})
    modules['astrbot.core.utils.astrbot_path'].get_astrbot_data_path = lambda: data_dir
    with patch.dict(sys.modules, modules):
        spec = importlib.util.spec_from_file_location('rf4_plugin.main', ROOT / 'main.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.RF4Plugin(None, {})


class PluginTests(unittest.IsolatedAsyncioTestCase):
    async def test_lookup_and_unknown(self):
        with tempfile.TemporaryDirectory() as tmp:
            plugin = load_plugin(tmp)
            event = types.SimpleNamespace(get_group_id=lambda: '', plain_result=lambda v: v)
            result = [x async for x in plugin.fish(event, '白北鲑')][0]
            self.assertIn('暂无匹配数据', result)
            plugin.data_dir.mkdir(parents=True)
            (plugin.data_dir / 'rf4_data.json').write_text(json.dumps({'fish': [{'name': '白北鲑', 'trophy': '25 kg'}]}, ensure_ascii=False), encoding='utf-8')
            result = [x async for x in plugin.fish(event, '白北鲑')][0]
            self.assertIn('上星：25 kg', result)
            self.assertIn('蓝冠：未知', result)

    async def test_group_disabled(self):
        with tempfile.TemporaryDirectory() as tmp:
            plugin = load_plugin(tmp)
            plugin.config['group_enabled'] = False
            event = types.SimpleNamespace(get_group_id=lambda: '123', plain_result=lambda v: v)
            result = [x async for x in plugin.price(event, '鲤鱼')][0]
            self.assertEqual(result, '群聊查询已关闭。')

    async def test_broken_data_does_not_leak_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            plugin = load_plugin(tmp)
            plugin.data_dir.mkdir(parents=True)
            (plugin.data_dir / 'rf4_data.json').write_text('not json', encoding='utf-8')
            event = types.SimpleNamespace(get_group_id=lambda: '', plain_result=lambda v: v)
            result = [x async for x in plugin.spots(event, '铜湖')][0]
            self.assertIn('读取失败', result)
            self.assertNotIn(tmp, result)


if __name__ == '__main__':
    unittest.main()
