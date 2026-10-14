"""Offline checks for 08/12/16/20 same-hour fallback without double posting."""
from pathlib import Path
import re
import unittest
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

WORKFLOW=Path(".github/workflows/threads-drafts.yml")
# Production workflow intentionally reads vetted 104-test source, not main.
PIN="daf2610ec4b84cbc7b3ca0b17f0215a0828a611d"
WANTED=["0 23 * * *","0 3 * * *","0 7 * * *","0 11 * * *",
        "20 23 * * *","20 3 * * *","20 7 * * *","20 11 * * *"]


class FallbackWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.text=WORKFLOW.read_text(encoding="utf-8")

    def test_four_primary_four_fallback_no_extra_hours(self):
        actual=re.findall(r"^\s+- cron: '([^']+)'",self.text,re.M)
        self.assertEqual(actual,WANTED)
        jst=timezone(timedelta(hours=9))
        times=set()
        for expr in actual:
            minute,hour,_,_,_=expr.split()
            dt=datetime(2026,10,15,int(hour),int(minute),tzinfo=timezone.utc).astimezone(jst)
            times.add((dt.hour,dt.minute))
        self.assertEqual(times,{(8,0),(8,20),(12,0),(12,20),
                                (16,0),(16,20),(20,0),(20,20)})

    def test_publisher_still_exact_same_pinned_source(self):
        self.assertEqual(re.findall(r"^\s+ref: ([0-9a-f]{40})",self.text,re.M),[PIN])
        self.assertIn("python3 -m scripts.threads.scheduled_publisher",self.text)
        self.assertIn("python3 -m scripts.threads.prepare_schedule",self.text)
        self.assertIn("if: github.event_name == 'schedule'",self.text)
        self.assertIn("group: survival40-threads-live",self.text)
        self.assertIn("cancel-in-progress: false",self.text)
        self.assertIn("ref: ",self.text)
        self.assertIn("THREADS_ACCESS_TOKEN: ''",self.text)

    def test_no_alternative_publishing_mechanism_or_meta_copy(self):
        self.assertEqual(self.text.count("python3 -m scripts.threads.scheduled_publisher"),1)
        self.assertEqual(self.text.count("threads-output/draft.json"),1)
        self.assertNotIn("workflow_run:",self.text)
        self.assertNotIn("repository_dispatch:",self.text)
        self.assertIn("permissions:\n  contents: write",self.text)

if __name__=="__main__":
    unittest.main()
