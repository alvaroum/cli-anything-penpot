import json
import os
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner
from cli_anything.penpot.cli import cli
from cli_anything.penpot.config import Config


class PenpotHandler(BaseHTTPRequestHandler):
    calls = []

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        body = json.loads(self.rfile.read(length) or b"{}")
        method = self.path.rsplit("/", 1)[-1]
        self.__class__.calls.append((method, body, self.headers.get("Authorization")))
        responses = {
            "get-profile": {"id": "profile-1", "email": "agent@example.test"},
            "get-owned-teams": [{"id": "team-1", "name": "Design"}],
            "get-projects": [{"id": "project-1", "teamId": body.get("teamId")}],
            "get-project-files": [{"id": "file-1", "projectId": body.get("projectId")}],
            "get-page": {"id": body.get("fileId"), "page": {}},
        }
        result = responses.get(method, {"method": method, "body": body})
        encoded = json.dumps(result).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, *_args):
        pass


class IntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), PenpotHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.thread.join()
        cls.server.server_close()

    def setUp(self):
        PenpotHandler.calls.clear()
        self.runner = CliRunner()
        self.env = {
            "PENPOT_SERVER": f"http://127.0.0.1:{self.server.server_port}",
            "PENPOT_TOKEN": "test-token",
        }

    def test_status_json_and_auth(self):
        result = self.runner.invoke(cli, ["--json", "status"], env=self.env)
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertEqual(json.loads(result.output)["id"], "profile-1")
        self.assertEqual(PenpotHandler.calls[-1][2], "Token test-token")

    def test_workspace_inspection_commands(self):
        for args, key in [
            (["teams", "list", "--json"], "team-1"),
            (["projects", "list", "--team-id", "team-1", "--json"], "project-1"),
            (["files", "list", "--project-id", "project-1", "--json"], "file-1"),
            (["file", "page", "--file-id", "file-1", "--json"], "file-1"),
        ]:
            result = self.runner.invoke(cli, args, env=self.env)
            self.assertEqual(result.exit_code, 0, result.output)
            self.assertIn(key, result.output)

    def test_missing_setup_is_actionable(self):
        with tempfile.TemporaryDirectory() as directory:
            env = {"PENPOT_CONFIG": str(Path(directory) / "missing.json")}
            result = self.runner.invoke(cli, ["status"], env=env)
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("config init", result.output)

    def test_config_show_redacts_token(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text(json.dumps({"server": "https://example.test", "token": "do-not-print"}))
            result = self.runner.invoke(cli, ["config", "show", "--json"], env={"PENPOT_CONFIG": str(path)})
        self.assertEqual(result.exit_code, 0)
        self.assertNotIn("do-not-print", result.output)
        self.assertEqual(json.loads(result.output)["token"], "<redacted>")
    def test_first_run_default_prompts_before_repl(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {}, clear=False):
            os.environ.pop("PENPOT_SERVER", None)
            os.environ.pop("PENPOT_TOKEN", None)
            config_path = Path(directory) / "config.json"
            with patch("cli_anything.penpot.cli.default_config_path", return_value=config_path), \
                 patch("cli_anything.penpot.cli.prompt_config", return_value=Config("https://example.test", "secret")) as prompt, \
                 patch("cli_anything.penpot.cli.save_config", return_value=config_path), \
                 patch("cli_anything.penpot.cli.ReplSkin.create_prompt_session", return_value=None), \
                 patch("cli_anything.penpot.cli.ReplSkin.get_input", side_effect=["quit"]):
                result = self.runner.invoke(cli, [])
        self.assertEqual(result.exit_code, 0, result.output)
        prompt.assert_called_once()


if __name__ == "__main__":
    unittest.main()
