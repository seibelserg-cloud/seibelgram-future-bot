#!/usr/bin/env python3
"""Buffer GraphQL publishing, disabled unless explicitly enabled in GitHub workflow."""
import argparse
import json
import os
from pathlib import Path
import time
import requests

API="https://api.buffer.com"
MUTATION="""mutation CreateSeibelgram($input: CreatePostInput!) {
  createPost(input: $input) {
    ... on PostActionSuccess { post { id status } }
    ... on MutationError { message }
  }
}"""

def gql(token, query, variables=None):
    r=requests.post(API,json={"query":query,"variables":variables or {}},
      headers={"Authorization":f"Bearer {token}","Content-Type":"application/json"},timeout=40)
    r.raise_for_status()
    obj=r.json()
    if obj.get("errors"): raise RuntimeError(f"Buffer GraphQL rejected request: {obj['errors']}")
    return obj["data"]

def channels(token):
    orgs=gql(token,"query { account { organizations { id name } } }")["account"]["organizations"]
    out=[]
    for org in orgs:
        q="query($id: String!) { channels(input: { organizationId: $id }) { id name service isDisconnected isLocked } }"
        for ch in gql(token,q,{"id":org["id"]})["channels"]:
            out.append(ch)
    return out

def selected(token):
    allowed={"tiktok":os.getenv("BUFFER_CHANNEL_TIKTOK",""),
             "instagram":os.getenv("BUFFER_CHANNEL_INSTAGRAM","")}
    available={c["id"]:c for c in channels(token)}
    out=[]
    for service,channel_id in allowed.items():
        if not channel_id:continue
        c=available.get(channel_id)
        if not c or str(c["service"]).lower()!=service or c["isDisconnected"] or c["isLocked"]:
            raise RuntimeError(f"Buffer {service} channel not connected or mismatched")
        name=c["name"].lower().strip().lstrip("@")
        if service=="tiktok" and name!="seibelgram":
            raise RuntimeError(f"Unexpected TikTok destination: {c['name']}")
        print("Verified:",service,c["name"],c["id"])
        out.append((service,channel_id))
    if not out:raise RuntimeError("No Buffer destination configured")
    return out

def ensure_public(url):
    if not url.startswith("https://"):raise ValueError("Public HTTPS media URL required")
    for _ in range(8):
        try:
            r=requests.head(url,allow_redirects=True,timeout=20)
            if r.status_code==200 and r.headers.get("Content-Type","").lower().startswith("video/"):
                return
        except requests.RequestException:pass
        time.sleep(15)
    raise RuntimeError("MP4 not publicly accessible yet")

def send(token, meta, media_url, targets):
    if meta.get("demo"):raise RuntimeError("Refusing to publish offline demo")
    for service,id_ in targets:
        payload={"text":meta["caption"],"channelId":id_,
          "schedulingType":"automatic","mode":"shareNow","aiAssisted":True,
          "assets":[{"video":{"url":media_url,"metadata":{"thumbnailOffset":1500}}}]}
        if service=="tiktok":
            payload["metadata"]={"tiktok":{"isAiGenerated":True}}
        else:
            payload["metadata"]={"instagram":{"type":"reel","shouldShareToFeed":True,"isAiGenerated":True}}
        result=gql(token,MUTATION,{"input":payload})["createPost"]
        if not result or not result.get("post"):
            raise RuntimeError(f"Buffer did not accept {service}: {result}")
        print("Submitted to Buffer:",service,result["post"])

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--discover",action="store_true")
    p.add_argument("--check-only",action="store_true")
    p.add_argument("--media-url",default="")
    a=p.parse_args()
    token=os.environ.get("BUFFER_API_KEY")
    if not token:raise RuntimeError("BUFFER_API_KEY GitHub secret required")
    if a.discover:
        for c in channels(token):print(c["service"],c["name"],c["id"])
        return
    targets=selected(token)
    if a.check_only:return
    meta=json.loads(Path("site/post.json").read_text(encoding="utf-8"))
    ensure_public(a.media_url)
    send(token,meta,a.media_url,targets)

if __name__=="__main__":main()
