#!/usr/bin/env python3
"""Read-only Buffer status check for the one authorized November 9 TikTok post."""
import json,os
from pathlib import Path
from publish import gql
ID="6af1dbc2010fa6782143d2b5"
EXPECTED="2070. Would you drive this?"
def main():
    token=os.getenv("BUFFER_API_KEY","").strip()
    if not token:raise RuntimeError("Buffer token missing")
    query="""query ReadSeibelgramPost($input: PostInput!) {
      post(input: $input) { id status externalLink sentAt text channelService }
    }"""
    post=gql(token,query,{"input":{"id":ID}})["post"]
    if post.get("id")!=ID:
        raise RuntimeError("Buffer returned wrong post ID")
    if EXPECTED not in (post.get("text") or ""):
        raise RuntimeError("Buffer post text differs from expected.")
    result={"id":ID,"status":post.get("status"),"sentAt":post.get("sentAt"),
        "public_tiktok_url":post.get("externalLink"),"platform":post.get("channelService"),
        "content_verified":True,"public_confirmation":bool(post.get("externalLink") and post.get("sentAt")),
        "read_only":True}
    print(json.dumps(result,ensure_ascii=False,indent=2))
    Path("nov9-publish-status.json").write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding="utf-8")
if __name__=="__main__":main()
