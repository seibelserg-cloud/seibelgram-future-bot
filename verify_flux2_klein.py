#!/usr/bin/env python3
"""One real FLUX.2 klein-9b smoke image. Free-plan quota, no billing setup or posting.

Uses Cloudflare Workers AI hosted model. Multipart request per official docs.
"""
import base64
import io
import os
from pathlib import Path
import requests
from PIL import Image
from photo_bot import prompts_for

MODEL="@cf/black-forest-labs/flux-2-klein-9b"
OUTPUT=Path("flux2-klein-smoke.jpg")
def generate_one():
    account=os.environ.get("CF_ACCOUNT_ID","").strip()
    token=os.environ.get("CF_API_TOKEN","").strip()
    if not account or not token:raise RuntimeError("Missing existing Cloudflare Free secrets")
    prompt=prompts_for("2026-11-09",1,showcase=True)[1][1]  # AERO BEAST
    url=f"https://api.cloudflare.com/client/v4/accounts/{account}/ai/run/{MODEL}"
    # Cloudflare's FLUX.2 multipart models do not accept JSON requests.
    fields={
        "prompt":(None,prompt),
        "width":(None,"1024"),
        "height":(None,"1024"),
    }
    response=requests.post(url,headers={"Authorization":f"Bearer {token}"},
        files=fields,timeout=160)
    if response.status_code==403:
        raise RuntimeError("Klein 9B unavailable on this Workers Free account; no upgrade made.")
    response.raise_for_status()
    body=response.json()
    if not body.get("success") or not body.get("result",{}).get("image"):
        raise RuntimeError("Cloudflare FLUX2 did not return a generated image.")
    image=Image.open(io.BytesIO(base64.b64decode(body["result"]["image"],validate=True))).convert("RGB")
    if min(image.size)<512:raise RuntimeError("Flux2 returned undersized image")
    image.save(OUTPUT,quality=92,optimize=True,subsampling=0)
    print(f"SUCCESS: 1 Cloudflare-hosted {MODEL} test image; {image.size}; NO social posting or billing change.")
    print(f"Saved {OUTPUT} ({OUTPUT.stat().st_size} bytes)")

if __name__=="__main__":generate_one()
