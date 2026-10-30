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
        self.assertIn("上星 尚未明确", fish_line({"name": "x"}))
        self.assertIn("分布：尚未明确", fish_line({"name": "x"}))
        self.assertIn("榜单记录：尚未明确", fish_line({"name": "x"}))
        self.assertIn("价格：尚未明确", fish_line({"name": "x"}, price=True))

    def test_fish_details_and_legacy_map(self):
        row = {"name": "欧鳊", "trophy": "4.4 kg", "blue": "7 kg",
               "weight_range": {"min": "100 g", "max": "8 kg"},
               "distribution": [{"water": "水域1", "max_weight": "8 kg"}, {"water": "水域2"}],
               "record": {"weight": "5 kg", "water": "水域1", "bait": "蚯蚓", "scope": "中国区", "checked_at": "2026-10-29"}}
        self.assertEqual(fish_line(row), "欧鳊  ⭐上星 4.4 kg  ✨蓝冠 7 kg\n重量：100 g～8 kg\n分布：水域1（最大 8 kg）\n　　　水域2（最大 尚未明确）\n榜单记录（中国区，2026-10-29）：5 kg，来自 水域1，饵料：蚯蚓")
        self.assertIn('分布：下通古斯卡河（最大 尚未明确）', fish_line(self.row))

    def test_price_is_labeled_as_estimate(self):
        result = fish_line(self.row, price=True)
        self.assertIn("9.2 银币/公斤", result)
        self.assertIn("实际售价以游戏内为准", result)
        self.assertIn("来源：测试", result)

    def test_spot_and_equipment(self):
        self.assertIn("鱼情可能变化", spot_line({"name": "x"}))
        self.assertIn("价格：尚未明确", equipment_line({"name": "竿"}))

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

    def test_search_new_distribution(self):
        row = {'name': '测试鱼', 'distribution': [{'water': '亚马河'}]}
        self.assertEqual(search({'fish': [row]}, 'fish', '亚马河'), [row])

    def test_snapshot_date_is_shown_instead_of_check_date(self):
        result = fish_line({'name': '鱼', 'record': {'weight': '1 kg', 'scope': '国际绝对榜', 'snapshot_at': '2026-10-13', 'checked_at': '2026-10-30'}})
        self.assertIn('国际绝对榜，2026-10-13', result)
        self.assertNotIn('2026-10-30', result)

    def test_snapshot_integrity(self):
        data = load_data(Path(__file__).resolve().parents[1] / 'data' / 'fish_snapshot.json')
        records = [r['record'] for r in data['fish'] if r.get('record')]
        self.assertEqual(len(records), 251)
        for record in records:
            self.assertTrue(record.get('bait'))
            self.assertTrue(record.get('water'))
            self.assertRegex(record['weight'], r'^\d+(?:\.\d+)? (?:g|kg)$')
            self.assertRegex(record['snapshot_at'], r'^2026-\d{2}-\d{2}$')
        maps = json.loads((Path(__file__).resolve().parents[1] / 'data/distribution_research.json').read_text(encoding='utf-8'))
        self.assertEqual(len(maps['maps']), 19)
        self.assertEqual(len(maps['missing_maps']), 0)

    def test_packaged_snapshot_is_attributed_and_dated(self):
        data = load_data(Path(__file__).resolve().parents[1] / 'data' / 'fish_snapshot.json')
        self.assertEqual(len(data['fish']), 251)
        names = [row['name'] for row in data['fish']]
        self.assertNotIn('小欧鳊', names)
        self.assertEqual(len(names), len(set(names)))
        unknown = {'叉牙楔齿七鳃鳗', '黑尾叉牙七鳃鳗', '雷氏七鳃鳗'}
        for row in data['fish']:
            self.assertTrue(row.get('source'))
            self.assertTrue(row.get('updated_at'))
            for field in ('trophy', 'blue'):
                value = row.get(field, '')
                if not value:
                    self.assertIn(row['name'], unknown)
                else:
                    self.assertRegex(value, r'^\d+(?:\.\d+)? (?:g|kg)$')


if __name__ == '__main__':
    unittest.main()
