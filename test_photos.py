"""Safety tests for still-photo workflow: no overlays or accidental posting."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image
import photo_bot
import photo_draft

class PhotoTests(unittest.TestCase):
    def test_two_distinct_concepts(self):
        a,p=photo_bot.prompts_for("2026-11-08",1)
        self.assertEqual(len(p),2)
        self.assertNotEqual(a[0][0],a[1][0])
        self.assertEqual({name for name,_ in photo_bot.THEMES},{"MONOLITH","AERO BEAST","SPACE LIMO"})
        for prompt in p:
            self.assertIn("no badges",prompt.lower())
            self.assertIn("watermark",prompt.lower())
            self.assertIn("text",prompt.lower())
            self.assertIn("not an suv",prompt.lower())
            self.assertIn("design leap",prompt.lower())
            self.assertLessEqual(len(prompt),2048)
    def test_each_theme_emerges_and_no_repeat_in_batch(self):
        seen=set()
        for day in ("2026-11-09","2026-11-10","2026-11-11","2026-11-12"):
            for slot in (1,2):
                themes,prompts=photo_bot.prompts_for(day,slot)
                labels=[x[0] for x in themes]
                self.assertEqual(len(set(labels)),2)
                self.assertEqual(len(prompts),2)
                seen.update(labels)
        self.assertEqual(seen,{"MONOLITH","AERO BEAST","SPACE LIMO"})
    def test_photo_metadata_contains_new_creative_version(self):
        with tempfile.TemporaryDirectory() as t:
            with patch.object(photo_bot,"OUT",Path(t)),patch.object(photo_bot,"get_image",
                    return_value=Image.new("RGB",(1024,1024),(40,80,120))):
                photo_bot.run("2026-11-09",1,True)
            import json
            data=json.loads((Path(t)/"post.json").read_text())
            self.assertEqual(data["creative_version"],"FUTURE-IMPOSSIBLE-01")
            self.assertFalse(data["approved_for_publication"])
            self.assertFalse(data["published"])
    def test_full_showcase_has_three_individual_concepts(self):
        themes,prompts=photo_bot.prompts_for("2026-11-09",1,showcase=True)
        self.assertEqual([x[0] for x in themes],["MONOLITH","AERO BEAST","SPACE LIMO"])
        self.assertEqual(len(prompts),3)
        self.assertEqual(len(set(prompts)),3)
        self.assertTrue(all(len(p)<=2048 for p in prompts))
    def test_generate_is_review_only_and_no_typography(self):
        with tempfile.TemporaryDirectory() as t:
            with patch.object(photo_bot,"OUT",Path(t)), patch.object(photo_bot,"get_image",
                    return_value=Image.new("RGB",(1024,1024),(36,71,110))):
                photo_bot.run("2026-11-08",1,True)
            import json
            metadata=json.loads((Path(t)/"post.json").read_text())
            self.assertTrue(metadata["requires_visual_review"])
            self.assertFalse(metadata["approved_for_publication"])
            self.assertFalse(metadata["published"])
            self.assertEqual(len(metadata["images"]),2)
            self.assertEqual(metadata["images"][0]["portrait_file"],"portrait-car-1.jpg")
            with Image.open(Path(t)/"portrait-car-1.jpg") as portrait:
                self.assertEqual(portrait.size,(1080,1920))
                self.assertTrue(all(abs(a-b)<=3 for a,b in zip(portrait.getpixel((540,960)),(36,71,110))))
            with Image.open(Path(t)/"car-1.jpg") as im:
                self.assertEqual(im.size,(1024,1024))
                self.assertTrue(all(abs(a-b) <= 3 for a,b in zip(im.getpixel((512,512)),(36,71,110))))
    def test_prompts_vary_camera_angles(self):
        _,prompts=photo_bot.prompts_for("2026-11-09",1)
        self.assertNotEqual(prompts[0],prompts[1])
        self.assertTrue(any("STRICT ORTHOGRAPHIC SIDE PROFILE" in p or "FRONT" in p or "REAR" in p for p in prompts))
    def test_9_16_frame_does_not_write_text(self):
        import inspect
        src=inspect.getsource(photo_bot.portrait_frame)
        self.assertNotIn("ImageDraw",src)
        self.assertNotIn(".text(",src)
        photo=Image.new("RGB",(1024,1024),(95,108,126))
        self.assertEqual(photo_bot.portrait_frame(photo).size,(1080,1920))
    def test_partial_cloudflare_failure_keeps_remaining_photos(self):
        with tempfile.TemporaryDirectory() as t:
            with patch.object(photo_bot,"OUT",Path(t)):
                with patch.object(photo_bot,"get_image",side_effect=[
                    RuntimeError("temporary HTTP 500"),Image.new("RGB",(1024,1024),(60,80,100))
                ]):
                    photo_bot.run("2026-11-09",1,False)
            import json
            data=json.loads((Path(t)/"post.json").read_text())
            self.assertEqual(len(data["generation_errors"]),1)
            self.assertEqual(len(data["images"]),1)
            self.assertFalse(data["generation_complete"])
            self.assertFalse(data["approved_for_publication"])
            self.assertTrue((Path(t)/"car-2.jpg").exists())
    def test_draft_payload_never_schedules_or_publishes(self):
        urls=["https://raw.githubusercontent.com/seibelserg-cloud/seibelgram-future-bot/main/photo-test/car-1.jpg"]
        payload=photo_draft.make_draft_payload("channel",urls)
        self.assertIs(payload["saveToDraft"],True)
        self.assertEqual(payload["mode"],"addToQueue")
        self.assertEqual(len(payload["assets"]),1)
        self.assertIn("AI-generated",payload["text"])
        with self.assertRaisesRegex(RuntimeError,"Unapproved photo URL"):
            photo_draft.make_draft_payload("channel",["https://other.example.com/photo.jpg"])
    def test_post_text_not_burned_into_photos(self):
        import inspect
        s=inspect.getsource(photo_bot.run)
        self.assertNotIn("ImageDraw",s)
        self.assertNotIn("draw.text",s)

if __name__=="__main__":
    unittest.main()
