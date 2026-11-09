"""SEIBELGRAM music reel safety and encoding tests (no network, no uploads)."""
import shutil
import json
import subprocess
import tempfile
import unittest
import wave
from pathlib import Path
from PIL import Image, ImageDraw
import reel_from_photo as r

class ReelSoundTests(unittest.TestCase):
    def test_original_audio_is_audible_and_finite(self):
        with tempfile.TemporaryDirectory() as t:
            path=Path(t)/"sound.wav"
            r.original_soundtrack(path,seconds=1.0)
            with wave.open(str(path)) as wav:
                self.assertEqual(wav.getnchannels(),1)
                self.assertEqual(wav.getframerate(),r.RATE)
                self.assertEqual(wav.getnframes(),r.RATE)
                signal=wav.readframes(r.RATE)
            self.assertGreater(max(abs(x) for x in signal),0)
            self.assertTrue(path.stat().st_size>10_000)
    def test_distinct_original_sound_styles(self):
        with tempfile.TemporaryDirectory() as t:
            a=Path(t)/"a.wav";b=Path(t)/"b.wav"
            r.original_soundtrack(a,style="neon-pulse",seconds=.5)
            r.original_soundtrack(b,style="glacier-drive",seconds=.5)
            self.assertNotEqual(a.read_bytes(),b.read_bytes())
    def test_refuse_wrong_image_shape(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/"square.jpg"
            Image.new("RGB",(1024,1024),"orange").save(p)
            with self.assertRaisesRegex(RuntimeError,"9:16"):
                r.build(p,Path(t)/"bad.mp4")
    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),"ffmpeg unavailable")
    def test_full_reel_has_video_and_own_aac_audio(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/"photo.jpg";v=Path(t)/"reel.mp4"
            im=Image.new("RGB",(720,1280),(23,39,76))
            draw=ImageDraw.Draw(im)
            draw.polygon([(80,700),(225,590),(500,600),(630,740)],fill=(238,128,26))
            im.save(p,quality=87)
            r.build(p,v,style="deep-motion")
            result=subprocess.run(["ffprobe","-v","error","-show_entries",
                "stream=codec_type,codec_name,width,height","-of","json",str(v)],
                text=True,capture_output=True,check=True)
            streams=json.loads(result.stdout)["streams"]
            video=[x for x in streams if x["codec_type"]=="video"]
            audio=[x for x in streams if x["codec_type"]=="audio"]
            self.assertEqual(len(video),1)
            self.assertEqual(len(audio),1)
            self.assertEqual([video[0]["width"],video[0]["height"]],[720,1280])
            self.assertEqual(audio[0]["codec_name"],"aac")
            self.assertGreater(v.stat().st_size,30_000)
if __name__=="__main__":unittest.main()
