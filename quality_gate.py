#!/usr/bin/env python3
"""SEIBELGRAM image QA: hard technical checks + optional vision model.

Fail closed: missing AI result, model error, uncertain verdict, a duplicate,
or an unapproved photo never triggers publishing. This script cannot publish.
"""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
from PIL import Image, ImageStat, ImageOps
import requests

VISION_MODEL="@cf/cloudflare/clef"
MIN_SIDE=512
MAX_BYTES=5_000_000
DUPLICATE_THRESHOLD=13
DEFAULT_ARCHIVE=Path("content")

QUESTIONS={
    "one_car":{"type":"noul",
        "instructions":"Does the image clearly show exactly ONE complete recognizable futuristic automobile, no collage or multiple cars? Answer no if cropped or ambiguous."},
    "branding":{"type":"noul",
        "instructions":"Does the image show ANY visual lettering, typographic text, manufacturer logo, fake brand badge, emblem, crest, symbol, hubcap marking, licence plate, or watermark on the car or the scene? If uncertain, answer yes."},
    "geometry_error":{"type":"noul",
        "instructions":"Are there obvious structural CGI errors such as more than four wheels, mismatched wheel geometry, wheels melting into body, impossible body connections or deformed anatomy of the car? If uncertain, answer yes."},
    "futurism":{"type":"score",
        "instructions":"How original and distinctly futuristic is this car compared with 2025 production SUVs and sports cars? Prioritize credible striking automotive industrial design, not superficial LED lighting.",
        "criteria":["Ordinary modern production car","Mildly futuristic facelift","Distinctive believable future concept","Extraordinary novel futuristic car design"]},
    "professional":{"type":"noul",
        "instructions":"Is the image technically crisp, coherent, clean, professionally lit and visually suitable for a premium futuristic automotive CGI social account? Answer no if blurry, posterized, badly framed, low detail or crude."}
}

def fingerprint(image):
    """16x16 difference hash, integer, not a trained perceptual similarity metric."""
    x=ImageOps.grayscale(image).resize((17,16),Image.Resampling.LANCZOS)
    b=list(x.getdata())
    value=0
    for y in range(16):
        for col in range(16):
            value=(value<<1)|int(b[y*17+col]>b[y*17+col+1])
    return value

def archive_hashes(directory=DEFAULT_ARCHIVE):
    found=[]
    if not directory.exists():return found
    for p in directory.rglob("*"):
        if p.suffix.lower() not in (".jpg",".jpeg",".png",".webp"):continue
        try:
            with Image.open(p) as img:
                found.append((str(p),fingerprint(img)))
        except (OSError,ValueError):continue
    return found

def technical_checks(path, other_hashes=()):
    result={"file":str(path),"passed":False,"reasons":[]}
    p=Path(path)
    if not p.is_file():
        result["reasons"].append("missing_file")
        return result
    if p.stat().st_size>MAX_BYTES or p.stat().st_size<10_000:
        result["reasons"].append("file_size_out_of_range")
    try:
        with Image.open(p) as im:
            im.verify()
        with Image.open(p) as im:
            img=im.convert("RGB")
            w,h=img.size
            result["size"]=[w,h]
            if min(w,h)<MIN_SIDE:result["reasons"].append("low_resolution")
            ratio=w/h
            # Allows square source photos; a separate 9:16 formatter is required before posting.
            if ratio<.42 or ratio>1.8:result["reasons"].append("extreme_aspect_ratio")
            st=ImageStat.Stat(img.resize((96,96)))
            if max(st.stddev)<10:result["reasons"].append("flat_or_placeholder")
            if max(st.mean)>250 or min(st.mean)<3:result["reasons"].append("extreme_exposure")
            digest=fingerprint(img)
            for label, old in other_hashes:
                distance=(digest^old).bit_count()
                if distance<=DUPLICATE_THRESHOLD:
                    result["reasons"].append("possible_duplicate")
                    result["duplicate_of"]=label
                    result["hash_distance"]=distance
                    break
    except (OSError,ValueError):
        result["reasons"].append("invalid_image")
    result["passed"]=len(result["reasons"])==0
    return result

