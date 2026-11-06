"""Heartbeat gate for the off-Mac article failover.

No Shopify, no publisher, no model router, no image tool, no live feed.
The decision function is pure. CLI tests inject the feed.
"""
import datetime as dt
import json
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import genseo_cloud_failover as gate
import validate_article as va


def ict(hour, minute, day=18):
    return dt.datetime(2026, 10, day, hour, minute, tzinfo=gate.ICT)


def snap(**overrides):
    base = {
        "enabled": True,
        "now": ict(19, 0),
        "cutoff_minutes": 18 * 60 + 30,
        "target": 5,
        "live_count": 0,
        "feed_error": None,
        "peer_active": False,
        "repo_done_today": 0,
        "open_tickets": 2,
        "tickets_error": None,
        "lock": "absent",
        "lint_ok": True,
        "gaps": [],
        "warnings": [],
    }
    base.update(overrides)
    return base


def enabled_env(**extra):
    env = {"GENSEO_CLOUD_FAILOVER": "1"}
    env.update(extra)
    return env


def ready_probe():
    return {
        "gaps": [],
        "warnings": [],
        "nine_router_key_present": True,
        "anthropic_api_key_set": False,
        "shopify_token_file_present": True,
        "roster_nonempty": True,
        "qrg_launcher_present": True,
        "label_guards_loaded": True,
        "geo_citability_loaded": True,
        "publish_arm": False,
        "paid_api_called": False,
    }


