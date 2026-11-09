"""Offline unit tests for SEIBELGRAM fail-closed quality checks."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image,ImageDraw
import quality_gate as qc

def synthetic(path):
    image=Image.new("RGB",(1024,1024),(42,65,92))
    draw=ImageDraw.Draw(image)
    for idx in range(30):
        x=idx*31
        draw.rectangle((x,idx*14,x+120,idx*14+120),fill=((idx*9)%255,(idx*4)%255,(idx*11)%255))
    image.save(path)

def answers():
    return {"result":{"answers":{
        "one_car":{"type":"noul","noul":.95},
        "branding":{"type":"noul","noul":.02},
        "geometry_error":{"type":"noul","noul":.07},
        "futurism":{"type":"score","score":2.7},
        "professional":{"type":"noul","noul":.94},
    }}}

class QualityTest(unittest.TestCase):
    def test_good_vision_response(self):
        ok,reasons,_=qc.assess_vision_data(answers())
        self.assertTrue(ok)
        self.assertEqual(reasons,[])
    def test_uncertain_logo_blocks_publication(self):
        result=answers()
        result["result"]["answers"]["branding"]["noul"]=.4
        ok,reasons,_=qc.assess_vision_data(result)
        self.assertFalse(ok)
        self.assertIn("branding_cannot_rule_out",reasons)
    def test_missing_vision_answers_blocks(self):
        for val in ({}, {"result":{}}, {"result":{"answers":{}}}):
            ok,_,_=qc.assess_vision_data(val)
            self.assertFalse(ok)
    def test_dedup_exact_and_reuse_in_batch(self):
        with tempfile.TemporaryDirectory() as root:
            root=Path(root)
            img=root/"a.jpg";synthetic(img)
            old=qc.fingerprint(Image.open(img))
            result=qc.technical_checks(img,[("previous-post",old)])
            self.assertFalse(result["passed"])
            self.assertIn("possible_duplicate",result["reasons"])
            self.assertEqual(result["duplicate_of"],"previous-post")
    def test_offline_cannot_approve(self):
        with tempfile.TemporaryDirectory() as root:
            root=Path(root);im=root/"new.jpg";synthetic(im)
            result=qc.run([im],root/"archive",root/"qa.json",online=False)
            self.assertFalse(result["all_approved"])
            self.assertEqual(result["items"][0]["vision"]["reasons"],["vision_not_evaluated"])
            self.assertFalse(result["automatically_published"])
    def test_vision_failure_blocks_and_does_not_post(self):
        with tempfile.TemporaryDirectory() as root:
            root=Path(root);im=root/"new.jpg";synthetic(im)
            with patch.object(qc,"vision_check",return_value=(False,["vision_api_error"],{})):
                result=qc.run([im],root/"archive",root/"qa.json",online=True)
            self.assertFalse(result["all_approved"])
            self.assertEqual(result["items"][0]["vision"]["reasons"],["vision_api_error"])
            self.assertFalse(result["automatically_published"])
    def test_bad_image_blocks_even_if_vision_would_accept(self):
        with tempfile.TemporaryDirectory() as root:
            root=Path(root);im=root/"small.jpg"
            Image.new("RGB",(64,64),(20,20,20)).save(im)
            with patch.object(qc,"vision_check",return_value=(True,[],{})) as fake:
                result=qc.run([im],root/"archive",root/"qa.json",online=True)
            self.assertFalse(result["all_approved"])
            fake.assert_not_called()

if __name__=="__main__":
    unittest.main()
