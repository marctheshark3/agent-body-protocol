import unittest

from mapper.serve import EVENTS
from mapper.skills import QI_REFUSE, SKILLS, SkillError, markers_for, qi_refuse_reason
from mapper.virtual_body import AIM, HOP, VirtualBody


class SkillVerbTests(unittest.TestCase):
    def test_five_named_skills(self):
        self.assertEqual({"look", "follow", "dance", "hatch", "stop"}, set(SKILLS))
        self.assertNotIn("hatch", EVENTS)
        self.assertEqual(9, len(EVENTS))

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

    def test_hatch_hops_then_looks(self):
        markers = markers_for("hatch")
        self.assertEqual(
            [
                '[HW:/servo/play:{"recording":"wake_up"}]',
                '[HW:/servo/aim:{"direction":"user"}]',
            ],
            markers,
        )
        blob = "".join(markers)
        self.assertIn("/servo/play", blob)
        self.assertIn("wake_up", blob)
        self.assertIn("/servo/aim", blob)
        self.assertIn("user", blob)
        self.assertNotIn("/led", blob)
        self.assertNotIn("happy_wiggle", blob)
        self.assertGreaterEqual(len(markers), 2)

    def test_hatch_moves_joints_hop_then_look(self):
        body = VirtualBody("near")
        rest = dict(body.pose)
        hop, look = markers_for("hatch")
        body.apply_markers([hop], "hatch")
        self.assertNotEqual(rest, body.pose)
        self.assertEqual(HOP, body.pose)
        hopped = dict(body.pose)
        body.apply_markers([look], "hatch")
        self.assertNotEqual(hopped, body.pose)
        self.assertEqual(AIM["user"], body.pose)

    def test_dance_on_qi_refuses_wiggle(self):
        qi = {
            "v": 1, "kind": "power", "ts": "2026-08-25T15:00:00Z",
            "voltage_v": 5.0, "source": "qi", "origin": "sim",
            "charging": True, "docked": True, "low": False, "power_w": 5.0,
        }
        blob = "".join(markers_for("dance", power=qi))
        self.assertEqual([], markers_for("dance", power=qi))
        self.assertNotIn("happy_wiggle", blob)
        self.assertEqual("qi-cannot-dance", qi_refuse_reason("dance", qi))

    def test_hatch_on_qi_refuses_hop(self):
        qi = {
            "v": 1, "kind": "power", "ts": "2026-08-25T15:00:00Z",
            "voltage_v": 5.0, "source": "qi", "origin": "sim",
            "charging": True, "docked": True, "low": False, "power_w": 5.0,
        }
        self.assertEqual([], markers_for("hatch", power=qi))
        self.assertEqual("qi-cannot-hatch", qi_refuse_reason("hatch", qi))
        self.assertEqual("qi-cannot-hatch", QI_REFUSE["hatch"])
        mains = {
            "v": 1, "kind": "power", "ts": "2026-08-25T15:00:00Z",
            "voltage_v": 12.0, "source": "mains", "origin": "sim",
            "charging": False, "docked": True, "low": False, "power_w": None,
        }
        self.assertEqual(2, len(markers_for("hatch", power=mains)))
        battery = {
            "v": 1, "kind": "power", "ts": "2026-08-25T15:00:00Z",
            "voltage_v": 11.1, "source": "battery", "origin": "sim",
            "charging": False, "docked": False, "low": False, "power_w": None,
        }
        self.assertEqual(2, len(markers_for("hatch", power=battery)))

    def test_unknown_and_raw_joints_fail(self):
        with self.assertRaises(SkillError):
            markers_for("moonwalk")
        blob = "".join(sum((list(m) for m in SKILLS.values()), []))
        self.assertNotIn("set_joint", blob)
        self.assertNotIn("wrist_pitch", blob)


if __name__ == "__main__":
    unittest.main()
