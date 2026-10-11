import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from sync_conferences import parse_date, field_rules, normalized_text, apply_updates

class TestParsing(unittest.TestCase):
    def test_date_languages(self):
        self.assertEqual(parse_date('18th October 2026'),'2026-10-18')
        self.assertEqual(parse_date('October 18, 2026'),'2026-10-18')
        self.assertIsNone(parse_date('October 40 2026'))
    def test_irspm_explicit(self):
        text=normalized_text('<p>Call for Abstracts 2027 will close on Sunday, October 18, 2026 (midnight CEST).</p>')
        self.assertEqual(field_rules('irspm-2027',text)['deadline:Abstract'],'2026-10-18')
    def test_icpp_panels_and_papers(self):
        text='Call for panels 3rd September 2026 - 26th October 2026 Ongoing. Call for papers 16th November 2026 - 29th January 2027 Upcoming. Registration 16th February 2027 - 5th July 2027.'
        self.assertEqual(field_rules('icpp8-2027',text),{'deadline:Panel':'2026-10-26','deadline:Paper':'2027-01-29','registration:closes':'2027-07-05'})
    def test_iaia_anchors(self):
        text='2 November 2026: Deadline for submission of paper or poster abstract. 13 January 2027: Presenter registration deadline & early bird rate deadline. 31 March 2027: Final registration & payment deadline for regular attendees.'
        actual=field_rules('iaia-2027',text)
        self.assertEqual(actual,{'deadline:Abstract':'2026-11-02','registration:earlyBird':'2027-01-13','registration:closes':'2027-03-31'})
    def test_large_change_queued(self):
        c={'id':'irspm-2027','source':'https://www.irspm.org','deadlines':[{'type':'Abstract','date':'2026-10-18'}]}
        changed=[]; pending=[]
        apply_updates(c,{'deadline:Abstract':'2027-10-18'},'2026-10-11',changed,pending)
        self.assertEqual(c['deadlines'][0]['date'],'2026-10-18')
        self.assertEqual(len(pending),1)
    def test_reasonable_change_applied(self):
        c={'id':'irspm-2027','source':'https://www.irspm.org','deadlines':[{'type':'Abstract','date':'2026-10-18'}]}
        changed=[]; pending=[]
        apply_updates(c,{'deadline:Abstract':'2026-10-27'},'2026-10-11',changed,pending)
        self.assertEqual(c['deadlines'][0]['date'],'2026-10-27')
        self.assertEqual(len(changed),1)

if __name__=='__main__':unittest.main()