class DecisionTests(unittest.TestCase):
    def test_flag_off_ignores_a_gap(self):
        body = gate.evaluate({"enabled": False, "live_count": 0})
        self.assertEqual(body["action"], "disabled")
        self.assertEqual(body["reason"], "flag-off")
        self.assertEqual(body["exit_code"], 0)
        self.assertFalse(body["publish"])
        self.assertFalse(body["paid_api_called"])

    def test_flag_is_exact(self):
        self.assertTrue(gate.flag_enabled("1"))
        for value in ("", "0", "true", "True", "yes", "1 ", " 1", "on"):
            self.assertFalse(gate.flag_enabled(value), value)

    def test_unreadable_feed_fail_closed_even_before_cutoff(self):
        body = gate.evaluate(snap(
            now=ict(8, 44), live_count=-1, feed_error="timed out", peer_active=None,
        ))
        self.assertEqual(body["action"], "fail-closed")
        self.assertEqual(body["reason"], "feed-unreadable")
        self.assertEqual(body["exit_code"], 2)
        self.assertFalse(body["publish"])
        self.assertEqual(body["would_fill"], None)
        self.assertIn("timed out", body["feed_error"])

    def test_feed_error_beats_a_high_count(self):
        body = gate.evaluate(snap(live_count=5, feed_error="boom"))
        self.assertEqual(body["reason"], "feed-unreadable")
        self.assertFalse(body["publish"])

    def test_before_cutoff_stands_down_without_a_peer_result(self):
        body = gate.evaluate(snap(now=ict(8, 44), live_count=0, peer_active=None))
        self.assertEqual(body["action"], "stand-down")
        self.assertEqual(body["reason"], "before-cutoff")
        self.assertEqual(body["exit_code"], 0)
        self.assertEqual(body["would_fill"], 5)
        self.assertFalse(body["publish"])

    def test_feed_at_target_stands_down_even_if_the_repo_has_no_done_line(self):
        body = gate.evaluate(snap(live_count=5, repo_done_today=0, peer_active=None))
        self.assertEqual(body["reason"], "feed-at-target")
        self.assertFalse(body["publish"])
        self.assertEqual(body["would_fill"], 0)

    def test_feed_above_target_stands_down(self):
        body = gate.evaluate(snap(live_count=6))
        self.assertEqual(body["reason"], "feed-at-target")

    def test_repo_record_stands_down_when_the_feed_is_behind(self):
        body = gate.evaluate(snap(live_count=2, repo_done_today=5))
        self.assertEqual(body["reason"], "repo-record-at-target")
        self.assertFalse(body["publish"])
        self.assertEqual(body["would_fill"], 3)

    def test_peer_window_stands_down_under_target(self):
        body = gate.evaluate(snap(live_count=1, peer_active=True, repo_done_today=0))
        self.assertEqual(body["reason"], "peer-window")
        self.assertFalse(body["publish"])

    def test_unknown_peer_fail_closed(self):
        body = gate.evaluate(snap(live_count=1, peer_active=None))
        self.assertEqual(body["reason"], "peer-unknown")
        self.assertEqual(body["exit_code"], 2)

    def test_held_lock_stands_down(self):
        body = gate.evaluate(snap(lock="held"))
        self.assertEqual(body["reason"], "lane-lock")
        self.assertFalse(body["publish"])

    def test_stale_lock_does_not_stand_down(self):
        body = gate.evaluate(snap(lock="stale"))
        self.assertEqual(body["reason"], "publish-blocked")
        self.assertIn("publish-arm-disabled", body["gaps"])

    def test_empty_queue_stands_down_without_publishing(self):
        body = gate.evaluate(snap(open_tickets=0))
        self.assertEqual(body["reason"], "queue-empty")
        self.assertFalse(body["publish"])

    def test_unreadable_tickets_fail_closed_when_the_feed_shows_a_gap(self):
        body = gate.evaluate(snap(tickets_error="FileNotFoundError", repo_done_today=None,
                                  open_tickets=None))
        self.assertEqual(body["reason"], "tickets-unreadable")
        self.assertEqual(body["exit_code"], 2)

    def test_lint_failure_fail_closed(self):
        body = gate.evaluate(snap(lint_ok=False))
        self.assertEqual(body["reason"], "ticket-lint")
        self.assertFalse(body["publish"])

    def test_lint_not_run_fail_closed(self):
        body = gate.evaluate(snap(lint_ok=None))
        self.assertEqual(body["reason"], "lint-not-run")

    def test_ready_dependencies_still_do_not_publish(self):
        body = gate.evaluate(snap(gaps=[]))
        self.assertEqual(body["action"], "fail-closed")
        self.assertEqual(body["reason"], "publish-blocked")
        self.assertEqual(body["exit_code"], 2)
        self.assertFalse(body["publish"])
        self.assertFalse(body["paid_api_called"])
        self.assertIn("publish-arm-disabled", body["gaps"])

    def test_missing_secret_names_are_kept_and_the_arm_stays_off(self):
        body = gate.evaluate(snap(gaps=["NINE_ROUTER_KEY", "shopify-token-file", "ima2"]))
        self.assertEqual(body["reason"], "publish-blocked")
        self.assertIn("NINE_ROUTER_KEY", body["gaps"])
        self.assertIn("shopify-token-file", body["gaps"])
        self.assertIn("ima2", body["gaps"])
        self.assertIn("publish-arm-disabled", body["gaps"])
        self.assertFalse(body["publish"])

    def test_bad_target_and_clock_fail_closed(self):
        self.assertEqual(gate.evaluate(snap(target=0))["reason"], "bad-target")
        self.assertEqual(gate.evaluate(snap(target="5"))["reason"], "bad-target")
        self.assertEqual(gate.evaluate(snap(cutoff_minutes=None))["reason"], "bad-clock")
        self.assertFalse(gate.evaluate(snap(target=0))["publish"])

    def test_qrg_warning_does_not_authorize_a_publish(self):
        body = gate.evaluate(snap(warnings=["claude-seo runtime not installed"]))
        self.assertEqual(body["reason"], "publish-blocked")
        self.assertIn("claude-seo runtime not installed", body["warnings"])
        self.assertFalse(body["publish"])


