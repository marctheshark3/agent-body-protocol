import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(relative: str, name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load adapter: {relative}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class AdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.claude = load("adapters/claude-code/hook.py", "claude_hook")
        cls.hermes = load("adapters/hermes/mcp_server.py", "hermes_mcp")

    def test_claude_hook_classification(self):
        cases = (
            ("SessionStart", {}, "started"),
            ("PermissionRequest", {}, "permission_required"),
            ("Notification", {"message": "Claude needs you"}, "permission_required"),
            ("Stop", {"result": "14 tests passed"}, "tests_passed"),
            ("Stop", {"result": "2 tests failed"}, "tests_failed"),
            ("Stop", {"result": "done"}, "completed"),
            ("PostToolUseFailure", {}, "blocked"),
        )
        for hook, payload, expected in cases:
            with self.subTest(hook=hook, expected=expected):
                self.assertEqual(expected, self.claude.classify(hook, payload))

    def test_hermes_lists_agent_body_emit(self):
        response = self.hermes.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
        self.assertEqual("agent_body_emit", response["result"]["tools"][0]["name"])

    def test_hermes_notification_has_no_response(self):
        self.assertIsNone(self.hermes.handle({"jsonrpc": "2.0", "method": "notifications/initialized"}))


if __name__ == "__main__":
    unittest.main()
