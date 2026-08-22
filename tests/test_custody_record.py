import tempfile
import unittest
from pathlib import Path

from custody.handoff import AlreadyOwned, handoff
from custody.presence import bind
from custody.record import CustodyRecord


class CustodyRecordTests(unittest.TestCase):
    def test_handoff_leaves_one_owner(self):
        rec = CustodyRecord(bindable_faces=["installer-face"], owner_phrase="setup-phrase")
        rec = handoff(rec, owner="Pat", owner_face="pat-face", owner_phrase="oak-lamp", installer_faces=["installer-face"], setup_phrase="setup-phrase")
        self.assertEqual("Pat", rec.owner)
        self.assertEqual(["pat-face"], rec.bindable_faces)
        self.assertIn("installer-face", rec.expired_installer_faces)
        self.assertEqual("oak-lamp", rec.owner_phrase)
        self.assertIsNotNone(rec.installer_expired_at)

    def test_installer_face_no_longer_binds_owner(self):
        rec = handoff(CustodyRecord(bindable_faces=["installer-face"]), owner="Pat", owner_face="pat-face", installer_faces=["installer-face"])
        self.assertNotEqual("owner", bind(rec, face="installer-face").subject)

    def test_setup_phrase_no_longer_binds(self):
        rec = CustodyRecord(owner_phrase="setup-phrase")
        rec = handoff(rec, owner="Pat", owner_face="pat-face", owner_phrase="oak-lamp", setup_phrase="setup-phrase")
        self.assertNotEqual("owner", bind(rec, phrase="setup-phrase", camera_miss=True).subject)

    def test_second_handoff_rejected(self):
        rec = handoff(CustodyRecord(), owner="Pat", owner_face="pat-face")
        with self.assertRaises(AlreadyOwned):
            handoff(rec, owner="Sam", owner_face="sam-face")

    def test_round_trip_disk(self):
        rec = handoff(CustodyRecord(), owner="Pat", owner_face="pat-face", owner_phrase="oak-lamp")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "custody.json"
            rec.save(path)
            loaded = CustodyRecord.load(path)
        self.assertEqual(rec.to_json(), loaded.to_json())


if __name__ == "__main__":
    unittest.main()