class RecordAndLockTests(unittest.TestCase):
    def test_repo_record_counts_today_only_and_open_lines(self):
        text = "\n".join([
            "## [DONE 2026-10-17 https://wellnessnest.co/blogs/news/older] Ticket",
            "## [DONE 2026-10-18 https://wellnessnest.co/blogs/news/one] Ticket",
            "- [DONE 2026-10-18 https://wellnessnest.co/blogs/news/two] Ticket",
            "## [DONE 2026-10-18] Ticket",
            "## [SKIPPED-DUPLICATE 2026-10-18 https://wellnessnest.co/blogs/news/skip] Ticket",
            "- [ ] **#MB1018-1 — open one**",
            "## [ ] Ticket #2 — open two",
            "## [x] Ticket #3 — closed",
        ])
        done, open_n = gate.count_repo_record(text, "2026-10-18")
        self.assertEqual(done, 3)
        self.assertEqual(open_n, 2)
        self.assertEqual(gate.count_repo_record(text, "2026-10-17"), (1, 2))

    def test_open_count_matches_the_wrapper_grep(self):
        path = os.path.join(ROOT, "daily-tickets.md")
        with open(path, encoding="utf-8") as handle:
            text = handle.read()
        _done, open_n = gate.count_repo_record(text, "1999-01-01")
        proc = subprocess.run(
            ["grep", "-cE", r"^(- \[ \]|## \[ \])", path],
            capture_output=True, text=True,
        )
        self.assertIn(proc.returncode, (0, 1))
        self.assertEqual(open_n, int((proc.stdout or "0").strip() or "0"))

    def test_lock_rules_match_the_daily_wrapper(self):
        now = 1_700_000_000
        stale = gate.LOCK_STALE_SEC
        with tempfile.TemporaryDirectory() as tmp:
            missing = os.path.join(tmp, "missing")
            self.assertEqual(
                gate.classify_lock(missing, now, stale, lambda _p: False, lambda _p: False),
                "absent",
            )
            young = os.path.join(tmp, "young")
            os.makedirs(young)
            os.utime(young, (now - 10, now - 10))
            self.assertEqual(
                gate.classify_lock(young, now, stale, lambda _p: False, lambda _p: False),
                "held",
            )
            old = os.path.join(tmp, "old")
            os.makedirs(old)
            os.utime(old, (now - stale, now - stale))
            self.assertEqual(
                gate.classify_lock(old, now, stale, lambda _p: False, lambda _p: False),
                "stale",
            )
            dead = os.path.join(tmp, "dead")
            os.makedirs(dead)
            with open(os.path.join(dead, "pid"), "w", encoding="utf-8") as handle:
                handle.write("42")
            os.utime(dead, (now - 5, now - 5))
            self.assertEqual(
                gate.classify_lock(dead, now, stale, lambda _p: False, lambda _p: True),
                "stale",
            )
            live = os.path.join(tmp, "live")
            os.makedirs(live)
            with open(os.path.join(live, "pid"), "w", encoding="utf-8") as handle:
                handle.write("7")
            os.utime(live, (now - stale - 10, now - stale - 10))
            self.assertEqual(
                gate.classify_lock(live, now, stale, lambda _p: True, lambda _p: True),
                "held",
            )
            other = os.path.join(tmp, "other")
            os.makedirs(other)
            with open(os.path.join(other, "pid"), "w", encoding="utf-8") as handle:
                handle.write("9")
            os.utime(other, (now - 5, now - 5))
            self.assertEqual(
                gate.classify_lock(other, now, stale, lambda _p: True, lambda _p: False),
                "held",
            )
            other_old = os.path.join(tmp, "other-old")
            os.makedirs(other_old)
            with open(os.path.join(other_old, "pid"), "w", encoding="utf-8") as handle:
                handle.write("9")
            os.utime(other_old, (now - stale, now - stale))
            self.assertEqual(
                gate.classify_lock(other_old, now, stale, lambda _p: True, lambda _p: False),
                "stale",
            )

    def test_wrapper_command_match_ignores_a_grep(self):
        self.assertTrue(gate.cmd_is_daily_wrapper(
            "/bin/bash /Users/kevinkreative/bin/grokbot-genseo-daily.sh"
        ))
        self.assertTrue(gate.cmd_is_daily_wrapper("grokbot-genseo-daily"))
        self.assertFalse(gate.cmd_is_daily_wrapper("grep grokbot-genseo-daily.sh daily"))
        self.assertFalse(gate.cmd_is_daily_wrapper(
            "vim /Users/kevinkreative/genseo/deploy/grokbot-genseo-daily.sh"
        ))
        self.assertFalse(gate.cmd_is_daily_wrapper(""))


