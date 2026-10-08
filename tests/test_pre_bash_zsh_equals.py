"""Black-box contracts for the PreToolUse hook that stops zsh `=` expansion failures."""

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

HOOK = Path(__file__).resolve().parents[1] / "hooks/pre-bash-zsh-equals.py"

BLOCKED = {
    "bare separator": "echo =====",
    "middle of a list": "cat a; echo =====; cat b",
    "after other arguments": 'echo "--- x ---" && echo ---- ==== foo',
    "printf argument": "printf '%s\\n' ====",
    "inside if": "if true; then echo ====; fi",
    "quote after the equals": 'echo ==="title"',
    "after a heredoc": "python3 - <<'EOF'\nprint(1 == 1)\nEOF\necho =====",
    "after an env assignment": "LANG=C echo ==== x",
    "in a subshell": "(cd /tmp && echo ====)",
    "after a quoted substitution": 'echo "$f: $(grep -c x $f)"; echo ====',
    "after a parameter expansion": "echo ${x} ====",
    "after a command substitution": "echo $(date) ====",
    "inside a command substitution": "x=$(echo ====)",
}

ALLOWED = {
    "single quoted": "echo '====='",
    "double quoted": 'echo "====="',
    "heredoc body": "python3 - <<'EOF'\nif a == b:\n    pass\necho ====\nEOF",
    "heredoc with dash": "cat <<-EOF\n\techo ====\n\tEOF\necho done",
    "double bracket test": "[[ a == b ]] && echo ok",
    "equals inside a word": "echo a=====b",
    "comment": "echo x # =====",
    "single equals": "echo = x",
    "quoted format": "git log --format='%h == %s'",
    "escaped": "echo \\=\\=\\=",
    "here string": 'cat <<<"=== x"',
    "other command": "grep -c ==== file.txt",
    "apostrophe in heredoc": "cat <<EOF\ndon't echo ====\nEOF",
    "quotes nested in a substitution": 'echo "$(git log -1 --format="%h == %s")"',
    "quotes nested in backticks": 'echo "`git log -1 --format="%h == %s"`"',
    "arithmetic": "echo $(( 1 == 1 ))",
    "old arithmetic": "echo $[ 1 == 1 ]",
    "nested quotes after a parenthesis": 'echo "sum (a+b): $(echo "== 3 ==")"',
    "nested quotes after a closed substitution": 'echo "$(cat /dev/null) (note) $(echo "== z ==")"',
    "nested quotes inside awk": """echo "$(awk '{print ($1) "x == y"}' /dev/null)\"""",
    "nested quotes in a parameter default": 'echo "${x:-"== d =="}"',
}


def run(payload, shell="/bin/zsh"):
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=payload,
        capture_output=True,
        text=True,
        env=dict(os.environ, SHELL=shell),
    )


def bash(command, **kwargs):
    return run(json.dumps({"tool_name": "Bash", "tool_input": {"command": command}}), **kwargs)


class PreBashZshEqualsTests(unittest.TestCase):
    def test_should_block_unquoted_equals_words_passed_to_echo(self):
        for name, command in BLOCKED.items():
            with self.subTest(name):
                done = bash(command)
                self.assertEqual(done.returncode, 2, done.stderr)
                self.assertIn("引用符", done.stderr)
                self.assertEqual(done.stdout, "")

    def test_should_show_the_word_to_quote(self):
        self.assertIn("echo '====='", bash("echo =====").stderr)
        self.assertIn("「=====VALID」", bash("echo =====VALID").stderr)
        self.assertIn("「====QUERY」", bash('echo ====QUERY"x"').stderr)

    def test_should_allow_commands_zsh_runs_without_expansion(self):
        for name, command in ALLOWED.items():
            with self.subTest(name):
                done = bash(command)
                self.assertEqual((done.returncode, done.stderr), (0, ""))

    def test_should_not_check_when_shell_is_not_zsh(self):
        self.assertEqual(bash("echo =====", shell="/bin/bash").returncode, 0)

    def test_should_allow_when_input_is_unreadable(self):
        for payload in ("", "{not json", "[]", json.dumps({"tool_input": {}}), json.dumps({"tool_input": {"command": 7}})):
            with self.subTest(payload=payload):
                self.assertEqual(run(payload).returncode, 0)


if __name__ == "__main__":
    unittest.main()
