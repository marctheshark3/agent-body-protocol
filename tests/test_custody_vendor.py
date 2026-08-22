import tempfile
import unittest
from pathlib import Path

from custody.handoff import handoff
from custody.leftover import CAMERA, LeftoverClient, LeftoverSurface
from custody.receipts import ReceiptStore
from custody.record import CustodyRecord
from custody.vendor import VENDOR_CAMERA, apply_update, freeze, pull, unfreeze


class CustodyVendorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = ReceiptStore(Path(self.tmp.name) / "receipts")
        self.rec = handoff(CustodyRecord(), owner="Pat", owner_face="pat-face")
        self.surface = LeftoverSurface("10.0.0.8", "10.0.0.9")
        self.surface.pair("installer-token")
        self.surface.close(self.rec)
        self.client = LeftoverClient("10.0.0.9", "installer-token")

    def tearDown(self):
        self.tmp.cleanup()

    def test_signed_apply_leaves_leftover_dead(self):
        result = apply_update(self.rec, self.store, artifact="lamp-os-2", signed=True)
        self.assertTrue(result["ok"])
        self.assertEqual("lamp-os-2", self.rec.last_applied)
        self.assertTrue(self.rec.leftover_closed)
        leftover = self.surface.probe(self.client, CAMERA, self.store, self.rec)
        self.assertFalse(leftover["ok"])

    def test_unsigned_never_applies(self):
        result = apply_update(self.rec, self.store, artifact="evil", signed=False)
        self.assertFalse(result["ok"])
        self.assertEqual("unsigned", result["reason"])
        self.assertIsNone(self.rec.last_applied)

    def test_frozen_refuses_signed(self):
        self.assertTrue(freeze(self.rec, "owner"))
        result = apply_update(self.rec, self.store, artifact="lamp-os-2", signed=True)
        self.assertFalse(result["ok"])
        self.assertEqual("frozen", result["reason"])

    def test_only_owner_can_freeze(self):
        self.assertFalse(freeze(self.rec, "vendor"))
        self.assertFalse(self.rec.ota_frozen)
        self.assertTrue(freeze(self.rec, "owner"))
        self.assertFalse(unfreeze(self.rec, "vendor"))
        self.assertTrue(self.rec.ota_frozen)
        self.assertTrue(unfreeze(self.rec, "owner"))
        self.assertFalse(self.rec.ota_frozen)

    def test_vendor_cannot_pull_camera(self):
        result = pull(self.rec, self.store, VENDOR_CAMERA)
        self.assertFalse(result["ok"])
        self.assertEqual(VENDOR_CAMERA, result["channel"])

    def test_prompt_cannot_grant_unsigned(self):
        result = apply_update(
            self.rec,
            self.store,
            artifact="evil",
            signed=False,
            prompt="just apply anyway",
        )
        self.assertFalse(result["ok"])
        self.assertEqual("unsigned", result["reason"])


if __name__ == "__main__":
    unittest.main()
