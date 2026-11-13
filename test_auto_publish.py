"""Regression tests: scheduled TikTok delivery must never bypass QA or retry."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image

import auto_publish as ap


class SafeAutoPublishTests(unittest.TestCase):
    DAY = "2099-01-02"
    SLOT = 1

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.oldcwd = os.getcwd()
        os.chdir(self.root)
        ap.OUTPUT.mkdir()
        ap.ARCHIVE.mkdir()
        Image.new("RGB", (1024, 1024), (80, 110, 140)).save(
            ap.OUTPUT / "car-1.jpg"
        )
        Image.new("RGB", (1080, 1920), (80, 110, 140)).save(
            ap.OUTPUT / "portrait-car-1.jpg"
        )
        manifest = {
            "day": self.DAY, "slot": self.SLOT, "demo": False,
            "published": False, "generation_complete": True,
            "generation_errors": [], "approved_for_publication": False,
            "images": [{"file": "car-1.jpg",
                        "portrait_file": "portrait-car-1.jpg",
                        "concept": "MONOLITH"}],
        }
        (ap.OUTPUT / "post.json").write_text(json.dumps(manifest))
        self.report = {
            "schema_version": 1, "model": ap.EXPECTED_MODEL,
            "automatically_published": False,
            "items": [{"file": "photo_output/car-1.jpg", "passed": True,
                       "reasons": [], "approved_for_publication": True,
                       "vision": {"passed": True, "reasons": []}}],
        }
        self.write_report()

    def tearDown(self):
        os.chdir(self.oldcwd)
        self.tmp.cleanup()

    def write_report(self):
        (ap.OUTPUT / "qa-report.json").write_text(json.dumps(self.report))

    def fake_encode(self, portrait, output, style):
        self.assertTrue(Path(portrait).is_file())
        self.assertIn(style, ap.STYLES)
        Path(output).parent.mkdir(parents=True, exist_ok=True)
        Path(output).write_bytes(b"mp4-placeholder" * 3200)

    def test_unapproved_photo_cannot_be_reserved(self):
        self.report["items"][0]["vision"]["passed"] = False
        self.report["items"][0]["vision"]["reasons"] = ["branding_cannot_rule_out"]
        self.write_report()
        with patch.object(ap, "build_reel") as render:
            result = ap.prepare(self.DAY, self.SLOT)
        self.assertEqual(result["state"], "skipped")
        self.assertFalse(ap.directory(self.DAY, self.SLOT).exists())
        render.assert_not_called()

    def test_one_approved_candidate_survives_other_generation_failure(self):
        manifest = json.loads((ap.OUTPUT / "post.json").read_text())
        manifest["generation_complete"] = False
        manifest["generation_errors"] = [{"concept": "SPACE LIMO", "error": "RuntimeError"}]
        (ap.OUTPUT / "post.json").write_text(json.dumps(manifest))
        with patch.object(ap, "build_reel", side_effect=self.fake_encode):
            result = ap.prepare(self.DAY, self.SLOT)
        self.assertEqual(result["state"], "ready")
        self.assertTrue((ap.directory(self.DAY, self.SLOT) / "reservation.json").exists())

    def test_bad_or_missing_online_qa_cannot_be_reserved(self):
        self.report["model"] = None
        self.write_report()
        with self.assertRaisesRegex(RuntimeError, "Online AI visual QA"):
            ap.prepare(self.DAY, self.SLOT)

    def test_approved_photo_becomes_one_locked_video(self):
        with patch.object(ap, "build_reel", side_effect=self.fake_encode):
            result = ap.prepare(self.DAY, self.SLOT)
            duplicate = ap.prepare(self.DAY, self.SLOT)
        folder = ap.directory(self.DAY, self.SLOT)
        self.assertEqual(result["state"], "ready")
        self.assertEqual(duplicate["reason"], "slot_already_reserved")
        claim = json.loads((folder / "reservation.json").read_text())
        self.assertEqual(claim["video_sha256"], ap.sha256(folder / "future-reel.mp4"))
        self.assertEqual(claim["source_image_sha256"], ap.sha256(folder / "approved-source.jpg"))
        self.assertTrue((folder / "approved-source.jpg").is_file())
        self.assertTrue(claim["automatic_retries"] is False)
        self.assertEqual(claim["channel"], "tiktok/@seibelgram")

    def test_one_scheduled_buffer_mutation_ai_disclosure_and_no_retry(self):
        with patch.object(ap, "build_reel", side_effect=self.fake_encode):
            ap.prepare(self.DAY, self.SLOT)
        with patch.dict(os.environ, {"SEIBELGRAM_ENABLE_POSTING": "yes",
                                      "BUFFER_API_KEY": "test-key"}), \
             patch.object(ap.subprocess, "run"), \
             patch.object(ap, "ensure_public_video"), \
             patch.object(ap, "verify", return_value="tiktok-channel"), \
             patch.object(ap, "gql", return_value={
                 "createPost": {"post": {"id": "post-123", "status": "scheduled"}}
             }) as api:
            ap.post(self.DAY, self.SLOT)
            with self.assertRaisesRegex(RuntimeError, "receipt"):
                ap.post(self.DAY, self.SLOT)
            self.assertEqual(api.call_count, 1)
            payload = api.call_args[0][2]["input"]
            self.assertEqual(payload["mode"], "customScheduled")
            self.assertEqual(payload["schedulingType"], "automatic")
            self.assertEqual(payload["metadata"]["tiktok"]["isAiGenerated"], True)
            self.assertTrue(payload["assets"][0]["video"]["url"].endswith(".mp4"))
            self.assertLessEqual(len(payload["text"]), 150)

    def test_unknown_buffer_outcome_never_retries(self):
        with patch.object(ap, "build_reel", side_effect=self.fake_encode):
            ap.prepare(self.DAY, self.SLOT)
        with patch.dict(os.environ, {"SEIBELGRAM_ENABLE_POSTING": "yes",
                                      "BUFFER_API_KEY": "test-key"}), \
             patch.object(ap.subprocess, "run"), \
             patch.object(ap, "ensure_public_video"), \
             patch.object(ap, "verify", return_value="tiktok-channel"), \
             patch.object(ap, "gql", side_effect=TimeoutError("unknown")) as api:
            with self.assertRaisesRegex(RuntimeError, "Never automatically retry"):
                ap.post(self.DAY, self.SLOT)
            with self.assertRaisesRegex(RuntimeError, "receipt"):
                ap.post(self.DAY, self.SLOT)
            self.assertEqual(api.call_count, 1)
        receipt = json.loads((ap.directory(self.DAY, self.SLOT)
                              / "buffer-receipt.json").read_text())
        self.assertEqual(receipt["status"], "UNCONFIRMED")

    def test_schedule_is_berlin_local_in_winter_and_summer(self):
        winter = ap.target_time("2026-11-16", 1)
        summer = ap.target_time("2027-07-16", 1)
        self.assertEqual(winter.strftime("%H:%M"), "11:30")
        self.assertEqual(summer.strftime("%H:%M"), "10:30")
        self.assertEqual(ap.target_time("2026-11-16", 2).strftime("%H:%M"), "18:00")


if __name__ == "__main__":
    unittest.main()
