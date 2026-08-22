import unittest

from mapper.skills import SKILLS, SkillError, markers_for


class SkillVerbTests(unittest.TestCase):
    def test_four_named_skills(self):
        self.assertEqual({"look", "follow", "dance", "stop"}, set(SKILLS))

    def test_look_is_named_aim(self):
        self.assertEqual(['[HW:/servo/aim:{"direction":"user"}]'], markers_for("look"))

    def test_follow_aims_then_tracks_person(self):
        self.assertEqual(
            [
                '[HW:/servo/aim:{"direction":"user"}]',
                '[HW:/servo/track:{"target":["person"]}]',
            ],
            markers_for("follow"),
        )

    def test_dance_is_stock_recording(self):
        self.assertEqual(['[HW:/servo/play:{"recording":"happy_wiggle"}]'], markers_for("dance"))

    def test_unknown_and_raw_joints_fail(self):
        with self.assertRaises(SkillError):
            markers_for("moonwalk")
        blob = "".join(sum((list(m) for m in SKILLS.values()), []))
        self.assertNotIn("set_joint", blob)
        self.assertNotIn("wrist_pitch", blob)


if __name__ == "__main__":
    unittest.main()
