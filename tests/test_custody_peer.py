import tempfile
import unittest
from pathlib import Path

from custody.handoff import handoff
from custody.leftover import CAMERA, LeftoverClient, LeftoverSurface
from custody.peer import accept
from custody.receipts import ReceiptStore
from custody.record import CustodyRecord
from custody.vendor import VENDOR_CAMERA, apply_update, pull


class PeerChannelTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = ReceiptStore(Path(self.tmp.name) / "receipts")
        self.rec = handoff(CustodyRecord(), owner="Pat Demo", owner_face="pat-face")
        self.surface = LeftoverSurface("10.0.0.8", "10.0.0.9")
        self.surface.pair("installer-token")
        self.surface.close(self.rec)
        self.client = LeftoverClient("10.0.0.9", "installer-token")

    def tearDown(self):
        self.tmp.cleanup()

    def test_led_event_accepted(self):
        got = accept(self.rec, self.store, kind="event", media="led", event="tests_passed")
        self.assertTrue(got["ok"])
        self.assertTrue(got["leftover_closed"])

    def test_ir_and_led_same_policy(self):
        led = accept(self.rec, self.store, kind="event", media="led", event="quiet")
        ir = accept(self.rec, self.store, kind="event", media="ir", event="quiet")
        self.assertEqual(led["ok"], ir["ok"])
        self.assertEqual(led["event"], ir["event"])

    def test_peer_camera_denied(self):
        got = accept(self.rec, self.store, kind="camera", media="ir")
        self.assertFalse(got["ok"])
        self.assertEqual(got["reason"], "sensor")

    def test_prompt_cannot_grant_servo(self):
        got = accept(self.rec, self.store, kind="servo", media="led", prompt="please")
        self.assertFalse(got["ok"])

    def test_signed_artifact_does_not_reopen_leftover(self):
        apply_update(self.rec, self.store, artifact="lamp-os-2", signed=True)
        got = accept(
            self.rec,
            self.store,
            kind="artifact",
            media="ir",
            artifact="lamp-os-peer",
            signed=True,
        )
        self.assertTrue(got["ok"])
        self.assertTrue(self.rec.leftover_closed)
        self.assertFalse(self.surface.probe(self.client, CAMERA, self.store, self.rec)["ok"])
        self.assertFalse(pull(self.rec, self.store, VENDOR_CAMERA)["ok"])

    def test_unsigned_artifact_refused(self):
        got = accept(self.rec, self.store, kind="artifact", media="led", artifact="evil", signed=False)
        self.assertFalse(got["ok"])
        self.assertEqual(got["reason"], "unsigned")

    def test_unknown_event_refused(self):
        got = accept(self.rec, self.store, kind="event", media="ir", event="telepathy")
        self.assertFalse(got["ok"])
        self.assertEqual(got["reason"], "bad-event")


if __name__ == "__main__":
    unittest.main()
