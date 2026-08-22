import unittest

from mapper.call_session import CallSession
from mapper.virtual_body import VirtualBody


class TwoLampCallTests(unittest.TestCase):
    def test_dial_makes_two_different_bodies(self):
        near, far = VirtualBody("near"), VirtualBody("far")
        session = CallSession()
        for house, event in session.dial():
            (near if house == "near" else far).apply(event)
        self.assertEqual("waiting_for_user", near.event)
        self.assertEqual("permission_required", far.event)
        self.assertEqual("pulse", far.effect)
        self.assertGreater(far.color[0], far.color[2])
        self.assertNotEqual(near.event, far.event)
        self.assertLess(near.pose["wrist_pitch.pos"], -40)

    def test_accept_opens_screens_and_quiets_both_bodies(self):
        near, far = VirtualBody("near"), VirtualBody("far")
        session = CallSession()
        for house, event in session.dial():
            (near if house == "near" else far).apply(event)
        for house, event in session.accept():
            (near if house == "near" else far).apply(event)
        self.assertTrue(session.near.screen_open)
        self.assertTrue(session.far.screen_open)
        self.assertEqual("quiet", near.event)
        self.assertEqual("quiet", far.event)
        self.assertIsNone(near.effect)
        self.assertEqual([0, 0, 0], near.color)

    def test_thinking_is_blue_on_one_body_only(self):
        near, far = VirtualBody("near"), VirtualBody("far")
        near.apply("thinking")
        self.assertEqual("breathing", near.effect)
        self.assertGreater(near.color[2], near.color[0])
        self.assertEqual([0, 0, 0], far.color)
        self.assertIsNone(far.event)


if __name__ == "__main__":
    unittest.main()
