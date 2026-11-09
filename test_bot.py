"""Offline safety tests: no external requests or publishing."""
import unittest
from unittest.mock import patch
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import bot
import publish
import inspect
from PIL import Image

class BotTests(unittest.TestCase):
    def test_repeatability_and_different_designs(self):
        a=bot.concept("2026-11-08",1)
        b=bot.concept("2026-11-08",1)
        self.assertEqual(a,b)
        self.assertNotEqual(a["labels"][0],a["labels"][1])
        self.assertIn("AI-generated",a["caption"])
    def test_video_has_distinct_colors_and_locations_per_post(self):
        for slot in (1,2):
            data=bot.concept("2026-11-09",slot)
            self.assertEqual(len(data["prompts"]),2)
            self.assertIn("NO sunset",data["prompts"][0])
            self.assertIn("NO sunset",data["prompts"][1])
            colours=[next((x for x in bot.COLORS if x in prompt),None)
                     for prompt in data["prompts"]]
            places=[next((x for x in bot.PLACES if x in prompt),None)
                    for prompt in data["prompts"]]
            self.assertEqual(len(set(colours)),2)
            self.assertEqual(len(set(places)),2)
            self.assertTrue(all(x is not None for x in colours + places))
    def test_clean_frame_contains_no_rendered_typography(self):
        src = inspect.getsource(bot.slide)
        self.assertNotIn(".text(", src)
        self.assertNotIn("ImageDraw.Draw(", src)
        pure_color = (44, 66, 88)
        frame = bot.slide(Image.new("RGB", (1024,1024), pure_color), "A", 0, False)
        self.assertEqual(frame.size, (720,1280))
        self.assertEqual(frame.getpixel((360,640)), pure_color)
    def test_prompts_prohibit_all_emblems(self):
        for prompt in bot.concept("2026-11-08",1)["prompts"]:
            self.assertIn("NO invented emblem",prompt)
            self.assertIn("NO brand badge",prompt)
            self.assertIn("NO lettering",prompt)
    def test_cloudflare_requires_secrets(self):
        with patch.dict("os.environ",{},clear=True):
            with self.assertRaisesRegex(RuntimeError,"Cloudflare secrets"):
                bot.get_image("something",False,0)
    def test_demo_placeholder(self):
        im=bot.get_image("irrelevant",True,0)
        self.assertEqual(im.size,(1024,1024))
    def test_reject_demo_for_publishing(self):
        with self.assertRaisesRegex(RuntimeError,"offline demo"):
            publish.make_post_payload({"demo":True},"https://example.test/test.mp4","id","tiktok")
    def test_tiktok_channel_guard(self):
        other = {"id": "bad", "name": "othercreator", "service": "tiktok",
                 "externalLink": "https://www.tiktok.com/@othercreator",
                 "isDisconnected": False, "isLocked": False}
        ours = {"id": "ours", "name": "Seibelgram", "service": "tiktok",
                "externalLink": "https://www.tiktok.com/@seibelgram",
                "isDisconnected": False, "isLocked": False}
        self.assertFalse(publish.is_target_tiktok(other))
        self.assertTrue(publish.is_target_tiktok(ours))
        with patch.object(publish, "channels", return_value=[other]):
            with self.assertRaisesRegex(RuntimeError, "exactly one TikTok"):
                publish.verify("fake")

    def test_buffer_verification_is_read_only(self):
        ours = {"id": "ours", "name": "Seibelgram", "service": "tiktok",
                "externalLink": "https://www.tiktok.com/@seibelgram",
                "isDisconnected": False, "isLocked": False}
        with patch.object(publish, "channels", return_value=[ours]):
            self.assertEqual(publish.verify("fake"), "ours")

    def test_buffer_post_is_explicit_and_no_demo(self):
        metadata = {"demo": False, "title": "FUTURE CARS 2051",
                    "labels": ["HYPERCAR", "FUTURE WAGON"]}
        post = publish.make_post_payload(metadata, "https://example.org/car.mp4", "ours", "tiktok")
        self.assertEqual(post["metadata"]["tiktok"]["isAiGenerated"], True)
        self.assertLessEqual(len(post["text"]), 150)
        self.assertEqual(post["mode"], "addToQueue")
        with self.assertRaisesRegex(RuntimeError, "offline demo"):
            publish.make_post_payload({"demo": True}, "https://example.org/car.mp4", "ours", "tiktok")

if __name__=="__main__":unittest.main()
