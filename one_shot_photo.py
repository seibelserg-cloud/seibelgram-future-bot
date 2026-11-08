#!/usr/bin/env python3
"""Create one 9:16 photo post via Buffer, one attempt only.

Image is adapted from the previously approved original without changing car design.
Create locks before submitting; do not retry if Buffer/TikTok show failure.
"""
from pathlib import Path
from PIL import Image,ImageOps,ImageFilter
import argparse,json,os,sys,time
import requests
from publish import gql, MUTATION, verify

ROOT=Path("content/first-live-test-2026-11-08")
SRC=Path("content/test-2026-11-08/car-1.jpg")
IMAGE=ROOT/"photo.jpg"
LOCK=ROOT/"attempt-lock.json"
RECEIPT=Path("seibelgram-first-test-result.json")
URL="https://raw.githubusercontent.com/seibelserg-cloud/seibelgram-future-bot/main/content/first-live-test-2026-11-08/photo.jpg"

def prepare():
    if not SRC.exists(): raise RuntimeError("Original approved photo missing")
    if LOCK.exists(): raise RuntimeError("Already attempted or prepared: do not repeat")
    img=Image.open(SRC).convert("RGB")
    if img.size != (1024,1024):raise RuntimeError("Unexpected original photo dimensions")
    canvas=ImageOps.fit(img,(1080,1920),method=Image.Resampling.LANCZOS)
    canvas=canvas.filter(ImageFilter.GaussianBlur(36))
    original=ImageOps.contain(img,(1080,1680),method=Image.Resampling.LANCZOS)
    canvas.paste(original,((1080-original.width)//2,(1920-original.height)//2))
    ROOT.mkdir(parents=True,exist_ok=True)
    canvas.save(IMAGE,quality=91,optimize=True,subsampling=0)
    LOCK.write_text(json.dumps({
        "date":"2026-11-08","type":"one-shot","target":"tiktok/@seibelgram",
        "status":"attempt authorized; do not repeat even if Buffer reports error",
        "source":str(SRC), "image":str(IMAGE),
        "attempts_allowed":1,"automatic_retries":False,
    },indent=2),encoding="utf8")
    print("Prepared 1080x1920 photo with original silver concept preserved.")
    print("Created one-shot lock (record before publication).")
    return

def check_online():
    for _ in range(12):
        try:
            r=requests.head(URL,allow_redirects=True,timeout=15)
            if r.status_code==200 and r.headers.get("content-type","").lower().startswith("image/"):return
        except requests.RequestException:pass
        time.sleep(6)
    raise RuntimeError("Photo hosting not ready, no posting requested. Keep attempt lock.")

def publish_once():
    if os.environ.get("SEIBELGRAM_ONE_SHOT_LIVE_TEST")!="yes":
        raise RuntimeError("One-shot posting safety gate absent.")
    if not LOCK.exists() or not IMAGE.exists():
        raise RuntimeError("One-shot lock/image missing.")
    token=os.environ.get("BUFFER_API_KEY","").strip()
    if not token:raise RuntimeError("Missing BUFFER_API_KEY")
    check_online()
    channel_id=verify(token)
    caption="A car from tomorrow. Would you drive it? ⚡ Fictional AI-generated concept. #FutureCars #ConceptCars #Seibelgram"
    payload={
        "text":caption,
        "channelId":channel_id,
        "schedulingType":"automatic",
        "mode":"shareNow",
        "aiAssisted":True,
        "metadata":{"tiktok":{"title":"A car from tomorrow"}},
        "assets":[{"image":{"url":URL}}]
    }
    print("Submitting ONE TikTok photo post via Buffer. No automatic retries.")
    try:
        response=gql(token,MUTATION,{"input":payload}).get("createPost")
        if response and response.get("post"):
            post=response["post"]
            receipt={"status":"accepted by Buffer","post_id":post.get("id"),
                "buffer_status":post.get("status"),"public_url":None,
                "live_publication_confirmed":False,
                "retries_permitted":False}
            print("Buffer accepted first photo post; status:",post.get("status"))
        else:
            receipt={"status":"unconfirmed","reason":"Buffer createPost returned no post",
                "live_publication_confirmed":False,"retries_permitted":False}
            print("UNCONFIRMED: Buffer did not return a post. Check TikTok before any further action.")
    except Exception as exc:
        receipt={"status":"unconfirmed","reason":type(exc).__name__,
            "live_publication_confirmed":False,"retries_permitted":False}
        print("UNCONFIRMED:",type(exc).__name__,"Check TikTok. DO NOT RETRY.")
    RECEIPT.write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding="utf8")
    return

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("phase",choices=("prepare","publish"))
    a=p.parse_args()
    prepare() if a.phase=="prepare" else publish_once()
