#!/usr/bin/env python3
"""Single authorized live photo post, Monday Nov 9. Never retry or duplicate."""
import argparse
import json
import os
import time
from pathlib import Path
from PIL import Image, ImageOps
import requests
from publish import gql, MUTATION, verify

SOURCE=Path(".review/car.jpg")
ROOT=Path("content/2026-11-09-magenta")
PHOTO=ROOT/"photo.jpg"
LOCK=ROOT/"attempt-lock.json"
RECEIPT=Path("nov9-publication-result.json")
PUBLIC="https://raw.githubusercontent.com/seibelserg-cloud/seibelgram-future-bot/main/content/2026-11-09-magenta/photo.jpg"
CAPTION="2070. Would you drive this? ⚡ Fictional AI-generated concept art. #FutureCars #ConceptCars #CarDesign #Seibelgram"

def stage():
    if LOCK.exists() or PHOTO.exists():
        raise RuntimeError("Nov 9 post already reserved. Never stage or publish twice.")
    if not SOURCE.exists():
        raise RuntimeError("The visually reviewed Runway image is missing.")
    with Image.open(SOURCE) as im:
        im.verify()
    with Image.open(SOURCE) as im:
        im=ImageOps.exif_transpose(im).convert("RGB")
        if im.width < 700 or im.height < 1200:
            raise RuntimeError("Portrait too small for social publication.")
        if abs(im.width/im.height - 9/16) > 0.015:
            raise RuntimeError("Expected near 9:16 portrait, no cropping permitted.")
        im=im.resize((1080,1920),Image.Resampling.LANCZOS)
        ROOT.mkdir(parents=True,exist_ok=True)
        im.save(PHOTO,format="JPEG",quality=92,optimize=True,subsampling=0)
    LOCK.write_text(json.dumps({
        "unique_post":"SEIBELGRAM-2026-11-09-MAGENTA-ONE-SHOT",
        "reserved":True,"attempts_allowed":1,"automatic_retries":False,
        "date":"2026-11-09","channel":"tiktok/@seibelgram",
        "status":"reserved BEFORE Buffer submission - may have been published",
        "source_run_id":42636823339,"source_artifact":"seibelgram-nov9-runway-editorial-review",
        "image":"photo.jpg","caption":CAPTION
    },indent=2,ensure_ascii=False),encoding="utf8")
    print("Reserved unique post, created 1080x1920 photo. Nothing submitted yet.")

def check_hosted():
    for _ in range(10):
        try:
            response=requests.head(PUBLIC,timeout=12,allow_redirects=True)
            if response.status_code==200 and response.headers.get("Content-Type","").lower().startswith("image/"):
                return
        except requests.RequestException:pass
        time.sleep(7)
    raise RuntimeError("Public image not reachable; no Buffer call was made.")

def publish_once():
    if os.getenv("SEIBELGRAM_NOV9_LIVE_ONE_SHOT")!="yes":
        raise RuntimeError("User authorization gate absent.")
    if not PHOTO.exists() or not LOCK.exists():
        raise RuntimeError("Committed attempt reservation missing; abort.")
    token=os.getenv("BUFFER_API_KEY","").strip()
    if not token:raise RuntimeError("Buffer secret unavailable")
    check_hosted()
    channel=verify(token)
    payload={
        "text":CAPTION,
        "channelId":channel,
        "schedulingType":"automatic",
        "mode":"shareNow",
        "aiAssisted":True,
        "metadata":{"tiktok":{"title":"2070: Would you drive this?"}},
        "assets":[{"image":{"url":PUBLIC}}]
    }
    print("Submitting EXACTLY ONE approved 9:16 photo to @seibelgram. NEVER retry this job.")
    try:
        response=gql(token,MUTATION,{"input":payload}).get("createPost")
        post=response.get("post") if isinstance(response,dict) else None
        if not post:
            result={"status":"UNCONFIRMED","reason":"Buffer returned no post"}
        else:
            result={"status":"BUFFER_ACCEPTED","post_id":post.get("id"),
                "buffer_status":post.get("status"),"tiktok_publication_verified":False}
            print("Buffer accepted post ID",post.get("id"),"status",post.get("status"))
    except Exception as exc:
        result={"status":"UNCONFIRMED","reason":type(exc).__name__}
        print("Unknown Buffer outcome, DO NOT RETRY, inspect TikTok:",type(exc).__name__)
    result.update({"channel":"@seibelgram","date":"2026-11-09",
        "automatic_retries":False,"image_url":PUBLIC,"caption":CAPTION})
    RECEIPT.write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding="utf-8")
    print("Receipt stored; no more public submissions in this run.")

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("phase",choices=("stage","publish"))
    args=p.parse_args()
    stage() if args.phase=="stage" else publish_once()
