import unittest

from mapper.call_session import CONTACT, CallSession


class CallSessionTests(unittest.TestCase):
    def test_contact_is_synthetic(self):
        self.assertEqual("Sam", CONTACT)
        self.assertNotIn("gigi", CONTACT.lower())

    def test_start_does_not_open_media(self):
        session = CallSession()
        emitted = session.start()
        self.assertEqual([("near", "permission_required")], emitted)
        self.assertFalse(session.media_allowed)
        self.assertFalse(session.near.screen_open)
        self.assertFalse(session.near.camera_on)

    def test_ring_asks_far_house(self):
        session = CallSession()
        session.start()
        emitted = session.invite()
        self.assertEqual(
            [("near", "waiting_for_user"), ("far", "permission_required")],
            emitted,
        )
        self.assertEqual("ringing", session.phase)
        self.assertFalse(session.far.screen_open)

    def test_accept_opens_screens_not_lamp_camera(self):
        session = CallSession()
        session.start()
        session.invite()
        emitted = session.accept()
        self.assertEqual([("near", "quiet"), ("far", "quiet")], emitted)
        self.assertTrue(session.near.screen_open)
        self.assertTrue(session.far.screen_open)
        self.assertFalse(session.near.camera_on)
        self.assertFalse(session.far.camera_on)

    def test_decline_before_invite_stays_dark(self):
        session = CallSession()
        session.start()
        session.decline()
        self.assertEqual("ended", session.phase)
        self.assertFalse(session.media_allowed)
        self.assertFalse(session.far.screen_open)
        self.assertEqual("quiet", session.near.event)

    def test_hangup_closes_screens(self):
        session = CallSession()
        session.start()
        session.invite()
        session.accept()
        session.hangup()
        self.assertFalse(session.near.screen_open)
        self.assertFalse(session.media_allowed)
        self.assertEqual("quiet", session.near.event)

    def test_cannot_accept_from_idle(self):
        with self.assertRaises(ValueError):
            CallSession().accept()

    def test_snapshot_does_not_mutate_after_later_actions(self):
        session = CallSession()
        session.start()
        snap = session.snapshot()
        session.decline()
        self.assertEqual("confirm", snap["phase"])
        self.assertEqual("permission_required", snap["near"]["event"])

    def test_start_after_ended_restarts(self):
        session = CallSession()
        session.start()
        session.decline()
        emitted = session.start()
        self.assertEqual("confirm", session.phase)
        self.assertEqual([("near", "permission_required")], emitted)

    def test_dial_rings_far_house(self):
        session = CallSession()
        emitted = session.dial()
        self.assertEqual("ringing", session.phase)
        self.assertEqual(
            [
                ("near", "permission_required"),
                ("near", "waiting_for_user"),
                ("far", "permission_required"),
            ],
            emitted,
        )


if __name__ == "__main__":
    unittest.main()
