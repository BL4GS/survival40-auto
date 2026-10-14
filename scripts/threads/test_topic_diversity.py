"""No-network regression tests for Shiori's topic cooldown and safe drafts."""
import datetime as dt
import json
import unittest
from unittest.mock import patch

from scripts.threads.compose import CONFIG, SLOTS, validate_post
from scripts.threads.prepare_schedule import choose_copy
from scripts.threads.topic_diversity import (
    _pick, family_set, select_diverse_topic
)

JST=dt.timezone(dt.timedelta(hours=9))


class ShioriVarietyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config=json.loads(CONFIG.read_text(encoding="utf-8"))

    def at(self, day, hour):
        return dt.datetime(2026,10,day,hour,25,tzinfo=JST)

    def test_retire_repeated_premise_and_expand_options(self):
        groups=self.config["topic_groups"]
        self.assertNotIn("部屋着に着替えてからもう一つ用事を思い出すこと",groups["daily_routine"])
        self.assertGreaterEqual(len(groups["daily_routine"]),12)
        self.assertGreaterEqual(len(groups["movement"]),10)
        self.assertGreaterEqual(len(groups["grooming"]),15)
        self.assertEqual(len({x for v in groups.values() for x in v}),
                         sum(len(v) for v in groups.values()))

    def test_filter_identical_post_topic(self):
        group=self.config["topic_groups"]["daily_routine"]
        example="朝食の定番メニューを決めておくこと"
        alternatives=[example,"食後に少し歩くか座って休むか迷うこと"]
        got=_pick({"topic_group":"daily_routine","theme":example},
                  alternatives,[("daily_routine",example)],dt.date(2026,10,15),"morning")
        self.assertEqual(got["theme"],alternatives[1])

    def test_filter_recognizable_shared_scene_not_just_exact_text(self):
        base="帰宅後の着替えや洗顔の順番"
        alt="部屋着に着替えてからもう一つ用事を思い出すこと"
        distinct="朝食の定番メニューを決めておくこと"
        self.assertIn("着替え",family_set(base)&family_set(alt))
        got=_pick({"topic_group":"daily_routine","theme":alt},[alt,distinct],
                  [("daily_routine",base)],dt.date(2026,10,15),"evening")
        self.assertEqual(got["theme"],distinct)

    def test_approved_deterministic_topics_in_four_slots(self):
        dates=[dt.date(2026,10,15)+dt.timedelta(days=i) for i in range(14)]
        times={"morning":8,"midday":12,"afternoon":16,"evening":20}
        history=[]
        for date in dates:
            for slot in SLOTS:
                now=dt.datetime(date.year,date.month,date.day,times[slot],25,tzinfo=JST)
                v=select_diverse_topic(now,slot,self.config)
                self.assertEqual(v,select_diverse_topic(now,slot,self.config))
                self.assertIn(v["theme"],self.config["topic_groups"][v["topic_group"]])
                self.assertFalse(v["theme"] in [x for x in history[-8:]],
                                 msg=f"recent duplicate on {date} {slot}: {v['theme']}")
                history.append(v["theme"])

    def test_20h_curated_topics_stay_unmodified_by_rotation(self):
        # Approved article intros use a separate branch, no Gemini/model call.
        now=self.at(17,20)
        with patch("scripts.threads.prepare_schedule.gemini_generate") as make:
            draft=choose_copy(now,self.config,None)
            self.assertEqual(draft["kind"],"article")
            self.assertEqual(draft["id"],"2026-10-17-evening")
            self.assertIn("40s-male-yoga-mat-home-training",draft["text"])
            make.assert_not_called()

    def test_no_token_no_meta_api_and_no_artificial_extra_post(self):
        now=self.at(15,12)
        with patch("scripts.threads.prepare_schedule.gemini_generate",
                   return_value="朝食は毎回同じように見えても、温かいものにするかどうかで迷います。") as m:
            draft=choose_copy(now,self.config,"DUMMY_GEMINI_KEY")
        self.assertEqual(draft["id"],"2026-10-15-midday")
        self.assertEqual(draft["status"],"prepared_for_separate_publish_gate")
        self.assertFalse(draft["publish"])
        self.assertEqual(draft["kind"],"everyday")
        prompt=json.loads(m.call_args.args[0])
        self.assertIn(prompt["theme"],self.config["topic_groups"][prompt["topic_group"]])
        self.assertEqual(draft["text"],validate_post(draft["text"],"midday",300))

    def test_reject_out_of_scope_topic_signal(self):
        with self.assertRaises(ValueError):
            select_diverse_topic(self.at(15,20),"evening",self.config,
                                 preferred={"theme":"海外の最新ニュース","topic_group":"grooming"})
        with self.assertRaises(ValueError):
            select_diverse_topic(self.at(15,8),"invalid",self.config)


if __name__=="__main__":
    unittest.main()
