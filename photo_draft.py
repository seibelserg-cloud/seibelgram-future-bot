#!/usr/bin/env python3
"""Create exactly one Buffer PHOTO DRAFT. Never publishes, schedules or queues.

Requires: public image URLs from this GitHub repository, Buffer API secret.
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path
from urllib.parse import urlparse
import requests
from publish import verify, gql, MUTATION

SAFE_REPO_PREFIX = "https://raw.githubusercontent.com/seibelserg-cloud/seibelgram-future-bot/"

def check_media(url):
    if not url.startswith(SAFE_REPO_PREFIX):
        raise RuntimeError("Photo URL must come from the approved public SEIBELGRAM repository.")
    for attempt in range(6):
        try:
            resp=requests.head(url,allow_redirects=True,timeout=18)
            if resp.status_code==200 and resp.headers.get("Content-Type","").lower().startswith("image/"):
                if int(resp.headers.get("Content-Length","0") or 0) > 20_000_000:
                    raise RuntimeError("Photo exceeds 20 MB.")
                return
        except requests.RequestException:
            pass
        time.sleep(8)
    raise RuntimeError("Photo is not publicly accessible as an image over HTTPS.")

def make_draft_payload(channel_id, urls):
    if not 1<=len(urls)<=10:
        raise RuntimeError("Only 1–10 photos are supported.")
    for url in urls:
        if not url.startswith(SAFE_REPO_PREFIX):
            raise RuntimeError("Unapproved photo URL.")
    return {
        "text": "Which future car would you drive — first or second? ⚡ "
                "Fictional AI-generated car concepts. #FutureCars #ConceptCars #Seibelgram",
        "channelId": channel_id,
        "schedulingType": "automatic",
        "mode": "addToQueue",
        "saveToDraft": True,
        "aiAssisted": True,
        "metadata": {"tiktok": {"title": "Future Cars: first or second?"}},
        "assets": [{"image": {"url": url}} for url in urls],
    }

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--urls",nargs="+",required=True)
    parser.add_argument("--output",default="photo-draft-result.json")
    args=parser.parse_args()
    if os.getenv("SEIBELGRAM_ALLOW_DRAFT_ONLY")!="yes":
        raise RuntimeError("Refusing to write to Buffer without explicit DRAFT-only mode.")
    token=os.getenv("BUFFER_API_KEY","").strip()
    if not token:raise RuntimeError("BUFFER_API_KEY secret missing.")
    target_id=verify(token)
    for url in args.urls:check_media(url)
    payload=make_draft_payload(target_id,args.urls)
    response=gql(token,MUTATION,{"input":payload}).get("createPost")
    if not response or not response.get("post"):
        raise RuntimeError("Buffer refused draft creation.")
    post=response["post"]
    if str(post.get("status","")).lower() not in ("draft",):
        raise RuntimeError("Buffer returned unexpected status; inspect Buffer account before any retry.")
    Path(args.output).write_text(json.dumps({
        "status":"draft", "post_id":post["id"], "photos":len(args.urls),
        "public_post_created":False, "requires_visual_review":True,
        "no_automatic_publishing":True
    },indent=2),encoding="utf-8")
    print("SUCCESS: saved a Buffer PHOTO DRAFT for @seibelgram. Not published, queued, or scheduled.")
    print("Post ID:",post["id"])

if __name__=="__main__":main()
