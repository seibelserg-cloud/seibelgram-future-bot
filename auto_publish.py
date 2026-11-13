#!/usr/bin/env python3
"""SEIBELGRAM autonomous TikTok delivery, one post per day at most.

Post a generated valid concept image without subjective AI visual screening.
Preserve basic media integrity, exact-repeat prevention, original AI disclosure,
and the immutable reservation committed BEFORE a single Buffer request.
Unknown Buffer outcomes must never trigger a second post attempt.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
import shutil
from pathlib import Path
import subprocess
import time
from zoneinfo import ZoneInfo

import requests
from PIL import Image
from publish import gql, MUTATION, verify
from reel_from_photo import build as build_reel

OUTPUT = Path("photo_output")
ARCHIVE = Path("content")
HOST = "https://raw.githubusercontent.com/seibelserg-cloud/seibelgram-future-bot/main/"
STYLES = ("neon-pulse", "deep-motion", "glacier-drive")


def directory(day, slot):
    dt.date.fromisoformat(day)
    if slot not in (1, 2):
        raise ValueError("Only slot 1 or slot 2 is valid")
    return ARCHIVE / day / ("slot-" + str(slot))


def target_time(day, slot):
    local = dt.datetime.combine(
        dt.date.fromisoformat(day),
        dt.time(12, 30) if slot == 1 else dt.time(19, 0),
        tzinfo=ZoneInfo("Europe/Berlin"),
    )
    return local.astimezone(dt.timezone.utc)


def short_caption(concept):
    concept = str(concept).upper()
    if concept not in ("MONOLITH", "AERO BEAST", "SPACE LIMO"):
        raise ValueError("Unknown internal concept")
    caption = (
        f"Future / Impossible: {concept}. Would you drive it? "
        "⚡ AI-generated concept car. #FutureCars #AIConcept #Seibelgram"
    )
    if len(caption) > 150:
        raise ValueError("TikTok caption exceeds 150 characters")
    return caption


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save_status(state, reason, **details):
    OUTPUT.mkdir(parents=True, exist_ok=True)
    status = {"state": state, "reason": reason, **details}
    (OUTPUT / "auto-status.json").write_text(
        json.dumps(status, indent=2, ensure_ascii=False), encoding="utf8"
    )
    print(json.dumps(status, ensure_ascii=False))
    return status


def accepted_candidates(day, slot):
    """Select the first valid, non-repeated generated image. No AI visual QA.

    The user explicitly opted out of subjective checks for beauty, novelty,
    logos or car geometry. Only corruption, broken format and exact reuse
    of an already reserved source file can prevent scheduling.
    """
    manifest = json.loads((OUTPUT / "post.json").read_text(encoding="utf8"))
    if manifest.get("day") != day or manifest.get("slot") != slot:
        raise RuntimeError("AI images belong to a different day or publishing slot")
    if manifest.get("demo") is not False or manifest.get("published") is not False:
        raise RuntimeError("Demo or already-published images are prohibited")
    if not isinstance(manifest.get("images"), list):
        raise RuntimeError("Missing generated-image manifest list")

    previously_used = {
        sha256(p) for p in ARCHIVE.rglob("approved-source.jpg") if p.is_file()
    }
    eligible = []
    for image in manifest["images"]:
        if not isinstance(image, dict):
            continue
        filename = image.get("file")
        portrait_filename = image.get("portrait_file")
        if (not isinstance(filename, str) or Path(filename).name != filename
                or not isinstance(portrait_filename, str)
                or Path(portrait_filename).name != portrait_filename):
            continue
        source = OUTPUT / filename
        portrait = OUTPUT / portrait_filename
        if not source.is_file() or not portrait.is_file():
            continue
        if source.stat().st_size < 10_000:
            continue
        try:
            with Image.open(source) as im:
                im.verify()
            with Image.open(source) as im:
                if min(im.size) < 512:
                    continue
            with Image.open(portrait) as im:
                im.verify()
            with Image.open(portrait) as im:
                if im.size != (1080, 1920):
                    continue
        except (OSError, ValueError):
            continue
        digest = sha256(source)
        if digest in previously_used:
            continue
        eligible.append((image, source, portrait))
        previously_used.add(digest)
    return eligible

def prepare(day, slot):
    folder = directory(day, slot)
    # The morning and evening jobs are fallback attempts, NOT two daily posts.
    # Once the earlier slot is reserved, we never create another post that day:
    # even an unknown Buffer response might already have queued the first video.
    if slot == 2 and (directory(day, 1) / "reservation.json").exists():
        return save_status("skipped", "daily_post_already_reserved",
                           earlier_slot=str(directory(day, 1)))
    if folder.exists():
        # Previously reserved even if Buffer outcome was unknown. No retries.
        return save_status("skipped", "slot_already_reserved", folder=str(folder))
    due_at = target_time(day, slot)
    now = dt.datetime.now(dt.timezone.utc)
    if now >= due_at - dt.timedelta(minutes=15):
        return save_status("skipped", "too_late_to_schedule_safely")
    eligible = accepted_candidates(day, slot)
    if not eligible:
        return save_status("skipped", "no_valid_nonduplicate_image_generated")
    image, source, portrait = eligible[0]  # At most one video per slot
    folder.mkdir(parents=True, exist_ok=False)
    # Keep the generated source image to prevent exact repeat posts.
    shutil.copyfile(source, folder / "approved-source.jpg")
    media = folder / "future-reel.mp4"
    style = STYLES[(dt.date.fromisoformat(day).toordinal() + slot) % len(STYLES)]
    build_reel(portrait, media, style)
    if not media.is_file() or media.stat().st_size < 30_000:
        raise RuntimeError("Video encoder failed to produce a valid MP4")
    caption = short_caption(image["concept"])
    claim = {
        "unique_slot": f"{day}-slot-{slot}",
        "date": day,
        "slot": slot,
        "channel": "tiktok/@seibelgram",
        "state": "RESERVED_BEFORE_BUFFER_ATTEMPT",
        "automatic_retries": False,
        "source_photo": source.name,
        "source_image_sha256": sha256(source),
        "archived_source": "approved-source.jpg",
        "video_sha256": sha256(media),
        "video": media.name,
        "caption": caption,
        "scheduled_for_utc": due_at.isoformat(),
        "ai_generated": True,
        "original_synth_audio": True,
        "visual_qa_required": False,
    }
    (folder / "reservation.json").write_text(
        json.dumps(claim, indent=2, ensure_ascii=False), encoding="utf8"
    )
    (OUTPUT / "auto-ready.json").write_text(
        json.dumps({"folder": str(folder), "slot": slot, "day": day}, indent=2),
        encoding="utf8",
    )
    return save_status("ready", "valid_generated_video_encoded_and_reserved",
                       folder=str(folder), due_at=due_at.isoformat())


def ensure_public_video(url):
    if not url.startswith(HOST) or not url.endswith(".mp4"):
        raise RuntimeError("Refusing non-repository or non-MP4 media URL")
    # Repository media may need seconds to appear on the public raw endpoint.
    for attempt in range(8):
        try:
            response = requests.head(url, allow_redirects=True, timeout=15)
            mime = response.headers.get("Content-Type", "").lower().split(";")[0]
            if response.ok and mime in ("video/mp4", "application/octet-stream"):
                return
        except requests.RequestException:
            pass
        if attempt < 7:
            time.sleep(8)
    raise RuntimeError("Committed MP4 is not publicly accessible; do not post")


def post(day, slot):
    if os.getenv("SEIBELGRAM_ENABLE_POSTING") != "yes":
        raise RuntimeError("Live publishing flag absent")
    # Defence in depth: an evening publish invocation may not override the
    # first reservation even if it bypasses the earlier prepare() path.
    if slot == 2 and (directory(day, 1) / "reservation.json").exists():
        raise RuntimeError("Daily TikTok post already reserved in morning slot")
    folder = directory(day, slot)
    claim_file = folder / "reservation.json"
    receipt = folder / "buffer-receipt.json"
    if receipt.exists():
        raise RuntimeError("A Buffer attempt already has a receipt; refusing retry")
    claim = json.loads(claim_file.read_text(encoding="utf8"))
    if (
        claim.get("state") != "RESERVED_BEFORE_BUFFER_ATTEMPT"
        or claim.get("unique_slot") != f"{day}-slot-{slot}"
        or claim.get("channel") != "tiktok/@seibelgram"
        or claim.get("automatic_retries") is not False
        or claim.get("scheduled_for_utc") != target_time(day, slot).isoformat()
    ):
        raise RuntimeError("Invalid or mismatched immutable slot reservation")
    mp4 = folder / "future-reel.mp4"
    if not mp4.exists() or sha256(mp4) != claim.get("video_sha256"):
        raise RuntimeError("Video does not match reserved SHA-256")
    # Guard against a workflow that skips the reservation git commit.
    subprocess.run(["git", "cat-file", "-e", "HEAD:" + claim_file.as_posix()],
                   check=True, capture_output=True)
    subprocess.run(["git", "cat-file", "-e", "HEAD:" + mp4.as_posix()],
                   check=True, capture_output=True)
    due = target_time(day, slot)
    if dt.datetime.now(dt.timezone.utc) >= due - dt.timedelta(minutes=10):
        save_status("skipped", "missed_scheduled_slot", folder=str(folder))
        return
    public_url = HOST + mp4.as_posix()
    ensure_public_video(public_url)
    token = os.getenv("BUFFER_API_KEY", "").strip()
    if not token:
        raise RuntimeError("Missing BUFFER_API_KEY")
    channel_id = verify(token)
    # This is the sole mutating Buffer request. NO retries on HTTP timeout
    # or unknown outcomes: the GitHub reservation is already persisted.
    payload = {
        "text": claim["caption"],
        "channelId": channel_id,
        "schedulingType": "automatic",
        "mode": "customScheduled",
        "dueAt": due.isoformat().replace("+00:00", "Z"),
        "aiAssisted": True,
        "metadata": {"tiktok": {"isAiGenerated": True}},
        "assets": [{"video": {"url": public_url, "metadata": {"thumbnailOffset": 1500}}}],
    }
    result = {"slot": claim["unique_slot"], "video_sha256": claim["video_sha256"],
              "status": "UNCONFIRMED", "no_automatic_retry": True}
    try:
        action = gql(token, MUTATION, {"input": payload}).get("createPost")
        post_data = action.get("post") if isinstance(action, dict) else None
        if post_data and post_data.get("id"):
            result.update({"status": "BUFFER_ACCEPTED", "buffer_post_id": post_data["id"],
                           "buffer_status": post_data.get("status")})
        else:
            result["error"] = "Buffer refused the post or returned no post ID"
    except Exception as exc:
        result["error"] = type(exc).__name__
    finally:
        receipt.write_text(json.dumps(result, indent=2), encoding="utf8")
    print(json.dumps(result))
    if result["status"] != "BUFFER_ACCEPTED":
        raise RuntimeError("Buffer outcome not confirmed. Never automatically retry.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("prepare", "post"))
    parser.add_argument("--day", required=True)
    parser.add_argument("--slot", required=True, type=int, choices=(1, 2))
    args = parser.parse_args()
    if args.action == "prepare":
        prepare(args.day, args.slot)
    else:
        post(args.day, args.slot)


if __name__ == "__main__":
    main()
