"""Offline safety tests: no external requests or publishing."""
import unittest
from unittest.mock import patch
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import bot
import publish

class BotTests(unittest.TestCase):
    def test_repeatability_and_different_designs(self):
        a=bot.concept("2026-11-08",1)
        b=bot.concept("2026-11-08",1)
        self.assertEqual(a,b)
        self.assertNotEqual(a["labels"][0],a["labels"][1])
        self.assertIn("AI-generated",a["caption"])
    def test_cloudflare_requires_secrets(self):
        with patch.dict("os.environ",{},clear=True):
            with self.assertRaisesRegex(RuntimeError,"Cloudflare secrets"):
                bot.get_image("something",False,0)
    def test_demo_placeholder(self):
        im=bot.get_image("irrelevant",True,0)
        self.assertEqual(im.size,(1024,1024))
    def test_reject_demo_for_publishing(self):
        with self.assertRaisesRegex(RuntimeError,"offline demo"):
            publish.send("fake",{"demo":True},"https://example.test/test.mp4",[("tiktok","id")])
    def test_tiktok_channel_guard(self):
        mock=[{"id":"bad","name":"othercreator","service":"tiktok","isDisconnected":False,"isLocked":False}]
        with patch.object(publish,"channels",return_value=mock), patch.dict("os.environ",{"BUFFER_CHANNEL_TIKTOK":"bad"},clear=True):
            with self.assertRaisesRegex(RuntimeError,"Unexpected TikTok"):
                publish.selected("fake")

if __name__=="__main__":unittest.main()
