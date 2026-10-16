import unittest
import sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R/'scripts'))
from export_data import build_status


class TestStatus(unittest.TestCase):
    def test_source_failure_is_not_reported_as_healthy(self):
        registry=[{'id':'a','organization':'A','url':'https://example.org/event'},
                  {'id':'b','organization':'B','url':'https://example.org/other'}]
        health={'a':{'status':'ok','lastCheckedAt':'2026-10-12T09:00:00+00:00'},
                'b':{'status':'not_checked','lastCheckedAt':'2026-10-12T09:01:00+00:00','reason':'Robots unavailable'}}
        result=build_status(registry,health,[],[],[])
        self.assertEqual(result['sourceSuccessCount'],1)
        self.assertEqual(result['sourceCount'],2)
        self.assertEqual(result['sources'][1]['state'],'not_checked')
        self.assertIn('Robots unavailable',result['sources'][1]['note'])

    def test_candidate_link_is_not_accepted_conference(self):
        candidates=[{'name':'Add to Calendar','year':2027,'url':'https://example.org/meet.ics'},
                    {'name':'Conference 2027','year':2027,'url':'https://example.org/conference'},
                    {'name':'Calendar dup','year':2027,'url':'https://example.org/meet.ics'},
                    {'name':'Unsafe','year':2027,'url':'javascript:alert(1)'}]
        result=build_status([],{},candidates,[],[])
        self.assertEqual(len(result['candidateLinks']),2)
        self.assertEqual(result['candidateLinks'][0]['reviewType'],'Utility or related resource')
        self.assertEqual(result['candidateLinks'][1]['reviewType'],'Potential conference link')
        self.assertNotIn('conferences',result)

if __name__=='__main__':unittest.main()
