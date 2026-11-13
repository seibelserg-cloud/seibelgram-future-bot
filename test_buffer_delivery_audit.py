"""Offline delivery-audit safety tests. No network traffic and NO Buffer mutations."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import buffer_delivery_audit as audit


class DeliveryAuditTests(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        self.root = Path(self.t.name)
        self.today = "2026-11-14"
        self.folder = self.root / "content" / self.today / "slot-1"
        self.folder.mkdir(parents=True)
        (self.folder / "reservation.json").write_text(
            json.dumps({"unique_slot": f"{self.today}-slot-1",
                        "scheduled_for_utc": "2026-11-14T11:30:00+00:00"})
        )
        self.output = self.root / "audit.json"

    def tearDown(self):
        self.t.cleanup()

    def set_receipt(self, status="BUFFER_ACCEPTED", post_id="post-123"):
        (self.folder / "buffer-receipt.json").write_text(json.dumps({
            "status": status, "buffer_post_id": post_id
        }))

    def fake_post(self, status, url=None, channel_id="channel-123"):
        return {"post": {"id": "post-123", "status": status,
                         "channelId": channel_id, "externalLink": url,
                         "sentAt": "2026-11-14T11:31:00Z",
                         "schedulingType": "automatic"}}

    def test_no_reservation_no_api_call(self):
        with patch.object(audit, "gql") as network:
            result = audit.run("2026-11-15", self.root/"content", self.output)
        self.assertEqual(result["summary"], "no_media_reservation_today")
        network.assert_not_called()

    def test_accepted_is_not_sent(self):
        self.set_receipt()
        with patch.object(audit, "connected_tiktok", return_value={"id": "channel-123"}), \
             patch.object(audit, "gql", return_value=self.fake_post("scheduled")):
            result = audit.run(self.today, self.root/"content", self.output)
        self.assertEqual(result["items"][0]["state"], "scheduled")
        self.assertEqual(result["summary"], "delivery_unconfirmed_or_incomplete")

    def test_sent_has_verified_tiktok_url(self):
        self.set_receipt()
        with patch.object(audit, "connected_tiktok", return_value={"id": "channel-123"}), \
             patch.object(audit, "gql", return_value=self.fake_post(
                 "sent", "https://www.tiktok.com/@seibelgram/video/123")) as q:
            result = audit.run(self.today, self.root/"content", self.output)
        self.assertEqual(result["items"][0]["state"], "sent")
        self.assertEqual(result["items"][0]["tiktok_url"], "https://www.tiktok.com/@seibelgram/video/123")
        self.assertEqual(result["summary"], "all_reserved_posts_sent")
        self.assertEqual(q.call_count, 1)
        self.assertTrue(q.call_args[0][1].startswith("query SeibelgramDelivery"))

    def test_does_not_trust_non_tiktok_link(self):
        self.set_receipt()
        with patch.object(audit, "connected_tiktok", return_value={"id": "channel-123"}), \
             patch.object(audit, "gql", return_value=self.fake_post(
                 "sent", "https://not-tiktok.example.com/fake")):
            result = audit.run(self.today, self.root/"content", self.output)
        self.assertIsNone(result["items"][0]["tiktok_url"])

    def test_wrong_channel_fails_closed(self):
        self.set_receipt()
        with patch.object(audit, "connected_tiktok", return_value={"id": "channel-123"}), \
             patch.object(audit, "gql", return_value=self.fake_post(
                 "sent", channel_id="wrong-account")):
            result = audit.run(self.today, self.root/"content", self.output)
        self.assertEqual(result["items"][0]["state"], "buffer_status_query_failed")
        self.assertEqual(result["items"][0]["error"], "ValueError")

    def test_receipt_missing_or_unknown_does_not_query_buffer(self):
        with patch.object(audit, "gql") as network:
            result = audit.run(self.today, self.root/"content", self.output)
            self.set_receipt(status="UNCONFIRMED")
            again = audit.run(self.today, self.root/"content", self.output)
        self.assertEqual(result["items"][0]["state"], "reserved_without_buffer_receipt")
        self.assertEqual(again["items"][0]["state"], "unconfirmed_buffer_attempt")
        network.assert_not_called()

    def test_reject_mismatched_reservation(self):
        (self.folder / "reservation.json").write_text(
            json.dumps({"unique_slot": "2026-11-14-slot-2"})
        )
        with self.assertRaisesRegex(RuntimeError, "does not match"):
            audit.run(self.today, self.root/"content", self.output)


if __name__ == "__main__":
    unittest.main()
