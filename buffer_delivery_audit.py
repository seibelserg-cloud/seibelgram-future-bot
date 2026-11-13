#!/usr/bin/env python3
"""Read-only verification of SEIBELGRAM's actual Buffer/TikTok delivery.

The scheduled publisher's BUFFER_ACCEPTED receipt means only that Buffer
accepted a job. This audit queries the post lifecycle after the publishing
window and records a TikTok URL if Buffer supplies one. NO createPost calls.
"""
import argparse
import datetime as dt
import json
import os
from pathlib import Path
from urllib.parse import urlparse

from publish import connected_tiktok, gql


QUERY = """query SeibelgramDelivery($id: PostId!) {
  post(input: {id: $id}) {
    id status channelId externalLink sentAt dueAt schedulingType
  }
}"""
OUTPUT = Path("delivery_audit") / "delivery-audit.json"
VALID_STATES = {"draft", "needs_approval", "scheduled", "sending", "sent", "error"}


def tiktok_url(value):
    """Return a verified-format TikTok URL only, never an arbitrary URL."""
    if not isinstance(value, str):
        return None
    p = urlparse(value)
    if p.scheme != "https" or not (p.hostname == "tiktok.com" or
                                     (p.hostname or "").endswith(".tiktok.com")):
        return None
    return value


def day_records(day, archive=Path("content")):
    dt.date.fromisoformat(day)
    folder = archive / day
    records = []
    for slot in (1, 2):
        entry = folder / f"slot-{slot}"
        reservation = entry / "reservation.json"
        receipt = entry / "buffer-receipt.json"
        if not reservation.exists():
            continue
        claim = json.loads(reservation.read_text(encoding="utf8"))
        if claim.get("unique_slot") != f"{day}-slot-{slot}":
            raise RuntimeError("Reservation's day/slot does not match its path")
        rec = {
            "slot": slot, "unique_slot": claim["unique_slot"],
            "scheduled_for_utc": claim.get("scheduled_for_utc"),
            "reservation": reservation.as_posix(),
            "receipt": receipt.as_posix() if receipt.exists() else None,
        }
        if receipt.exists():
            rec["buffer_receipt"] = json.loads(receipt.read_text(encoding="utf8"))
        records.append(rec)
    return records


def assess(records, token):
    """Safe query: only receipts from our immutable slots, no posting."""
    result = {"checked": len(records), "items": []}
    channel = None
    for entry in records:
        item = {k: entry[k] for k in ("slot", "unique_slot", "scheduled_for_utc", "reservation", "receipt")}
        receipt = entry.get("buffer_receipt")
        if not receipt:
            item["state"] = "reserved_without_buffer_receipt"
        elif receipt.get("status") != "BUFFER_ACCEPTED":
            item["state"] = "unconfirmed_buffer_attempt"
        elif not receipt.get("buffer_post_id"):
            item["state"] = "buffer_post_id_missing"
        else:
            try:
                if channel is None:
                    channel = connected_tiktok(token)
                data = gql(token, QUERY, {"id": receipt["buffer_post_id"]})
                post = data.get("post")
                if not isinstance(post, dict) or post.get("id") != receipt["buffer_post_id"]:
                    raise ValueError("Mismatched or missing Buffer post")
                if post.get("channelId") != channel.get("id"):
                    raise ValueError("Buffer post belongs to the wrong channel")
                status = str(post.get("status") or "").lower()
                if status not in VALID_STATES:
                    raise ValueError("Unknown Buffer posting status")
                item.update({
                    "state": status, "buffer_post_id": post["id"],
                    "sent_at": post.get("sentAt"),
                    "tiktok_url": tiktok_url(post.get("externalLink")),
                    "buffer_scheduling_type": post.get("schedulingType"),
                })
            except Exception as exc:
                # Surface a verifiable error without ever exposing API tokens.
                item.update({"state": "buffer_status_query_failed", "error": type(exc).__name__})
        result["items"].append(item)
    if not records:
        result["summary"] = "no_media_reservation_today"
    elif all(x["state"] == "sent" for x in result["items"]):
        result["summary"] = "all_reserved_posts_sent"
    else:
        result["summary"] = "delivery_unconfirmed_or_incomplete"
    return result


def run(day, archive=Path("content"), output=OUTPUT):
    records = day_records(day, archive)
    # Buffer access is needed only when a reservation and accepted receipt exist.
    token = os.getenv("BUFFER_API_KEY", "").strip()
    needs_query = any(rec.get("buffer_receipt", {}).get("status") == "BUFFER_ACCEPTED"
                      for rec in records)
    if needs_query and not token:
        raise RuntimeError("BUFFER_API_KEY is missing for delivery audit")
    report = {"day": day, "source": "Buffer GraphQL post(input.id) (read-only)"}
    report.update(assess(records, token))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf8")
    print(json.dumps(report, ensure_ascii=False))
    # A negative result is a visible failed Actions audit, not an automated re-post.
    return report


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--day", default=dt.datetime.now(dt.timezone.utc).date().isoformat())
    p.add_argument("--output", default=str(OUTPUT))
    a = p.parse_args()
    report = run(a.day, output=Path(a.output))
    problem_states = {
        "error", "draft", "needs_approval", "scheduled",
        "reserved_without_buffer_receipt", "unconfirmed_buffer_attempt",
        "buffer_post_id_missing", "buffer_status_query_failed",
    }
    if any(x["state"] in problem_states for x in report["items"]):
        raise SystemExit("Buffer did not confirm a successfully sent TikTok post; inspect audit and DO NOT re-post automatically")


if __name__ == "__main__":
    main()
