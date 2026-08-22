import tempfile
import unittest
from pathlib import Path

from custody.handoff import handoff
from custody.leftover import ACTUATE, BUDDY, CAMERA, LeftoverClient, LeftoverSurface
from custody.receipts import ReceiptStore
from custody.record import CustodyRecord


class CustodyLeftoverTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = ReceiptStore(Path(self.tmp.name) / "receipts")
        self.rec = CustodyRecord()
        self.surface = LeftoverSurface(body_host="10.0.0.8", leftover_host="10.0.0.9")
        self.surface.pair("installer-token")
        self.client = LeftoverClient(host="10.0.0.9", token="installer-token")

    def tearDown(self):
        self.tmp.cleanup()

    def test_pre_f1_leftover_camera_works(self):
        result = self.surface.probe(self.client, CAMERA, self.store, self.rec)
        self.assertTrue(result["ok"])

    def test_post_f1_camera_and_actuate_fail(self):
        handoff(self.rec, owner="Pat", owner_face="pat-face")
        self.surface.close(self.rec)
        cam = self.surface.probe(self.client, CAMERA, self.store, self.rec)
        act = self.surface.probe(self.client, ACTUATE, self.store, self.rec)
        self.assertFalse(cam["ok"])
        self.assertFalse(act["ok"])

    def test_buddy_token_fails_after_handoff(self):
        handoff(self.rec, owner="Pat", owner_face="pat-face")
        self.surface.close(self.rec)
        result = self.surface.probe(self.client, BUDDY, self.store, self.rec)
        self.assertFalse(result["ok"])
        self.assertIn("installer-token", self.rec.revoked_buddy_tokens)

    def test_receipt_names_path_time_and_owner(self):
        handoff(self.rec, owner="Pat", owner_face="pat-face")
        self.surface.close(self.rec)
        result = self.surface.probe(self.client, CAMERA, self.store, self.rec)
        receipt = result["receipt"]
        self.assertEqual(CAMERA, receipt["path"])
        self.assertEqual("Pat", receipt["owner"])
        self.assertIn("when", receipt)

    def test_leftover_cannot_delete_receipt(self):
        handoff(self.rec, owner="Pat", owner_face="pat-face")
        self.surface.close(self.rec)
        self.surface.probe(self.client, CAMERA, self.store, self.rec)
        self.assertFalse(self.store.delete_from("installer"))
        self.assertEqual(1, len(self.store.list()))

    def test_deny_holds_if_receipt_io_fails(self):
        handoff(self.rec, owner="Pat", owner_face="pat-face")
        self.surface.close(self.rec)
        dead = ReceiptStore(Path(self.tmp.name) / "receipts")
        dead.root = Path("/proc/1/not-a-dir/receipts")
        result = self.surface.probe(self.client, CAMERA, dead, self.rec)
        self.assertFalse(result["ok"])
        self.assertIsNone(result["receipt"])

    def test_same_host_is_not_f2(self):
        local = LeftoverClient(host="10.0.0.8", token="installer-token")
        result = self.surface.probe(local, CAMERA, self.store, self.rec)
        self.assertEqual("same-host-not-f2", result["error"])


if __name__ == "__main__":
    unittest.main()
