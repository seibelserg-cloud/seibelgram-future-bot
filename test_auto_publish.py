"""Offline tests for publish-first SEIBELGRAM: no subjective image QA gate.

Never contacts TikTok/Buffer or pays for an image-model request.
"""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image

import auto_publish as ap


class PublishFirstTests(unittest.TestCase):
    DAY = "2099-01-02"

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.oldcwd = os.getcwd()
        os.chdir(self.tmp.name)
        ap.OUTPUT.mkdir()
        ap.ARCHIVE.mkdir()
        Image.new("RGB", (1024, 1024), (80, 110, 140)).save(ap.OUTPUT / "car-1.jpg")
        Image.new("RGB", (1080, 1920), (80, 110, 140)).save(
            ap.OUTPUT / "portrait-car-1.jpg")
        self.manifest = {
            "day": self.DAY, "slot": 1, "demo": False,
            "published": False, "generation_complete": True, "generation_errors": [],
            "approved_for_publication": False, "images": [
                {"file": "car-1.jpg", "portrait_file": "portrait-car-1.jpg",
                 "concept": "MONOLITH"}
            ],
        }
        self.write_manifest()

    def tearDown(self):
        os.chdir(self.oldcwd)
        self.tmp.cleanup()

    def write_manifest(self):
        (ap.OUTPUT / "post.json").write_text(json.dumps(self.manifest))

    def fake_encode(self, image, output, style):
        self.assertTrue(Path(image).is_file())
        self.assertIn(style, ap.STYLES)
        Path(output).parent.mkdir(parents=True, exist_ok=True)
        Path(output).write_bytes(b"original-encoded-mp4-test" * 2500)

    def prepare(self, slot=1):
        with patch.object(ap, "build_reel", side_effect=self.fake_encode):
            return ap.prepare(self.DAY, slot)

    def test_no_ai_qa_report_required(self):
        self.assertFalse((ap.OUTPUT / "qa-report.json").exists())
        result = self.prepare()
        self.assertEqual(result["state"], "ready")
        claim = json.loads((ap.directory(self.DAY, 1) / "reservation.json").read_text())
        self.assertEqual(claim["visual_qa_required"], False)

    def test_negative_ai_review_does_not_block_publishing(self):
        (ap.OUTPUT / "qa-report.json").write_text(json.dumps({
            "model": "@cf/cloudflare/clef", "all_approved": False,
            "items": [{"approved_for_publication": False,
                       "vision": {"reasons": ["geometry_error_cannot_rule_out"]}}],
        }))
        self.assertEqual(self.prepare()["state"], "ready")

    def test_missing_generation_is_safe_skip(self):
        self.manifest["images"] = []
        self.write_manifest()
        with patch.object(ap, "build_reel") as encoder:
            result = ap.prepare(self.DAY, 1)
        self.assertEqual(result["reason"], "no_valid_nonduplicate_image_generated")
        encoder.assert_not_called()

    def test_corrupted_photo_cannot_be_encoded(self):
        (ap.OUTPUT / "car-1.jpg").write_bytes(b"invalid-jpg" * 5000)
        self.assertEqual(self.prepare()["state"], "skipped")

    def test_broken_portrait_cannot_be_encoded(self):
        Image.new("RGB", (128, 128), (30, 30, 30)).save(
            ap.OUTPUT / "portrait-car-1.jpg")
        self.assertEqual(self.prepare()["state"], "skipped")

    def test_existing_identical_source_does_not_repost(self):
        previous = ap.ARCHIVE / "2026-11-09" / "slot-1"
        previous.mkdir(parents=True)
        (previous / "approved-source.jpg").write_bytes(
            (ap.OUTPUT / "car-1.jpg").read_bytes())
        self.assertEqual(self.prepare()["reason"], "no_valid_nonduplicate_image_generated")

    def test_partial_generation_uses_valid_candidate(self):
        self.manifest["generation_complete"] = False
        self.manifest["generation_errors"] = [{"concept": "SPACE LIMO",
                                               "error": "RuntimeError"}]
        self.write_manifest()
        self.assertEqual(self.prepare()["state"], "ready")

    def test_preview_mode_cannot_be_published(self):
        self.manifest["demo"] = True
        self.write_manifest()
        with self.assertRaisesRegex(RuntimeError, "Demo"):
            self.prepare()

    def test_mismatched_slot_cannot_be_published(self):
        self.manifest["slot"] = 2
        self.write_manifest()
        with self.assertRaisesRegex(RuntimeError, "different day or publishing slot"):
            self.prepare()

    def test_reserved_video_and_original_saved_once(self):
        first = self.prepare()
        again = self.prepare()
        folder = ap.directory(self.DAY, 1)
        self.assertEqual(first["state"], "ready")
        self.assertEqual(again["reason"], "slot_already_reserved")
        claim = json.loads((folder / "reservation.json").read_text())
        self.assertEqual(claim["source_image_sha256"], ap.sha256(folder / "approved-source.jpg"))
        self.assertEqual(claim["video_sha256"], ap.sha256(folder / "future-reel.mp4"))
        self.assertEqual(claim["channel"], "tiktok/@seibelgram")
        self.assertIs(claim["automatic_retries"], False)

    def test_evening_does_not_overwrite_morning_post(self):
        self.prepare()
        result = self.prepare(2)
        self.assertEqual(result["reason"], "daily_post_already_reserved")
        self.assertFalse(ap.directory(self.DAY, 2).exists())
        with patch.dict(os.environ, {"SEIBELGRAM_ENABLE_POSTING": "yes"}):
            with self.assertRaisesRegex(RuntimeError, "Daily TikTok post already reserved"):
                ap.post(self.DAY, 2)

    def test_evening_can_post_if_morning_generation_failed(self):
        self.manifest["images"] = []
        self.write_manifest()
        self.assertEqual(self.prepare()["state"], "skipped")
        self.manifest["images"] = [
            {"file": "car-1.jpg", "portrait_file": "portrait-car-1.jpg",
             "concept": "MONOLITH"}]
        self.manifest["slot"] = 2
        self.write_manifest()
        self.assertEqual(self.prepare(2)["state"], "ready")

    def test_one_scheduled_buffer_call_with_ai_disclosure(self):
        self.prepare()
        with patch.dict(os.environ, {"SEIBELGRAM_ENABLE_POSTING": "yes",
                                      "BUFFER_API_KEY": "fake-key"}), \
             patch.object(ap.subprocess, "run"), \
             patch.object(ap, "ensure_public_video"), \
             patch.object(ap, "verify", return_value="target-tiktok"), \
             patch.object(ap, "gql", return_value={
                 "createPost": {"post": {"id": "post-123", "status": "scheduled"}}
             }) as api:
            ap.post(self.DAY, 1)
            with self.assertRaisesRegex(RuntimeError, "receipt"):
                ap.post(self.DAY, 1)
            self.assertEqual(api.call_count, 1)
            payload = api.call_args[0][2]["input"]
            self.assertEqual(payload["mode"], "customScheduled")
            self.assertEqual(payload["schedulingType"], "automatic")
            self.assertEqual(payload["metadata"]["tiktok"]["isAiGenerated"], True)
            self.assertTrue(payload["assets"][0]["video"]["url"].endswith(".mp4"))

    def test_unknown_api_result_cannot_retry(self):
        self.prepare()
        with patch.dict(os.environ, {"SEIBELGRAM_ENABLE_POSTING": "yes",
                                      "BUFFER_API_KEY": "fake-key"}), \
             patch.object(ap.subprocess, "run"), \
             patch.object(ap, "ensure_public_video"), \
             patch.object(ap, "verify", return_value="target-tiktok"), \
             patch.object(ap, "gql", side_effect=TimeoutError("uncertain")) as api:
            with self.assertRaisesRegex(RuntimeError, "Never automatically retry"):
                ap.post(self.DAY, 1)
            with self.assertRaisesRegex(RuntimeError, "receipt"):
                ap.post(self.DAY, 1)
            self.assertEqual(api.call_count, 1)

    def test_dst_berlin_time_target(self):
        self.assertEqual(ap.target_time("2026-11-16", 1).strftime("%H:%M"), "11:30")
        self.assertEqual(ap.target_time("2027-07-16", 1).strftime("%H:%M"), "10:30")
        self.assertEqual(ap.target_time("2026-11-16", 2).strftime("%H:%M"), "18:00")


if __name__ == "__main__":
    unittest.main()
