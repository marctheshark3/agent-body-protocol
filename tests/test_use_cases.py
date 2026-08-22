import unittest

from mapper.call_session import CallSession, sanitize_note
from mapper.help_mode import HelpMode
from mapper.virtual_body import VirtualBody


class MissedCallTests(unittest.TestCase):
    def test_no_answer_lets_near_leave_a_message(self):
        session = CallSession()
        session.dial()
        emitted = session.no_answer()
        self.assertEqual("missed", session.phase)
        self.assertIn(("near", "waiting_for_user"), emitted)
        self.assertIn(("far", "quiet"), emitted)
        left = session.leave_message("Call me when you land.")
        self.assertEqual("Call me when you land.", session.far.message)
        self.assertEqual("completed", session.near.event)
        self.assertEqual("waiting_for_user", session.far.event)
        self.assertTrue(session.far.screen_open)
        self.assertIn(("near", "completed"), left)

    def test_talk_stays_on_paired_screen(self):
        session = CallSession()
        session.dial()
        session.accept()
        session.talk("hey sam, tests are green")
        self.assertTrue(session.near.mic_on)
        self.assertEqual("hey sam, tests are green", session.far.heard)
        self.assertFalse(session.near.camera_on)

    def test_talk_rejected_before_accept(self):
        session = CallSession()
        session.dial()
        with self.assertRaises(ValueError):
            session.talk("hello")

    def test_secret_note_rejected(self):
        with self.assertRaises(ValueError):
            sanitize_note("password hunter2")


class HelpModeTests(unittest.TestCase):
    def test_walks_forgot_password_without_typing(self):
        help_mode = HelpMode()
        self.assertEqual("blocked", help_mode.stuck())
        self.assertEqual("thinking", help_mode.consent_yes())
        self.assertEqual("waiting_for_user", help_mode.point_reset())
        self.assertEqual("Send reset link", help_mode.pointed)
        rendered = str(help_mode.snapshot()).lower()
        self.assertNotIn("type", rendered)
        self.assertEqual("completed", help_mode.done())

    def test_cannot_point_before_consent(self):
        with self.assertRaises(ValueError):
            HelpMode().point_reset()


class ScenarioBodies(unittest.TestCase):
    def test_ci_pass_is_green_on_one_lamp(self):
        body = VirtualBody("near")
        for name in ("started", "thinking", "tests_passed", "completed"):
            body.apply(name)
        self.assertEqual("completed", body.event)
        self.assertGreater(body.color[1], body.color[0])


if __name__ == "__main__":
    unittest.main()
