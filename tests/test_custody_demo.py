import tempfile
import unittest
from pathlib import Path

from scripts.custody_demo import FAKE_OWNER, run


class CustodyDemoTests(unittest.TestCase):
    def test_missing_leftover_host_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(SystemExit):
                run("10.0.0.8", "", Path(tmp))
            with self.assertRaises(SystemExit):
                run("127.0.0.1", "127.0.0.1", Path(tmp))

    def test_fixture_names_are_fake(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run("10.0.0.8", "10.0.0.9", Path(tmp))
        self.assertEqual(FAKE_OWNER, result["owner"])
        blob = str(result).lower()
        self.assertNotIn("jenna", blob)
        self.assertNotIn("mailloux", blob)

    def test_phrase_fallback_label_is_visible(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run("10.0.0.8", "10.0.0.9", Path(tmp))
        self.assertEqual("phrase-fallback", result["phrase_source"])

    def test_demo_does_not_claim_liveness_or_tpm(self):
        text = Path("scripts/custody_demo.py").read_text().lower()
        self.assertNotIn("measured boot", text)
        self.assertNotIn("liveness", text)
        self.assertNotIn("tpm", text)

    def test_signed_update_does_not_reopen_leftover(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run("10.0.0.8", "10.0.0.9", Path(tmp))
        self.assertTrue(result["signed_apply"])
        self.assertTrue(result["leftover_after_ota"])
        self.assertTrue(result["vendor_camera_denied"])
        self.assertTrue(result["frozen_refuse"])
        self.assertTrue(result["peer_event"])
        self.assertTrue(result["peer_camera_denied"])


if __name__ == "__main__":
    unittest.main()
