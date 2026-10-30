import unittest
import json
from pathlib import Path

from bait_names import build_index, localize_bait


class BaitNameTests(unittest.TestCase):
    def setUp(self):
        self.index = build_index({'entries': [
            {'id': 'larva', 'names': {'en': 'Cockchafer Larva', 'zh': '土蚕', 'ru': 'Личинка майского жука'}},
            {'id': 'lure', 'names': {'en': 'Orig Crank 9-006', 'zh': 'Orig Crank 9-006', 'ru': 'Orig Crank 9-006'}},
            {'id': 'product', 'names': {'en': 'Cocos & Cream 22 Pop-Up', 'zh': 'Cocos & Cream 22 Pop-Up', 'ru': None}},
        ]})

    def test_three_languages_and_original_product_name(self):
        for name in ('Cockchafer Larva', '土蚕', 'Личинка майского жука'):
            self.assertEqual(localize_bait(name, self.index), '土蚕')
        self.assertEqual(localize_bait('Orig Crank 9-006', self.index), 'Orig Crank 9-006')

    def test_sandwich_and_ampersand(self):
        self.assertEqual(localize_bait('Cockchafer Larva + Cocos & Cream 22 Pop-Up', self.index), '土蚕 + Cocos & Cream 22 Pop-Up')

    def test_no_fuzzy_product_codes(self):
        self.assertEqual(localize_bait('Orig Crank 9-003', self.index), 'Orig Crank 9-003（尚未明确）')
        self.assertEqual(localize_bait('', self.index), '尚未明确')

    def test_unicode_spacing_and_ambiguity(self):
        self.assertEqual(localize_bait('Cockchafer\u00a0Larva', self.index), '土蚕')
        with self.assertRaises(ValueError):
            build_index({'entries': [{'id': 'a', 'names': {'en': 'X'}}, {'id': 'b', 'names': {'en': 'x'}}]})

    def test_packaged_catalog_and_real_names(self):
        catalog = json.loads((Path(__file__).resolve().parents[1] / 'data/bait_names.json').read_text(encoding='utf-8'))
        index = build_index(catalog)
        ids = [e['id'] for e in catalog['entries']]
        self.assertEqual(len(ids), len(set(ids)))
        for entry in catalog['entries']:
            self.assertEqual(set(entry['names']), {'zh', 'en', 'ru'})
            if entry['names']['zh']:
                self.assertTrue(entry['sources'])
            if entry['zh_display_mode'] == 'original':
                self.assertEqual(entry['names']['zh'], entry['names']['en'])
        self.assertEqual(localize_bait('Cockchafer Larva', index), '土蚕')
        self.assertEqual(localize_bait('Orig Popper 4-F006', index), 'Orig Popper 4-F006')
        self.assertEqual(localize_bait('Foam-rubber fish 004', index), 'Foam-rubber fish 004（尚未明确）')
