"""Tests for caveman-mode-tracker.js prompt parsing (issues #598, #599).

Drives the UserPromptSubmit hook with real prompts over stdin against an
isolated CLAUDE_CONFIG_DIR and asserts the flag-file state afterwards.

#598: natural-language triggers misfired — "turn caveman mode off"
ACTIVATED caveman (and clobbered the level to default), "turn caveman off"
was a no-op, questions about caveman armed it, and vim's "normal mode"
deactivated it.

#599: one-shot independent modes (/caveman-commit etc.) permanently
overwrote the active prose level, and the plugin-namespaced
/caveman:caveman-commit|-review variants were not recognized at all.

#537: Claude Code delivers slash commands as a <command-message>/
<command-name>/<command-args> envelope, not the literal command string.
The startsWith('/caveman') gate never matched it, so every level switch
AND '/caveman off' from the real slash UI was a silent no-op.
"""

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TRACKER = REPO_ROOT / "src" / "hooks" / "caveman-mode-tracker.js"


class ModeTrackerTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="caveman-tracker-")
        self.claude_dir = Path(self._tmp.name) / ".claude"
        self.claude_dir.mkdir(parents=True)
        self.flag = self.claude_dir / ".caveman-active"
        self.prev = self.claude_dir / ".caveman-active.prev"

    def tearDown(self):
        self._tmp.cleanup()

    def send(self, prompt, cwd=None):
        env = os.environ.copy()
        env.pop("CAVEMAN_DEFAULT_MODE", None)
        # Scrub XDG_CONFIG_HOME too: getConfigDir() prefers it over HOME, so a
        # developer's real caveman user config (e.g. defaultMode "off") would
        # otherwise leak into these assertions.
        env.pop("XDG_CONFIG_HOME", None)
        env["HOME"] = self._tmp.name
        env["USERPROFILE"] = self._tmp.name
        env["CLAUDE_CONFIG_DIR"] = str(self.claude_dir)
        payload = {"prompt": prompt}
        if cwd is not None:
            payload["cwd"] = str(cwd)
        return subprocess.run(
            ["node", str(TRACKER)],
            cwd=REPO_ROOT,
            env=env,
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            check=True,
        )

    def flag_value(self):
        return self.flag.read_text() if self.flag.exists() else None

    # ── #598: deactivation word orders ──────────────────────────────────

    def test_turn_caveman_mode_off_deactivates(self):
        # Pre-fix: this ACTIVATED caveman and downgraded ultra -> full.
        self.flag.write_text("ultra")
        self.send("turn caveman mode off")
        self.assertIsNone(self.flag_value())

    def test_turn_caveman_off_deactivates(self):
        self.flag.write_text("full")
        self.send("turn caveman off")
        self.assertIsNone(self.flag_value())

    def test_turn_off_caveman_deactivates(self):
        self.flag.write_text("full")
        self.send("turn off caveman")
        self.assertIsNone(self.flag_value())

    def test_stop_caveman_multiline_deactivates(self):
        # Pre-fix: `.*` without the s flag never matched across lines.
        self.flag.write_text("ultra")
        self.send("stop\ncaveman")
        self.assertIsNone(self.flag_value())

    def test_normal_mode_command_deactivates(self):
        self.flag.write_text("full")
        self.send("normal mode")
        self.assertIsNone(self.flag_value())

    def test_back_to_normal_mode_deactivates(self):
        self.flag.write_text("full")
        self.send("back to normal mode please")
        self.assertIsNone(self.flag_value())

    def test_vim_normal_mode_does_not_deactivate(self):
        self.flag.write_text("full")
        self.send("how do I exit vim normal mode")
        self.assertEqual(self.flag_value(), "full")

    # ── #598: activation guards ─────────────────────────────────────────

    def test_enable_caveman_with_stop_elsewhere_activates(self):
        # Pre-fix: "stop" anywhere suppressed activation, then the
        # deactivation regex matched "caveman and stop" and deleted the flag.
        self.flag.write_text("full")
        self.send("enable caveman and stop apologizing")
        self.assertEqual(self.flag_value(), "full")

    def test_question_does_not_activate(self):
        self.send("what is caveman mode?")
        self.assertIsNone(self.flag_value())
        self.send("does caveman lite mode drop articles?")
        self.assertIsNone(self.flag_value())

    def test_scoped_brevity_does_not_activate(self):
        self.send("be brief in the summary section")
        self.assertIsNone(self.flag_value())

    # ── E6: one-off brevity is not a mode switch ────────────────────────

    def test_bare_brevity_does_not_activate(self):
        # E6: "be brief" / "less tokens" alone is a single-response
        # instruction — it must NOT flip the persistent session flag.
        self.send("be brief")
        self.assertIsNone(self.flag_value())
        self.send("less tokens")
        self.assertIsNone(self.flag_value())
        self.send("be terse please")
        self.assertIsNone(self.flag_value())

    def test_brevity_with_incidental_always_does_not_activate(self):
        # "always" about something else must not count as a durable marker.
        self.send("tests always fail on ci, be brief")
        self.assertIsNone(self.flag_value())

    def test_durable_brevity_activates(self):
        self.send("always be brief")
        self.assertEqual(self.flag_value(), "full")
        self.flag.unlink()
        self.send("from now on, be brief")
        self.assertEqual(self.flag_value(), "full")

    def test_brevity_from_now_on_activates(self):
        self.send("use fewer tokens from now on")
        self.assertEqual(self.flag_value(), "full")

    def test_brevity_for_this_session_activates(self):
        self.send("shorter answers for this session")
        self.assertEqual(self.flag_value(), "full")

    def test_use_caveman_still_works(self):
        self.send("use caveman")
        self.assertEqual(self.flag_value(), "full")

    def test_activate_caveman_still_works(self):
        self.send("activate caveman")
        self.assertEqual(self.flag_value(), "full")

    def test_turn_on_caveman_mode_still_works(self):
        self.send("turn on caveman mode")
        self.assertEqual(self.flag_value(), "full")

    def test_talk_like_caveman_still_works(self):
        self.send("talk like a caveman")
        self.assertEqual(self.flag_value(), "full")

    def test_bare_caveman_mode_still_works(self):
        self.send("caveman mode")
        self.assertEqual(self.flag_value(), "full")

    # ── slash commands ──────────────────────────────────────────────────

    def test_slash_caveman_level_switch(self):
        self.send("/caveman ultra")
        self.assertEqual(self.flag_value(), "ultra")

    # ── #629/#630 (adapted): smart level ────────────────────────────────

    def test_slash_caveman_smart_switch(self):
        self.send("/caveman smart")
        self.assertEqual(self.flag_value(), "smart")

    def test_smart_reinforcement_names_level_without_grammar_compression(self):
        # smart = cut content, not grammar. The per-turn anchor (slimmed by
        # #660 to a generic re-pointer at the SessionStart ruleset) must name
        # the level and must NOT re-inject grammar-compression instructions —
        # that is the exact standing conflict smart exists to eliminate.
        self.flag.write_text("smart")
        r = self.send("ordinary follow-up question")
        self.assertIn("CAVEMAN MODE ACTIVE (smart)", r.stdout)
        self.assertNotIn("Drop articles", r.stdout)
        self.assertNotIn("Fragments OK", r.stdout)

    def test_slash_caveman_off(self):
        self.flag.write_text("full")
        self.send("/caveman off")
        self.assertIsNone(self.flag_value())

    # ── #599: one-shot independent modes ────────────────────────────────

    def test_commit_restores_prior_level_on_next_prompt(self):
        self.flag.write_text("ultra")
        self.send("/caveman-commit")
        self.assertEqual(self.flag_value(), "commit")
        r = self.send("ordinary follow-up question")
        self.assertEqual(self.flag_value(), "ultra")
        self.assertIn("CAVEMAN MODE ACTIVE (ultra)", r.stdout)

    def test_commit_with_no_prior_mode_deactivates_after(self):
        self.send("/caveman-commit")
        self.assertEqual(self.flag_value(), "commit")
        r = self.send("ordinary follow-up question")
        self.assertIsNone(self.flag_value())
        self.assertNotIn("CAVEMAN MODE ACTIVE", r.stdout)

    def test_chained_independent_modes_keep_original_prev(self):
        self.flag.write_text("wenyan-ultra")
        self.send("/caveman-commit")
        self.send("/caveman-review")
        self.assertEqual(self.flag_value(), "review")
        self.send("ordinary follow-up question")
        self.assertEqual(self.flag_value(), "wenyan-ultra")

    def test_namespaced_commit_and_review_recognized(self):
        # Pre-fix: only compress and stats had the /caveman:caveman- variant.
        self.flag.write_text("full")
        self.send("/caveman:caveman-commit")
        self.assertEqual(self.flag_value(), "commit")
        self.send("next prompt")  # restore
        self.send("/caveman:caveman-review")
        self.assertEqual(self.flag_value(), "review")

    def test_no_reinforcement_during_independent_turn(self):
        self.flag.write_text("full")
        r = self.send("/caveman-commit")
        self.assertNotIn("CAVEMAN MODE ACTIVE", r.stdout)

    def test_deactivation_clears_saved_prev(self):
        self.flag.write_text("ultra")
        self.send("/caveman-commit")
        self.send("stop caveman")
        self.assertIsNone(self.flag_value())
        self.assertFalse(self.prev.exists(), "prev file must not survive deactivation")
        self.send("ordinary prompt")
        self.assertIsNone(self.flag_value(), "nothing should resurrect the mode")

    # ── #537: Claude Code slash-command envelope unwrap ─────────────────

    @staticmethod
    def envelope(name, args, newlines=False):
        sep = "\n" if newlines else ""
        return (
            f"<command-message>{name.lstrip('/')}</command-message>{sep}"
            f"<command-name>{name}</command-name>{sep}"
            f"<command-args>{args}</command-args>"
        )

    def test_envelope_one_line_switches_level(self):
        # Audit probe B2: envelope args=smart with preset full. Pre-fix the
        # flag stayed 'full' and reinforcement kept naming the old level.
        self.flag.write_text("full")
        r = self.send(self.envelope("/caveman", "smart"))
        self.assertEqual(self.flag_value(), "smart")
        self.assertIn("CAVEMAN MODE ACTIVE (smart)", r.stdout)

    def test_envelope_one_line_activates_without_preset(self):
        # Audit probe B1: envelope args=smart, no flag preset. Pre-fix the
        # flag stayed absent — activation via the slash UI was dead.
        self.send(self.envelope("/caveman", "smart"))
        self.assertEqual(self.flag_value(), "smart")

    def test_envelope_newline_form_switches_level(self):
        # Audit probe B3: the exact newline-separated form from issue #537.
        self.flag.write_text("full")
        self.send(self.envelope("/caveman", "ultra", newlines=True))
        self.assertEqual(self.flag_value(), "ultra")

    def test_envelope_off_deactivates(self):
        # Audit probe B4: '/caveman off' via envelope must delete the flag.
        # Pre-fix deactivation was dead too — worse than a stuck level.
        self.flag.write_text("full")
        self.send(self.envelope("/caveman", "off", newlines=True))
        self.assertIsNone(self.flag_value())

    def test_envelope_stats_passthrough_does_not_touch_flag(self):
        # /caveman-stats via envelope must reach the stats branch (block
        # decision) and must not disturb the active level.
        self.flag.write_text("full")
        r = self.send(self.envelope("/caveman-stats", "", newlines=True))
        self.assertEqual(self.flag_value(), "full")
        self.assertIn('"decision":"block"', r.stdout)

    def test_envelope_non_level_arg_does_not_flip(self):
        # Non-level arg = task at current level; no silent flag overwrite —
        # same contract as raw-typed '/caveman <non-level>'.
        self.flag.write_text("ultra")
        self.send(self.envelope("/caveman", "explain connection pooling"))
        self.assertEqual(self.flag_value(), "ultra")

    def test_raw_typed_command_still_works_after_unwrap(self):
        # The literal path must stay intact alongside the envelope path.
        self.send("/caveman lite")
        self.assertEqual(self.flag_value(), "lite")

    def test_foreign_command_envelope_untouched(self):
        # A non-caveman command envelope must not be rewritten — and must
        # not disturb the flag.
        self.flag.write_text("full")
        self.send(self.envelope("/commit", "fix the caveman parser", newlines=True))
        self.assertEqual(self.flag_value(), "full")

    # ── #634 (adapted): repo-local config resolves against per-event cwd ─

    def _make_repo(self, default_mode):
        repo = Path(self._tmp.name) / "project"
        repo.mkdir()
        (repo / ".caveman.json").write_text(
            json.dumps({"defaultMode": default_mode})
        )
        return repo

    def test_nl_trigger_uses_stdin_cwd_for_repo_config(self):
        # The hook's spawn cwd (REPO_ROOT) has no .caveman.json; only the cwd
        # sent on stdin does. Pre-fix the walk started at the spawn cwd and
        # this activated at 'full' instead of the repo's 'lite'.
        repo = self._make_repo("lite")
        self.send("activate caveman", cwd=repo)
        self.assertEqual(self.flag_value(), "lite")

    def test_nl_trigger_respects_off_in_stdin_cwd_repo(self):
        # Repo-local defaultMode "off" must suppress NL auto-activation for a
        # session sitting in that repo, regardless of the hook's spawn cwd.
        repo = self._make_repo("off")
        self.send("activate caveman", cwd=repo)
        self.assertIsNone(self.flag_value())

    def test_bare_slash_caveman_uses_stdin_cwd_for_repo_config(self):
        # The call site the original PR missed: bare /caveman must resolve the
        # configured default against the per-event cwd too.
        repo = self._make_repo("ultra")
        self.send("/caveman", cwd=repo)
        self.assertEqual(self.flag_value(), "ultra")

    # ── #658 (adapted): per-turn anchor carries the language clause ─────

    def test_reinforcement_includes_language_clause(self):
        # The per-turn anchor is the one injection point with no language
        # rule; repeated English-only, it drags non-English sessions toward
        # English replies. It must carry the reply-in-user's-language clause.
        self.flag.write_text("full")
        r = self.send("ordinary follow-up question")
        self.assertIn("Reply in user's language", r.stdout)


if __name__ == "__main__":
    unittest.main()
