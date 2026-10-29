import json
import tempfile
import unittest
from pathlib import Path

from rf4 import load_data, search, fish_line, spot_line, equipment_line, web_links


class LookupTests(unittest.TestCase):
    def setUp(self):
        self.row = {"name": "白北鲑", "aliases": ["Nelma"], "trophy": "25 kg", "blue": "30 kg", "map": "下通古斯卡河", "source": "测试", "updated_at": "2026-10-29", "prices": [{"map": "下通古斯卡河", "price": "9.2"}]}
        self.data = {"fish": [self.row], "spots": [], "equipment": []}

    def test_name_alias_and_map(self):
        for term in ("白北鲑", "nelma", "通古斯卡"):
            self.assertEqual(search(self.data, "fish", term), [self.row])
        self.assertEqual(search(self.data, "fish", ""), [])

    def test_unknown_values_are_not_zero(self):
        self.assertIn("上星：未知", fish_line({"name": "x"}))
        self.assertIn("暂无价格数据", fish_line({"name": "x"}, price=True))

    def test_price_is_labeled_as_estimate(self):
        result = fish_line(self.row, price=True)
        self.assertIn("9.2 银币/公斤", result)
        self.assertIn("实际售价以游戏内为准", result)
        self.assertIn("来源：测试", result)

    def test_spot_and_equipment(self):
        self.assertIn("鱼情可能变化", spot_line({"name": "x"}))
        self.assertIn("价格：未知", equipment_line({"name": "竿"}))

    def test_loading_utf8_bom_and_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'data.json'
            self.assertEqual(load_data(path)['fish'], [])
            path.write_text(json.dumps(self.data, ensure_ascii=False), encoding='utf-8-sig')
            self.assertEqual(load_data(path)['fish'][0]['name'], '白北鲑')

    def test_invalid_and_oversized_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'data.json'
            path.write_text('{"fish":{}}', encoding='utf-8')
            with self.assertRaises(ValueError): load_data(path)
            path.write_bytes(b' ' * (4 * 1024 * 1024 + 1))
            with self.assertRaises(ValueError): load_data(path)

    def test_limit_exact_first_and_malformed_entries(self):
        data = {'fish': [None, {'name': '白北鲑幼鱼'}, {'name': '白北鲑'}] + [{'name': '白北鲑' + str(i)} for i in range(8)]}
        result = search(data, 'fish', '白北鲑')
        self.assertEqual(result[0]['name'], '白北鲑')
        self.assertEqual(len(result), 5)

    def test_url_encoded(self):
        result = web_links('白北鲑 & x')
        self.assertNotIn('白北鲑 & x', result)
        self.assertIn('%26', result)

    def test_packaged_snapshot_is_attributed_and_dated(self):
        data = load_data(Path(__file__).resolve().parents[1] / 'data' / 'fish_snapshot.json')
        self.assertGreaterEqual(len(data['fish']), 10)
        for row in data['fish']:
            self.assertTrue(row.get('source'))
            self.assertTrue(row.get('updated_at'))
            self.assertTrue(row.get('trophy'))
            self.assertTrue(row.get('blue'))


if __name__ == '__main__':
    unittest.main()
