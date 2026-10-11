import json
import unittest
from datetime import date
from pathlib import Path
from urllib.parse import urlparse
R=Path(__file__).resolve().parents[1]
class TestCatalogue(unittest.TestCase):
 def test_edition_integrity_and_links(self):
  d=json.loads((R/'data/conferences.json').read_text())
  self.assertEqual(d['meta']['schemaVersion'],2)
  self.assertEqual(len(d['conferences']),21)
  for c in d['conferences']:
   with self.subTest(c=c['id']):
    self.assertEqual(c['year'],int(c['startDate'][:4]))
    self.assertLessEqual(date.fromisoformat(c['startDate']),date.fromisoformat(c['endDate']))
    self.assertTrue(c['source'].startswith('https://'))
    for v in c['deadlines']:
     self.assertLess(date.fromisoformat(v['date']),date.fromisoformat(c['startDate']))
     self.assertTrue(v['source'].startswith('https://'))
    if c['id']=='aapa-2026':self.assertEqual(urlparse(c['source']).hostname,'aapa.asia')
 def test_browser_export_keeps_all_records(self):
  s=(R/'data/conferences.js').read_text()
  self.assertTrue(s.startswith('window.ATLAS_DATA = '))
  parsed=json.loads(s[len('window.ATLAS_DATA = '):].removesuffix(';\n'))
  self.assertEqual(len(parsed['conferences']),21)
if __name__=='__main__':unittest.main()
