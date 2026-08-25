"""Credential-gated live backend test; ordinary CI runs unit/integration tests only."""

import json
import os
import shutil
import subprocess
import unittest


def _resolve_cli(name):
    force = os.environ.get("CLI_ANYTHING_FORCE_INSTALLED") == "1"
    path = shutil.which(name)
    if path:
        return [path]
    if force:
        raise RuntimeError(f"{name} not found; install the package first")
    return [os.environ.get("PYTHON", "python3"), "-m", "cli_anything.penpot"]


@unittest.skipUnless(os.environ.get("PENPOT_SERVER") and os.environ.get("PENPOT_TOKEN"), "requires PENPOT_SERVER and PENPOT_TOKEN")
class LivePenpotWorkflow(unittest.TestCase):
    def test_status_and_teams_use_live_backend(self):
        command = _resolve_cli("cli-anything-penpot")
        env = os.environ.copy()
        status = subprocess.run(command + ["--json", "status"], env=env, capture_output=True, text=True)
        self.assertEqual(status.returncode, 0, status.stderr)
        profile = json.loads(status.stdout)
        self.assertIsInstance(profile, dict)
        teams = subprocess.run(command + ["--json", "teams", "list"], env=env, capture_output=True, text=True)
        self.assertEqual(teams.returncode, 0, teams.stderr)
        self.assertIsInstance(json.loads(teams.stdout), (dict, list))


if __name__ == "__main__":
    unittest.main()