class ProbeTests(unittest.TestCase):
    def test_probe_reports_names_not_values(self):
        secret = "shpat_SUPERSECRETVALUE"
        router = "router-secret-value-should-not-leak"
        anthropic = "sk-ant-secret-value-should-not-leak"
        with tempfile.TemporaryDirectory() as tmp:
            token = os.path.join(tmp, "token.json")
            with open(token, "w", encoding="utf-8") as handle:
                handle.write('{"shop":"example.myshopify.com","access_token":"%s"}' % secret)
            probe = gate.probe_dependencies(
                env={
                    "NINE_ROUTER_KEY": router,
                    "ANTHROPIC_API_KEY": anthropic,
                    "GENSEO_CONFIG": token,
                },
                which=lambda name: name == "cwebp",
                roster_nonempty=False,
                qrg_bin=None,
            )
        dumped = json.dumps(probe)
        self.assertNotIn(secret, dumped)
        self.assertNotIn(router, dumped)
        self.assertNotIn(anthropic, dumped)
        self.assertNotIn("SUPERSECRET", dumped)
        self.assertTrue(probe["nine_router_key_present"])
        self.assertTrue(probe["anthropic_api_key_set"])
        self.assertTrue(probe["shopify_token_file_present"])
        self.assertIn("ANTHROPIC_API_KEY-must-stay-unset", probe["gaps"])
        self.assertIn("ima2", probe["gaps"])
        self.assertIn("claude-cli", probe["gaps"])
        self.assertIn("gem9", probe["gaps"])
        self.assertIn("roster-empty", probe["gaps"])
        self.assertNotIn("cwebp", probe["gaps"])
        self.assertFalse(probe["publish_arm"])
        self.assertFalse(probe["paid_api_called"])
        self.assertTrue(probe["label_guards_loaded"])
        self.assertTrue(probe["geo_citability_loaded"])

    def test_missing_token_file_is_a_named_gap_and_is_not_opened(self):
        missing = os.path.join(tempfile.gettempdir(), "genseo-no-such-token.json")
        probe = gate.probe_dependencies(
            env={},
            token_path=missing,
            which=lambda _name: False,
            roster_nonempty=True,
            qrg_bin="/tmp/claude-seo",
        )
        self.assertIn("shopify-token-file", probe["gaps"])
        self.assertIn("NINE_ROUTER_KEY", probe["gaps"])
        self.assertNotIn("ANTHROPIC_API_KEY-must-stay-unset", probe["gaps"])
        self.assertTrue(probe["qrg_launcher_present"])
        self.assertEqual(probe["warnings"], [])

    def test_qrg_skip_matches_validate_article_when_the_launcher_is_absent(self):
        if va._claude_seo_bin() is not None:
            self.skipTest("claude-seo is installed on this host")
        _scores, note = va.qrg_scores("plain prose")
        probe = gate.probe_dependencies(
            env={"NINE_ROUTER_KEY": "present"},
            token_path=os.path.join(ROOT, "README.md"),
            which=lambda _name: True,
            roster_nonempty=True,
            qrg_bin=None,
        )
        self.assertTrue(any(item == note or note in item for item in probe["warnings"]))
        self.assertIn("claude-seo runtime not installed", note)

    def test_redact_strips_credential_shapes(self):
        cleaned = gate.redact("shop shpat_ABCDEF token sk-ant-api03-zzzz")
        self.assertNotIn("shpat_ABCDEF", cleaned)
        self.assertNotIn("sk-ant-api03-zzzz", cleaned)
        self.assertIn("[redacted]", cleaned)


