import unittest

from custody.handoff import handoff
from custody.presence import EXPIRED_INSTALLER, OWNER, STRANGER, bind
from custody.record import CustodyRecord


class CustodyPresenceTests(unittest.TestCase):
    def setUp(self):
        self.rec = handoff(
            CustodyRecord(bindable_faces=["installer-face"]),
            owner="Pat",
            owner_face="pat-face",
            owner_phrase="oak-lamp",
            installer_faces=["installer-face"],
        )

    def test_owner_face_binds_owner(self):
        presence = bind(self.rec, face="pat-face")
        self.assertEqual(OWNER, presence.subject)
        self.assertEqual("face", presence.source)

    def test_unknown_face_binds_stranger(self):
        self.assertEqual(STRANGER, bind(self.rec, face="random").subject)

    def test_installer_face_after_f1_is_expired(self):
        presence = bind(self.rec, face="installer-face")
        self.assertEqual(EXPIRED_INSTALLER, presence.subject)

    def test_phrase_without_camera_miss_does_not_bind(self):
        presence = bind(self.rec, phrase="oak-lamp", camera_miss=False)
        self.assertEqual(STRANGER, presence.subject)
        self.assertEqual("unbound", presence.source)

    def test_phrase_after_camera_miss_is_labeled_fallback(self):
        presence = bind(self.rec, phrase="oak-lamp", camera_miss=True)
        self.assertEqual(OWNER, presence.subject)
        self.assertEqual("phrase-fallback", presence.source)


if __name__ == "__main__":
    unittest.main()
