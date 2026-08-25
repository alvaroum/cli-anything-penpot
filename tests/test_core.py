import json
import os
import stat
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cli_anything.penpot.api import ApiError, PenpotApi
from cli_anything.penpot.config import Config, ConfigError, load_config, normalize_server, save_config


class ConfigTests(unittest.TestCase):
    def test_normalize_server(self):
        self.assertEqual(normalize_server("penpot.example/api/main/methods/"), "https://penpot.example")
        self.assertEqual(normalize_server("http://localhost:9001/"), "http://localhost:9001")

    def test_reject_invalid_server(self):
        with self.assertRaises(ConfigError):
            normalize_server("ftp://example.test")
        with self.assertRaises(ConfigError):
            normalize_server("")

    def test_save_load_owner_only(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            config = Config("https://penpot.example", "secret")
            save_config(config, path)
            self.assertEqual(load_config(path), config)
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), stat.S_IRUSR | stat.S_IWUSR)

    def test_malformed_config(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text("not json")
            with self.assertRaises(ConfigError):
                load_config(path)

    def test_environment_requires_pair(self):
        with patch.dict(os.environ, {"PENPOT_SERVER": "https://example.test"}, clear=False), patch("cli_anything.penpot.config.default_config_path", return_value=Path("/missing")):
            os.environ.pop("PENPOT_TOKEN", None)
            with self.assertRaises(ConfigError):
                load_config()


class ApiTests(unittest.TestCase):
    def test_post_uses_token_header_and_json(self):
        class Response:
            status = 200
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self): return b'{"ok":true}'

        with patch("cli_anything.penpot.api.urllib.request.urlopen", return_value=Response()) as open_url:
            result = PenpotApi(Config("https://example.test", "abc")).post("get-profile")
        request = open_url.call_args.args[0]
        self.assertEqual(request.get_header("Authorization"), "Token abc")
        self.assertEqual(json.loads(request.data), {})
        self.assertEqual(result, {"ok": True})

    def test_verify_token_sends_body_without_auth_header(self):
        class Response:
            status = 200
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self): return b'{}'

        with patch("cli_anything.penpot.api.urllib.request.urlopen", return_value=Response()) as open_url:
            PenpotApi(Config("https://example.test", "abc")).verify_token()
        request = open_url.call_args.args[0]
        self.assertIsNone(request.get_header("Authorization"))
        self.assertEqual(json.loads(request.data), {"token": "abc"})

    def test_http_error_becomes_api_error(self):
        from urllib.error import HTTPError
        error = HTTPError("https://example.test", 401, "Unauthorized", {}, None)
        error.read = lambda: b'{"type":"unauthorized"}'
        with patch("cli_anything.penpot.api.urllib.request.urlopen", side_effect=error):
            with self.assertRaisesRegex(ApiError, "HTTP 401"):
                PenpotApi(Config("https://example.test", "abc")).profile()


if __name__ == "__main__":
    unittest.main()