class CliTests(unittest.TestCase):
    def test_disabled_cli_does_not_fetch_or_echo_secrets(self):
        calls = []
        env = enabled_env()
        env["GENSEO_CLOUD_FAILOVER"] = "0"
        env["NINE_ROUTER_KEY"] = "router-secret-value-should-not-leak"
        body = gate.main(
            argv=[],
            env=env,
            now=ict(19, 0),
            fetch_count_fn=lambda: calls.append("count") or {"live_count": 0, "feed_error": None},
        )
        self.assertEqual(body["reason"], "flag-off")
        self.assertEqual(calls, [])
        self.assertNotIn("router-secret", json.dumps(body))
        self.assertFalse(body["publish"])

    def test_bad_cutoff_does_not_fetch(self):
        calls = []
        body = gate.main(
            argv=[],
            env=enabled_env(GENSEO_CLOUD_CUTOFF_ICT="25:99"),
            now=ict(19, 0),
            fetch_count_fn=lambda: calls.append("count"),
        )
        self.assertEqual(body["reason"], "bad-cutoff")
        self.assertEqual(calls, [])
        self.assertFalse(body["publish"])

    def test_at_target_does_not_ask_the_peer_or_lint(self):
        peers = []
        lints = []
        body = gate.main(
            argv=[],
            env=enabled_env(),
            now=ict(19, 0),
            fetch_count_fn=lambda: {"live_count": 5, "feed_error": None, "peer_active": None},
            fetch_peer_fn=lambda: peers.append("peer"),
            lint_fn=lambda: lints.append("lint") or (True, "lint_tickets: 0"),
            read_tickets_fn=lambda: ("- [ ] open\n", None),
            lock_fn=lambda: "absent",
            probe_fn=ready_probe,
        )
        self.assertEqual(body["reason"], "feed-at-target")
        self.assertEqual(peers, [])
        self.assertEqual(lints, [])
        self.assertFalse(body["publish"])
        self.assertFalse(body["dependencies"]["publish_arm"])

    def test_gap_fail_closes_without_publishing_even_when_deps_look_ready(self):
        lints = []
        body = gate.main(
            argv=[],
            env=enabled_env(),
            now=ict(19, 0),
            fetch_count_fn=lambda: {"live_count": 2, "feed_error": None},
            fetch_peer_fn=lambda: {"peer_active": False, "feed_error": None, "peer_note": "peer-idle"},
            read_tickets_fn=lambda: (
                "## [DONE 2026-10-18 https://wellnessnest.co/blogs/news/one] T\n- [ ] open\n",
                None,
            ),
            lock_fn=lambda: "absent",
            lint_fn=lambda: lints.append(1) or (True, "lint_tickets: 0 open ticket(s) with brand-rule violations"),
            probe_fn=ready_probe,
        )
        self.assertEqual(lints, [1])
        self.assertEqual(body["action"], "fail-closed")
        self.assertEqual(body["reason"], "publish-blocked")
        self.assertEqual(body["exit_code"], 2)
        self.assertEqual(body["live_count"], 2)
        self.assertEqual(body["repo_done_today"], 1)
        self.assertEqual(body["would_fill"], 3)
        self.assertIn("publish-arm-disabled", body["gaps"])
        self.assertFalse(body["publish"])
        self.assertFalse(body["paid_api_called"])
        self.assertFalse(body["dependencies"]["paid_api_called"])

    def test_peer_active_stands_down_and_does_not_lint(self):
        lints = []
        body = gate.main(
            argv=[],
            env=enabled_env(),
            now=ict(19, 0),
            fetch_count_fn=lambda: {"live_count": 1, "feed_error": None},
            fetch_peer_fn=lambda: {
                "peer_active": True,
                "feed_error": None,
                "peer_note": "peer-active: https://wellnessnest.co/blogs/news/example",
            },
            lint_fn=lambda: lints.append(1) or (True, "ok"),
            read_tickets_fn=lambda: ("- [ ] open\n", None),
            lock_fn=lambda: "absent",
            probe_fn=ready_probe,
        )
        self.assertEqual(body["reason"], "peer-window")
        self.assertEqual(lints, [])
        self.assertFalse(body["publish"])
        self.assertNotIn("shpat_", json.dumps(body))

    def test_held_lock_on_this_machine_stands_down(self):
        body = gate.main(
            argv=[],
            env=enabled_env(),
            now=ict(19, 0),
            fetch_count_fn=lambda: {"live_count": 0, "feed_error": None},
            fetch_peer_fn=lambda: {"peer_active": False, "feed_error": None, "peer_note": ""},
            read_tickets_fn=lambda: ("- [ ] open\n", None),
            lock_fn=lambda: "held",
            lint_fn=lambda: (True, "ok"),
            probe_fn=ready_probe,
        )
        self.assertEqual(body["reason"], "lane-lock")
        self.assertFalse(body["publish"])

    def test_repo_done_stands_down_before_lint(self):
        lints = []
        body = gate.main(
            argv=[],
            env=enabled_env(),
            now=ict(19, 0),
            fetch_count_fn=lambda: {"live_count": 0, "feed_error": None},
            fetch_peer_fn=lambda: {"peer_active": False, "feed_error": None, "peer_note": ""},
            read_tickets_fn=lambda: (
                "\n".join(
                    "## [DONE 2026-10-18 https://wellnessnest.co/blogs/news/n%s] T" % n
                    for n in range(5)
                ),
                None,
            ),
            lock_fn=lambda: "stale",
            lint_fn=lambda: lints.append(1) or (False, "should-not-run"),
            probe_fn=ready_probe,
        )
        self.assertEqual(body["reason"], "repo-record-at-target")
        self.assertEqual(lints, [])
        self.assertFalse(body["publish"])

    def test_process_entry_disabled_exits_zero_without_the_secret(self):
        env = os.environ.copy()
        env.pop("GENSEO_CLOUD_FAILOVER", None)
        env["NINE_ROUTER_KEY"] = "router-secret-value-should-not-leak"
        env["ANTHROPIC_API_KEY"] = "sk-ant-secret-value-should-not-leak"
        proc = subprocess.run(
            [sys.executable, os.path.join(ROOT, "scripts", "genseo_cloud_failover.py")],
            capture_output=True, text=True, timeout=20, env=env, cwd=ROOT,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("flag-off", proc.stdout)
        self.assertIn("publish=false", proc.stderr)
        self.assertNotIn("router-secret-value", proc.stdout)
        self.assertNotIn("sk-ant-secret-value", proc.stdout)
        self.assertNotIn("router-secret-value", proc.stderr)


class ScaffoldFileTests(unittest.TestCase):
    def test_script_does_not_import_the_publisher_or_image_lane(self):
        path = os.path.join(ROOT, "scripts", "genseo_cloud_failover.py")
        with open(path, encoding="utf-8") as handle:
            src = handle.read()
        for banned in (
            "import shopify_publisher",
            "import genseo_config",
            "import article_images",
            "import persona_picker",
            "shopify_publisher.py",
            "ima2 gen",
        ):
            self.assertNotIn(banned, src)

    def test_workflow_is_off_unless_the_variable_is_exactly_one(self):
        path = os.path.join(ROOT, ".github", "workflows", "genseo-cloud-failover.yml")
        with open(path, encoding="utf-8") as handle:
            text = handle.read()
        self.assertIn("vars.GENSEO_CLOUD_FAILOVER == '1'", text)
        self.assertIn("workflow_dispatch:", text)
        self.assertIn("cron: '30 11 * * *'", text)
        self.assertIn("cron: '0 15 * * *'", text)
        self.assertIn("contents: read", text)
        self.assertIn("GENSEO_NO_FACE: '1'", text)
        self.assertNotIn("secrets.", text)
        self.assertNotIn("shopify_publisher", text)
        self.assertNotIn("NINE_ROUTER_KEY", text)
        self.assertNotIn("ANTHROPIC_API_KEY", text)


if __name__ == "__main__":
    unittest.main()
