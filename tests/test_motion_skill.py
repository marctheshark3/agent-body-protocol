import os
import unittest

from mapper.serve import EVENTS
from mapper.motion import FORBIDDEN, MotionError, aim, named_aim, validate_markers


class MotionSkillTests(unittest.TestCase):
    def test_named_user_matches_waiting_marker_prefix(self):
        markers = named_aim("user")
        self.assertEqual(['[HW:/servo/aim:{"direction":"user"}]'], markers)

    def test_unknown_direction_fails(self):
        with self.assertRaises(MotionError):
            named_aim("behind_you")

    def test_raw_joints_fail_closed(self):
        with self.assertRaises(MotionError):
            validate_markers(['[HW:/servo/aim:{"base_yaw.pos":-90}]'])

    def test_set_joint_token_forbidden(self):
        self.assertIn("set_joint", FORBIDDEN)
        with self.assertRaises(MotionError):
            validate_markers(["[HW:/servo/set:{}]"])

    def test_still_nine_events(self):
        self.assertEqual(9, len(EVENTS))
        self.assertNotIn("look", EVENTS)
        self.assertNotIn("aim", EVENTS)
        self.assertNotIn("hatch", EVENTS)
        self.assertNotIn("dance", EVENTS)

    def test_learned_slot_falls_back_to_named(self):
        os.environ["ABP_AIM_POLICY"] = "learned"
        try:
            self.assertEqual(named_aim("center"), aim("center"))
        finally:
            os.environ.pop("ABP_AIM_POLICY", None)


if __name__ == "__main__":
    unittest.main()
