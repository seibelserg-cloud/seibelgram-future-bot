"""Offline tests for Cloudflare FLUX.2 Klein 9B Free-only photo backend."""
import base64
import io
import unittest
from unittest.mock import patch, Mock
from PIL import Image
import image_models
import photo_bot

class Flux2BackendTest(unittest.TestCase):
    def test_photo_bot_uses_new_model(self):
        self.assertIs(photo_bot.get_image,image_models.get_image)
        self.assertIn("flux-2-klein-9b",image_models.MODEL)

    def test_requires_free_credentials(self):
        with patch.dict("os.environ",{},clear=True):
            with self.assertRaisesRegex(RuntimeError,"Free credentials"):
                image_models.get_image("test",False,0)

    def test_multipart_is_required_and_image_decodes(self):
        b=io.BytesIO()
        Image.new("RGB",(1024,1024),(60,90,130)).save(b,format="PNG")
        fake=Mock()
        fake.status_code=200
        fake.json.return_value={"success":True,
            "result":{"image":base64.b64encode(b.getvalue()).decode()}}
        with patch.dict("os.environ",{"CF_ACCOUNT_ID":"test-account","CF_API_TOKEN":"test-key"},clear=True):
            with patch.object(image_models.requests,"post",return_value=fake) as post:
                image=image_models.get_image("a radical car with 4 wheels",False,0)
        self.assertEqual(image.size,(1024,1024))
        args,kwargs=post.call_args
        self.assertEqual(kwargs["files"]["width"],(None,"1024"))
        self.assertEqual(kwargs["files"]["height"],(None,"1024"))
        self.assertEqual(kwargs["files"]["prompt"],(None,"a radical car with 4 wheels"))
        self.assertNotIn("Content-Type",kwargs["headers"])
        self.assertNotIn("json",kwargs)
        self.assertTrue(args[0].endswith("flux-2-klein-9b"))

    def test_no_paid_upgrade_or_fallback_on_403(self):
        with patch.dict("os.environ",{"CF_ACCOUNT_ID":"acc","CF_API_TOKEN":"tok"},clear=True):
            with patch.object(image_models.requests,"post",return_value=Mock(status_code=403)):
                with self.assertRaisesRegex(RuntimeError,"No paid plan"):
                    image_models.get_image("future car",False,0)

    def test_retries_transient_500_exactly_once(self):
        b=io.BytesIO()
        Image.new("RGB",(1024,1024)).save(b,format="PNG")
        fail=Mock(status_code=500)
        okay=Mock(status_code=200)
        okay.json.return_value={"success":True,
            "result":{"image":base64.b64encode(b.getvalue()).decode()}}
        with patch.dict("os.environ",{"CF_ACCOUNT_ID":"acc","CF_API_TOKEN":"tok"},clear=True):
            with patch.object(image_models.requests,"post",side_effect=[fail,okay]) as send:
                with patch.object(image_models.time,"sleep"):
                    photo=image_models.get_image("radical vehicle",False,0)
        self.assertEqual(photo.size,(1024,1024))
        self.assertEqual(send.call_count,2)
    def test_overlong_prompt_fails_before_api(self):
        with patch.dict("os.environ",{"CF_ACCOUNT_ID":"acc","CF_API_TOKEN":"tok"},clear=True):
            with patch.object(image_models.requests,"post") as post:
                with self.assertRaises(ValueError):
                    image_models.get_image("X"*2050,False,0)
                post.assert_not_called()
if __name__=="__main__":
    unittest.main()
