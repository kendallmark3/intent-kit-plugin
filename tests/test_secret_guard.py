"""Tests for the intent-kit secret guard. Standard library only.

Run from the repository root:  python3 -m unittest discover -s tests -v
"""
import json
import os
import subprocess
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGIN = os.path.join(ROOT, "plugins", "intent-kit")
LAUNCHER = os.path.join(PLUGIN, "scripts", "run-python.sh")
GUARD = os.path.join(PLUGIN, "scripts", "secret_guard.py")

# Assembled at runtime so this file never contains a literal credential.
AWS_KEY = "AKIA" + "Q7RZ4MXN2KTB5WPL"
GH_TOKEN = "ghp_" + "a1B2c3D4e5F6g7H8i9J0k1L2m3N4o5P6q7R8"
ANTHROPIC_KEY = "sk-ant-" + "api03-Zx9Yw8Vu7Ts6Rq5Po4Nm3Lk2"
PRIVATE_KEY = "-----BEGIN RSA " + "PRIVATE KEY-----"


def run_hook(mode, payload, cwd=None):
    """Run the hook exactly as hooks.json does: sh launcher -> python -> guard."""
    return subprocess.run(
        ["sh", LAUNCHER, GUARD, mode],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        cwd=cwd,
        timeout=30,
    )


def write_payload(content, path="/tmp/app/config.py", cwd=None):
    return {"tool_name": "Write", "tool_input": {"file_path": path, "content": content}, "cwd": cwd or "/tmp"}


class PreToolUse(unittest.TestCase):
    def assertBlocked(self, result, kind):
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn(kind, result.stderr)  # reason must reach Claude via stderr

    def test_blocks_known_token_formats(self):
        for content, kind in [
            (f'key = "{AWS_KEY}"', "AWS access key"),
            (f"token: {GH_TOKEN}", "GitHub token"),
            (f"ANTHROPIC_API_KEY={ANTHROPIC_KEY}", "Anthropic API key"),
            (PRIVATE_KEY, "private key"),
        ]:
            with self.subTest(kind=kind):
                self.assertBlocked(run_hook("pre", write_payload(content)), kind)

    def test_blocks_json_style_assignment(self):
        content = '{\n  "api_key": "' + "q8Zr2Lk9Vb3Nm7Xc" + '"\n}'
        self.assertBlocked(run_hook("pre", write_payload(content, "/tmp/app/settings.json")), "hard-coded secret")

    def test_blocks_prefixed_names(self):
        content = 'CLIENT_SECRET = "' + "Hn4Pq8Ws2Kd6Yt1Z" + '"'
        self.assertBlocked(run_hook("pre", write_payload(content)), "hard-coded secret")

    def test_checks_edit_and_multiedit(self):
        edit = {"tool_name": "Edit", "cwd": "/tmp", "tool_input": {"file_path": "/tmp/a.py", "old_string": "x", "new_string": f"k = '{AWS_KEY}'"}}
        self.assertBlocked(run_hook("pre", edit), "AWS access key")
        multi = {"tool_name": "MultiEdit", "cwd": "/tmp", "tool_input": {"file_path": "/tmp/a.py", "edits": [{"old_string": "a", "new_string": "ok"}, {"old_string": "b", "new_string": GH_TOKEN}]}}
        self.assertBlocked(run_hook("pre", multi), "GitHub token")

    def test_allows_clean_code_and_placeholders(self):
        for content in [
            "import os\napi_key = os.environ['API_KEY']\n",
            'API_KEY = "your-api-key-here"',
            'password = "${DB_PASSWORD}"',
            'secret: "<set in vault>"',
            "aws_access_key_id = AKIAIOSFODNN7EXAMPLE",
            'password = "a sentence with spaces in it"',
            "if password == other_password:\n    pass",
            "def risk_assessment_for_production_systems(): pass",
        ]:
            with self.subTest(content=content):
                result = run_hook("pre", write_payload(content))
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_allow_marker(self):
        content = f'FIXTURE = "{AWS_KEY}"  # intent-kit: allow-secret'
        self.assertEqual(run_hook("pre", write_payload(content)).returncode, 0)

    def test_allows_writes_to_git_ignored_files(self):
        with tempfile.TemporaryDirectory() as repo:
            subprocess.run(["git", "init", "-q", repo], check=True)
            with open(os.path.join(repo, ".gitignore"), "w") as handle:
                handle.write(".env\n")
            env_path = os.path.join(repo, ".env")
            result = run_hook("pre", write_payload(f"AWS_ACCESS_KEY_ID={AWS_KEY}", env_path, repo), cwd=repo)
            self.assertEqual(result.returncode, 0, result.stderr)
            tracked = os.path.join(repo, "config.py")
            self.assertEqual(run_hook("pre", write_payload(f"k='{AWS_KEY}'", tracked, repo), cwd=repo).returncode, 2)

    def test_bad_input_fails_open(self):
        result = subprocess.run(["sh", LAUNCHER, GUARD, "pre"], input="not json", capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn("skipped", result.stdout)


class Stop(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = self.tmp.name
        subprocess.run(["git", "init", "-q", self.repo], check=True)
        subprocess.run(["git", "-C", self.repo, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "--allow-empty", "-m", "init"], check=True)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, name, content):
        with open(os.path.join(self.repo, name), "w") as handle:
            handle.write(content)

    def stop(self, active=False):
        result = run_hook("stop", {"cwd": self.repo, "stop_hook_active": active}, cwd=self.repo)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout) if result.stdout.strip() else {}

    def test_clean_repo_allows_stop(self):
        self.write("app.py", "print('hello')\n")
        self.assertEqual(self.stop(), {})

    def test_catches_untracked_new_file(self):
        self.write("creds.py", f"KEY = '{AWS_KEY}'\n")
        out = self.stop()
        self.assertEqual(out.get("decision"), "block")
        self.assertIn("creds.py", out["reason"])

    def test_catches_modified_tracked_file(self):
        self.write("app.py", "x = 1\n")
        subprocess.run(["git", "-C", self.repo, "add", "app.py"], check=True)
        subprocess.run(["git", "-C", self.repo, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "app"], check=True)
        self.write("app.py", f"x = 1\ntoken = '{GH_TOKEN}'\n")
        self.assertEqual(self.stop().get("decision"), "block")

    def test_ignored_files_are_skipped(self):
        self.write(".gitignore", ".env\n")
        self.write(".env", f"AWS_ACCESS_KEY_ID={AWS_KEY}\n")
        self.assertEqual(self.stop(), {})

    def test_second_stop_only_warns(self):
        self.write("creds.py", f"KEY = '{AWS_KEY}'\n")
        out = self.stop(active=True)
        self.assertNotIn("decision", out)
        self.assertIn("creds.py", out["systemMessage"])

    def test_outside_git_is_a_no_op(self):
        with tempfile.TemporaryDirectory() as plain:
            result = run_hook("stop", {"cwd": plain}, cwd=plain)
            self.assertEqual((result.returncode, result.stdout.strip()), (0, ""))


class Manifest(unittest.TestCase):
    def test_hook_commands_use_launcher_not_bare_python(self):
        with open(os.path.join(PLUGIN, "hooks", "hooks.json")) as handle:
            hooks = json.load(handle)["hooks"]
        commands = [h["command"] for groups in hooks.values() for group in groups for h in group["hooks"]]
        self.assertEqual(len(commands), 2)
        for command in commands:
            self.assertTrue(command.startswith('sh "${CLAUDE_PLUGIN_ROOT}/scripts/run-python.sh"'), command)


if __name__ == "__main__":
    unittest.main()
