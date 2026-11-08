#!/usr/bin/env python3
"""One-off safe Cloudflare test. Never print the token, account ID or response bodies."""
import base64
import io
import os
import re
import sys

import requests
from PIL import Image

MODEL = "@cf/black-forest-labs/flux-1-schnell"

def main():
    account = os.environ.get("CF_ACCOUNT_ID", "").strip()
    token = os.environ.get("CF_API_TOKEN", "").strip()
    missing = [name for name, value in (
        ("CF_ACCOUNT_ID", account), ("CF_API_TOKEN", token)) if not value]
    if missing:
        print("CONFIG ERROR: Missing GitHub repository secret(s): " + ", ".join(missing))
        return 2
    print("CONFIG OK: both secret names are present (values intentionally hidden).")
    if not re.fullmatch(r"[0-9a-fA-F]{32}", account):
        print("CONFIG ERROR: CF_ACCOUNT_ID does not look like a 32-character hexadecimal Cloudflare Account ID.")
        return 2
    if token.lower().startswith("bearer ") or "\n" in token:
        print("CONFIG ERROR: CF_API_TOKEN should be the raw token, without 'Bearer' or newlines.")
        return 2

    url = f"https://api.cloudflare.com/client/v4/accounts/{account}/ai/run/{MODEL}"
    print("TEST: Requesting one FLUX.1 Schnell image. No TikTok/Instagram publishing.")
    try:
        response = requests.post(url,
            headers={"Authorization": f"Bearer {token}", "Content-Type":"application/json"},
            json={"prompt":"An original fictional futuristic metallic silver grand touring concept car, full vehicle visible inside a clean modern design studio, cinematic lighting, no brand symbols, no text",
                  "steps":4},
            timeout=160)
    except requests.RequestException as exc:
        print("NETWORK ERROR:", type(exc).__name__, "(credentials not displayed)")
        return 3
    if response.status_code != 200:
        print(f"CLOUDFLARE ERROR: HTTP {response.status_code}.")
        if response.status_code in (401,403):
            print("Likely wrong token, missing Workers AI permission, or mismatched Account ID.")
        elif response.status_code == 404:
            print("Check Cloudflare Account ID and model availability.")
        elif response.status_code in (402,429):
            print("Check the free tier limit or account billing/usage status. Do not upgrade.")
        return 4
    try:
        payload = response.json()
        encoded = (payload.get("result") or {}).get("image")
        if not payload.get("success") or not encoded:
            print("CLOUDFLARE ERROR: 200 response without a generated image.")
            return 5
        img = Image.open(io.BytesIO(base64.b64decode(encoded, validate=True)))
        img.load()
        if min(img.size) < 256:
            print("CLOUDFLARE ERROR: Generated image unusually small.")
            return 5
        img.convert("RGB").save("cloudflare-test-image.jpg", quality=90)
    except (ValueError, TypeError, OSError, KeyError) as exc:
        print("CLOUDFLARE ERROR: Invalid image payload:", type(exc).__name__)
        return 5
    print(f"SUCCESS: Cloudflare token, permissions and image generation verified ({img.width} x {img.height}).")
    print("Image saved to the GitHub Actions artifact. Nothing was posted.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
