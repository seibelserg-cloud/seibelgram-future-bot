#!/usr/bin/env python3
"""Cloudflare Free-only FLUX.2 Klein 9B image backend for photo_bot.py.

This sends one Workers AI inference request and returns a Pillow image.
Cloudflare Free gives 10,000 Neurons/day; Klein 9B ~1,364 neurons / 1024²
according to Oct 2026 documentation. Quota exhaustion must fail closed;
NEVER enable Workers Paid or silently downgrade model quality.
"""
import base64
import io
import os
import time
import requests
from PIL import Image

MODEL="@cf/black-forest-labs/flux-2-klein-9b"
MAX_PROMPT=2048

def get_image(prompt,demo,index):
    if demo:
        from bot import get_image as offline_demo
        return offline_demo(prompt,True,index)
    account=os.getenv("CF_ACCOUNT_ID","").strip()
    token=os.getenv("CF_API_TOKEN","").strip()
    if not account or not token:
        raise RuntimeError("Missing Cloudflare Free credentials")
    if not isinstance(prompt,str) or not prompt or len(prompt)>MAX_PROMPT:
        raise ValueError("Image prompt empty or exceeds 2048 chars")
    url=f"https://api.cloudflare.com/client/v4/accounts/{account}/ai/run/{MODEL}"
    fields={"prompt":(None,prompt),"width":(None,"1024"),"height":(None,"1024")}
    # A transient 5xx can be retried once for IMAGE GENERATION ONLY.
    # Never retry Buffer/TikTok posting and never retry quota/permission errors.
    response=None
    for attempt in range(2):
        response=requests.post(url,files=fields,
            headers={"Authorization":f"Bearer {token}"},timeout=180)
        if response.status_code in (500,502,503,504) and attempt == 0:
            time.sleep(2)
            continue
        break
    if response.status_code==403:
        raise RuntimeError("FLUX2 model unavailable on Free plan. No paid plan enabled.")
    if response.status_code==429:
        raise RuntimeError("Free usage or capacity limit reached. Image rejected, no paid fallback.")
    response.raise_for_status()
    body=response.json()
    if not body.get("success") or not isinstance(body.get("result"),dict):
        raise RuntimeError("FLUX2 Workers AI image request failed")
    encoded=body["result"].get("image")
    if not encoded or not isinstance(encoded,str):
        raise RuntimeError("FLUX2 Workers AI returned no image")
    raw=base64.b64decode(encoded,validate=True)
    image=Image.open(io.BytesIO(raw)).convert("RGB")
    if min(image.size)<512:
        raise RuntimeError("FLUX2 returned unexpectedly small image")
    return image