def build_vision_request(image):
    with Image.open(image) as im:
        im=im.convert("RGB")
        im.thumbnail((900,900),Image.Resampling.LANCZOS)
        import io
        buffer=io.BytesIO()
        im.save(buffer,format="JPEG",quality=83)
    encoded=base64.b64encode(buffer.getvalue()).decode("ascii")
    return {
        "model":"clef",
        "state":"Inspect the attached single car CGI image for SEIBELGRAM premium original concept art. Be conservative. An unbranded unusual coherent futuristic vehicle is required. Do not infer logos that cannot be seen.",
        "images":[{"content_type":"image/jpeg","base64":encoded}],
        "questions":QUESTIONS
    }

def assess_vision_data(data):
    """Independently validate model output. No unknown output can pass."""
    reasons=[]
    body=data.get("result") if isinstance(data,dict) and "result" in data else data
    if not isinstance(body,dict):return False,["invalid_vision_response"],{}
    answers=body.get("answers")
    if not isinstance(answers,dict):
        return False,["missing_vision_answers"],{}
    cutoffs={"one_car":.85,"professional":.82}
    for name,cutoff in cutoffs.items():
        ans=answers.get(name,{})
        value=ans.get("noul") if isinstance(ans,dict) else None
        if not isinstance(value,(float,int)) or value<cutoff:
            reasons.append(name+"_not_verified")
    for name in ("branding","geometry_error"):
        ans=answers.get(name,{})
        value=ans.get("noul") if isinstance(ans,dict) else None
        if not isinstance(value,(float,int)) or value>.18:
            reasons.append(name+"_cannot_rule_out")
    future=answers.get("futurism",{})
    score=future.get("score") if isinstance(future,dict) else None
    if not isinstance(score,(float,int)) or score<2.25:
        reasons.append("not_distinctly_futuristic")
    score_summary={k:({kk:v for kk,v in a.items() if kk in ("type","noul","score","confidence")} if isinstance(a,dict) else {})
        for k,a in answers.items() if k in QUESTIONS}
    return len(reasons)==0,reasons,score_summary

def vision_check(path,token=None,account=None):
    token=(token or os.getenv("CF_API_TOKEN","")).strip()
    account=(account or os.getenv("CF_ACCOUNT_ID","")).strip()
    if not token or not account:
        return False,["vision_secrets_missing"],{}
    url=f"https://api.cloudflare.com/client/v4/accounts/{account}/ai/run/{VISION_MODEL}"
    try:
        response=requests.post(url,json=build_vision_request(path),
            headers={"Authorization":"Bearer "+token},timeout=110)
        response.raise_for_status()
        data=response.json()
        if data.get("success") is False:
            return False,["vision_api_error"],{}
        return assess_vision_data(data)
    except (requests.RequestException,ValueError,OSError):
        return False,["vision_request_failed"],{}

def run(files,archive,output,online=False):
    past=archive_hashes(archive)
    checks=[]
    for file in files:
        basic=technical_checks(file,past)
        if basic["passed"] and online:
            accepted,reasons,scores=vision_check(file)
        elif basic["passed"]:
            accepted,reasons,scores=False,["vision_not_evaluated"],{}
        else:
            accepted,reasons,scores=False,["technical_checks_failed"],{}
        basic["vision"]={"passed":accepted,"reasons":reasons,"scores":scores}
        basic["approved_for_publication"]=bool(basic["passed"] and accepted)
        checks.append(basic)
        # Also detect near-duplicates within a freshly generated batch.
        if basic.get("size"):
            with Image.open(file) as im:past.append((str(file),fingerprint(im.convert("RGB"))))
    report={"schema_version":1,"model":VISION_MODEL if online else None,
        "automatically_published":False,
        "all_approved":all(x["approved_for_publication"] for x in checks),
        "items":checks,
        "warning":"AI vision cannot guarantee no logos, no structural errors or original design. Human spot-check recommended; posting is separately gated."}
    Path(output).parent.mkdir(parents=True,exist_ok=True)
    Path(output).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"approved":report["all_approved"],
        "items":[{"file":x["file"],"approved":x["approved_for_publication"],
            "technical":x["reasons"],"vision":x["vision"]["reasons"]} for x in checks]},ensure_ascii=False))
    return report

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("files",nargs="+")
    parser.add_argument("--archive",default=str(DEFAULT_ARCHIVE))
    parser.add_argument("--output",default="photo_output/qa-report.json")
    parser.add_argument("--online",action="store_true")
    args=parser.parse_args()
    run(args.files,Path(args.archive),args.output,args.online)

if __name__=="__main__":
    main()
