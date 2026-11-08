"""Safety tests for still-photo workflow: no overlays or accidental posting."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image
import photo_bot

class PhotoTests(unittest.TestCase):
    def test_two_distinct_concepts(self):
        a,p=photo_bot.prompts_for("2026-11-08",1)
        self.assertEqual(len(p),2)
        self.assertNotEqual(a[0][0],a[1][0])
        for prompt in p:
            self.assertIn("no logos",prompt)
            self.assertIn("no watermark",prompt)
            self.assertIn("no text",prompt)
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
            with Image.open(Path(t)/"car-1.jpg") as im:
                self.assertEqual(im.size,(1024,1024))
                self.assertEqual(im.getpixel((512,512)),(36,71,110))
    def test_post_text_not_burned_into_photos(self):
        import inspect
        s=inspect.getsource(photo_bot.run)
        self.assertNotIn("ImageDraw",s)
        self.assertNotIn("draw.text",s)

if __name__=="__main__":
    unittest.main()
