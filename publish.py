#!/usr/bin/env python3
"""Buffer GraphQL integration. Safe by default: discovery only, no publishing."""
import argparse
import json
import os
from pathlib import Path
from urllib.parse import urlparse
import requests

API = "https://api.buffer.com"
TARGET_TIKTOK = "seibelgram"

MUTATION = """mutation CreateSeibelgram($input: CreatePostInput!) {
  createPost(input: $input) {
    ... on PostActionSuccess { post { id status } }
    ... on MutationError { message }
  }
}"""

def gql(token, query, variables=None):
    response = requests.post(API, json={"query": query, "variables": variables or {}},
        headers={"Authorization": f"Bearer {token.strip()}", "Content-Type": "application/json"},
        timeout=45)
    response.raise_for_status()
    data = response.json()
    if data.get("errors"):
        # Avoid echoing any accidental sensitive data in upstream errors.
        raise RuntimeError("Buffer GraphQL query rejected. Check the schema and key permissions.")
    if "data" not in data:
        raise RuntimeError("Buffer GraphQL returned no data.")
    return data["data"]

def channels(token):
    organizations = gql(token, "query { account { organizations { id name } } }")["account"]["organizations"]
    result = []
    for org in organizations:
        query = """query GetChannels($id: OrganizationId!) {
          channels(input: { organizationId: $id }) {
            id name displayName externalLink service isDisconnected isLocked
          }
        }"""
        result.extend(gql(token, query, {"id": org["id"]})["channels"])
    return result

def is_target_tiktok(channel):
    if str(channel.get("service","")).lower() != "tiktok":
        return False
    external = (channel.get("externalLink") or "").strip()
    if external:
        path = urlparse(external if "://" in external else "https://" + external).path.lower().rstrip("/")
        if path == "/@" + TARGET_TIKTOK:
            return True
        # If the provider supplies a different path, never silently pick that account.
        return False
    return channel.get("name", "").strip().lower().lstrip("@") == TARGET_TIKTOK

def connected_tiktok(token):
    matches = [ch for ch in channels(token) if is_target_tiktok(ch)]
    if len(matches) != 1:
        raise RuntimeError(f"Expected exactly one TikTok @{TARGET_TIKTOK}; matched {len(matches)}")
    ch = matches[0]
    if ch.get("isDisconnected") or ch.get("isLocked"):
        raise RuntimeError("TikTok channel is disconnected or locked in Buffer.")
    return ch

def verify(token):
    ch = connected_tiktok(token)
    print("SUCCESS: Buffer API authentication and connected TikTok verified.")
    print("Target channel:", ch.get("name"), "service:", ch["service"])
    print("No video was uploaded or published.")
    return ch["id"]

def caption_for_platform(meta, platform):
    # TikTok: Buffer's composer documents a 150-character description limit.
    title = meta.get("title", "Future car concepts")
    labels = meta.get("labels") or ["A", "B"]
    if platform == "tiktok":
        text = f"{title}. Which design wins: {labels[0]} or {labels[1]}? Comment A or B. #FutureCars #AIConcept"
        return text[:150]
    return meta.get("caption","")[:2000]

def make_post_payload(meta, media_url, channel_id, platform, mode="addToQueue"):
    if meta.get("demo") is not False:
        raise RuntimeError("Refusing to publish an offline demo or unverified post.")
    if not media_url.startswith("https://"):
        raise RuntimeError("A public HTTPS video URL is required.")
    payload = {
        "text": caption_for_platform(meta, platform),
        "channelId": channel_id,
        "schedulingType": "automatic",
        "mode": mode,
        "aiAssisted": True,
        "assets": [{"video": {"url": media_url, "metadata": {"thumbnailOffset": 1500}}}]
    }
    if platform == "tiktok":
        payload["metadata"] = {"tiktok": {"isAiGenerated": True}}
    elif platform == "instagram":
        payload["metadata"] = {"instagram": {
            "type": "reel", "shouldShareToFeed": True, "isAiGenerated": True}}
    return payload

def ensure_public_video(url):
    if not url.startswith("https://"):
        raise ValueError("Expected a public HTTPS URL.")
    response = requests.head(url, allow_redirects=True, timeout=20)
    response.raise_for_status()
    if not response.headers.get("Content-Type", "").lower().startswith("video/"):
        raise RuntimeError("URL did not return a video content-type")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true", help="Only verify Buffer API and TikTok connection")
    parser.add_argument("--publish", action="store_true", help="Explicit permission to create Buffer post")
    parser.add_argument("--media-url", default="")
    parser.add_argument("--metadata", default="site/post.json")
    args = parser.parse_args()

    token = os.environ.get("BUFFER_API_KEY", "").strip()
    if not token:
        raise RuntimeError("GitHub secret BUFFER_API_KEY is missing.")
    channel_id = verify(token)
    if not args.publish:
        return
    if not os.environ.get("SEIBELGRAM_ENABLE_POSTING") == "yes":
        raise RuntimeError("Publishing safety lock enabled. Explicit manual consent needed.")
    metadata = json.loads(Path(args.metadata).read_text(encoding="utf-8"))
    ensure_public_video(args.media_url)
    payload = make_post_payload(metadata, args.media_url, channel_id, "tiktok")
    result = gql(token, MUTATION, {"input": payload}).get("createPost")
    if not result or not result.get("post"):
        raise RuntimeError("Buffer did not accept the post; no confirmed publish.")
    print("Buffer post created:", result["post"]["id"])

if __name__ == "__main__":
    main()
