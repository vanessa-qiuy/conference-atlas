"""Data guarantees for the self-contained city-level conference map."""
import json
import math
import unittest
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]


class TestConferenceMap(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / 'data/conferences.json').read_text(encoding='utf-8'))

    def test_valid_city_coordinates(self):
        editions = self.data['conferences']
        self.assertTrue(editions)
        self.assertEqual(len({c['id'] for c in editions}), len(editions))
        for c in editions:
            with self.subTest(conference=c['id']):
                geo = c.get('geo')
                self.assertIsInstance(geo, dict)
                self.assertEqual(geo.get('precision'), 'city')
                self.assertTrue(math.isfinite(geo['lat']))
                self.assertTrue(math.isfinite(geo['lon']))
                self.assertLessEqual(abs(geo['lat']), 90)
                self.assertLessEqual(abs(geo['lon']), 180)
                self.assertTrue(c.get('city'))
                self.assertTrue(c.get('country'))
                self.assertTrue(c.get('source', '').startswith('https://'))

    def test_bundled_map_is_standalone_svg(self):
        svg_path = ROOT / 'assets/world-map.svg'
        root = ElementTree.parse(svg_path).getroot()
        self.assertTrue(root.tag.endswith('svg'))
        self.assertEqual(root.get('viewBox'), '0 0 1200 610')
        self.assertGreater(len(svg_path.read_bytes()), 10000)


if __name__ == '__main__':
    unittest.main()
