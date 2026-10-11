"""Tests avoid network: change-monitoring only flags text changes for review."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from monitor_sources import relevant_passages,fingerprint,changed_snippets
from sync_conferences import ALLOWED,field_rules

class TestSourceWatch(unittest.TestCase):
    def test_extract_dated_proposal_paragraph(self):
        html='<html><nav>Old 2026 Deadline 12 Nov 2026</nav><p>2027 Paper submission deadline is 14 December 2026</p><footer>Copyright 2026 conference</footer></html>'
        self.assertEqual(relevant_passages(html),['2027 Paper submission deadline is 14 December 2026'])
    def test_detect_changed_deadline_without_mixing_in_nav(self):
        older=['Call for Papers closes 14 December 2026']
        newer=['Call for Papers closes 21 December 2026']
        self.assertNotEqual(fingerprint(older),fingerprint(newer))
        self.assertEqual(changed_snippets(older,newer),newer)
        self.assertEqual(changed_snippets(newer,newer),[])
    def test_reject_unrelated_aapa_domain(self):
        self.assertIn('aapa.asia',ALLOWED)
        self.assertNotIn('www.aapa.org',ALLOWED)
    def test_ecpr_two_deadline_types_are_independent(self):
        s='Call for Sections 13 October 2026 – 9 November 2026 Call for full Panels and individual Papers 17 November 2026 – 8 January 2027'
        self.assertEqual(field_rules('ecpr-gc-2027',s),{'deadline:Section':'2026-11-09','deadline:Panel / Paper':'2027-01-08'})
    def test_ipsa_explicit_paper_deadline(self):
        s='Paper and Closed Panel Submission Deadline: 4 November 2026. Conference July 2027.'
        self.assertEqual(field_rules('ipsa-2027',s),{'deadline:Paper':'2026-11-04','deadline:Closed panel':'2026-11-04'})

if __name__=='__main__':unittest.main()
