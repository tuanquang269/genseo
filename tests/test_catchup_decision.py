"""Boot catch-up decisions. No Shopify, no launchd, no network.

The cases are the 2026-10-19 power-off: slots that passed while the Mac was
off are not replayed. Sleep coalescing is a different path and is not this
program.

    python3 -m unittest tests/test_catchup_decision.py
"""
import contextlib
import io
import json
import os
import plistlib
import shutil
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import genseo_boot_catchup as catchup  # noqa: E402


def minutes(text):
    return catchup.parse_hhmm(text)


class DecideTests(unittest.TestCase):
    def decide(self, hhmm, slots, done=False, locked=False, fired=False, readable=True):
        return catchup.decide_lane(
            minutes(hhmm), slots, done, locked, fired, readable=readable
        )

    def test_already_done_today(self):
        self.assertEqual(
            self.decide("08:09", catchup.ARTICLE_SLOTS, done=True),
            ("skip", "already-done"),
        )
        self.assertEqual(
            self.decide("10:00", catchup.LANDING_SLOTS, done=True),
            ("skip", "already-done"),
        )

    def test_in_progress_lock(self):
        self.assertEqual(
            self.decide("08:09", catchup.ARTICLE_SLOTS, locked=True),
            ("skip", "in-progress"),
        )
        self.assertEqual(
            self.decide("10:00", catchup.LANDING_SLOTS, locked=True),
            ("skip", "in-progress"),
        )

    def test_before_first_slot(self):
        self.assertEqual(
            self.decide("06:30", catchup.ARTICLE_SLOTS),
            ("skip", "before-first-slot"),
        )
        self.assertEqual(
            self.decide("08:09", catchup.LANDING_SLOTS),
            ("skip", "before-first-slot"),
        )

    def test_after_last_slot(self):
        self.assertEqual(
            self.decide("15:00", catchup.ARTICLE_SLOTS),
            ("skip", "after-last-slot"),
        )
        self.assertEqual(
            self.decide("23:10", catchup.ARTICLE_SLOTS),
            ("skip", "after-last-slot"),
        )
        self.assertEqual(
            self.decide("17:00", catchup.LANDING_SLOTS),
            ("skip", "after-last-slot"),
        )

    def test_missed_morning_slot_on_the_power_off_boot(self):
        # MacBook cold boot 2026-10-19 08:09 ICT. 07:30 and 08:05 had passed.
        # Landing's first slot, 08:15, had not.
        self.assertEqual(
            self.decide("08:09", catchup.ARTICLE_SLOTS),
            ("start", "missed-morning-slot"),
        )
        self.assertEqual(
            self.decide("08:09", catchup.LANDING_SLOTS),
            ("skip", "before-first-slot"),
        )

    def test_next_slot_soon_stays_with_launchd(self):
        self.assertEqual(
            self.decide("08:00", catchup.ARTICLE_SLOTS),
            ("skip", "next-slot-soon"),
        )
        self.assertEqual(
            self.decide("07:30", catchup.ARTICLE_SLOTS),
            ("skip", "next-slot-soon"),
        )
        self.assertEqual(
            self.decide("14:32", catchup.ARTICLE_SLOTS),
            ("skip", "next-slot-soon"),
        )
        self.assertEqual(
            self.decide("14:31", catchup.ARTICLE_SLOTS),
            ("start", "missed-morning-slot"),
        )
        self.assertEqual(
            self.decide("09:10", catchup.LANDING_SLOTS),
            ("skip", "next-slot-soon"),
        )

    def test_already_fired_and_unreadable_do_not_start(self):
        self.assertEqual(
            self.decide("10:00", catchup.ARTICLE_SLOTS, fired=True),
            ("skip", "already-fired"),
        )
        self.assertEqual(
            self.decide("10:00", catchup.ARTICLE_SLOTS, readable=False, done=True),
            ("skip", "unreadable"),
        )

    def test_done_is_reported_before_the_lock(self):
        self.assertEqual(
            self.decide("10:00", catchup.ARTICLE_SLOTS, done=True, locked=True),
            ("skip", "already-done"),
        )


class LockTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="catchup-lock.")
        self.addCleanup(shutil.rmtree, self.tmp)
        self.now = 1700000000

    def test_article_lock_matches_the_wrapper_rules(self):
        path = os.path.join(self.tmp, "daily.lock")
        self.assertFalse(catchup.article_lock_held(path, self.now, alive=lambda pid: True))
        os.mkdir(path)
        os.utime(path, (self.now, self.now))
        self.assertTrue(catchup.article_lock_held(path, self.now, alive=lambda pid: False))
        os.utime(path, (self.now - 21601, self.now - 21601))
        self.assertFalse(catchup.article_lock_held(path, self.now, alive=lambda pid: False))
        with open(os.path.join(path, "pid"), "w") as handle:
            handle.write("4242\n")
        os.utime(path, (self.now, self.now))
        self.assertFalse(catchup.article_lock_held(path, self.now, alive=lambda pid: False))
        self.assertTrue(catchup.article_lock_held(path, self.now - 99999, alive=lambda pid: True))

    def test_a_non_directory_lock_is_held(self):
        path = os.path.join(self.tmp, "daily.lock")
        with open(path, "w") as handle:
            handle.write("x")
        self.assertTrue(catchup.article_lock_held(path, self.now, alive=lambda pid: False))

    def test_landing_lock_is_held_until_four_hours(self):
        path = os.path.join(self.tmp, "landing-daily.lock")
        self.assertFalse(catchup.landing_lock_held(path, self.now))
        os.mkdir(path)
        os.utime(path, (self.now - 14400, self.now - 14400))
        self.assertTrue(catchup.landing_lock_held(path, self.now))
        os.utime(path, (self.now - 14401, self.now - 14401))
        self.assertFalse(catchup.landing_lock_held(path, self.now))


def _env(state, now, **overrides):
    env = {
        "HOME": state,
        "PATH": "/usr/bin:/bin",
        "GENSEO_CATCHUP_TEST": "1",
        "GENSEO_CATCHUP_DAY": "2026-10-19",
        "GENSEO_CATCHUP_NOW": now,
        "GENSEO_CATCHUP_STATE_DIR": state,
        "GENSEO_CATCHUP_ARTICLE_DONE": "0",
        "GENSEO_CATCHUP_ARTICLE_LOCKED": "0",
        "GENSEO_CATCHUP_LANDING_DONE": "0",
        "GENSEO_CATCHUP_LANDING_LOCKED": "0",
    }
    env.update(overrides)
    return env


def _run(env):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = catchup.run(env)
    return rc, buf.getvalue()


def _launches(state):
    path = os.path.join(state, "launched.jsonl")
    if not os.path.exists(path):
        return []
    rows = []
    with open(path, "r") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


class RunTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="catchup-run.")
        self.addCleanup(shutil.rmtree, self.tmp)
        self.real_live = catchup.live_facts
        self.probed = {"n": 0}

        def boom(*_args, **_kwargs):
            self.probed["n"] += 1
            raise AssertionError("live probe")

        catchup.live_facts = boom
        self.addCleanup(self._restore_live)

    def _restore_live(self):
        catchup.live_facts = self.real_live

    def test_power_off_boot_starts_articles_only(self):
        state = os.path.join(self.tmp, "boot")
        rc, out = _run(_env(state, "08:09"))
        self.assertEqual(rc, 0)
        self.assertIn("article start missed-morning-slot", out)
        self.assertIn("landing skip before-first-slot", out)
        self.assertIn("/usr/bin/caffeinate -i -s", out)
        self.assertIn("grokbot-genseo-daily.sh", out)
        self.assertNotIn("run_landing_daily.sh", out)
        self.assertNotIn("--live", out)
        self.assertNotIn("shopify_publisher", out)
        self.assertTrue(os.path.exists(os.path.join(state, "2026-10-19-article.started")))
        self.assertFalse(os.path.exists(os.path.join(state, "2026-10-19-landing.started")))
        rows = _launches(state)
        self.assertEqual([row["lane"] for row in rows], ["article"])
        self.assertEqual(rows[0]["argv"][0], "/usr/bin/caffeinate")
        self.assertEqual(rows[0]["argv"][1:3], ["-i", "-s"])
        self.assertEqual(rows[0]["env"]["GENSEO_TICKET_PREFIX"], "MB")
        self.assertEqual(rows[0]["env"]["GENSEO_HOST_ROLE"], "primary")
        self.assertEqual(rows[0]["env"]["GENSEO_DAILY_TARGET"], "5")
        self.assertNotIn("GENSEO_CATCHUP_TEST", rows[0]["env"])
        self.assertNotIn("GENSEO_LANDING_STANDBY_DELAY_MIN", rows[0]["env"])
        self.assertEqual(self.probed["n"], 0)

    def test_second_login_does_not_start_again(self):
        state = os.path.join(self.tmp, "twice")
        first, out1 = _run(_env(state, "08:09"))
        second, out2 = _run(_env(state, "10:00"))
        self.assertEqual(first, 0)
        self.assertEqual(second, 0)
        self.assertIn("article start missed-morning-slot", out1)
        self.assertIn("article skip already-fired", out2)
        self.assertIn("landing start missed-morning-slot", out2)
        rows = _launches(state)
        self.assertEqual([row["lane"] for row in rows], ["article", "landing"])
        self.assertIn("run_landing_daily.sh", rows[1]["argv"][-1])
        self.assertEqual(rows[1]["env"]["GENSEO_HOST_ROLE"], "standby")
        self.assertNotIn("--live", " ".join(rows[1]["argv"]))

    def test_skip_cases_do_not_launch_or_stamp(self):
        cases = (
            ("06:30", {}, "before-first-slot"),
            ("17:00", {}, "after-last-slot"),
            ("10:00", {"GENSEO_CATCHUP_ARTICLE_DONE": "1", "GENSEO_CATCHUP_LANDING_DONE": "1"}, "already-done"),
            ("10:00", {"GENSEO_CATCHUP_ARTICLE_LOCKED": "1", "GENSEO_CATCHUP_LANDING_LOCKED": "1"}, "in-progress"),
        )
        for now, overrides, reason in cases:
            state = os.path.join(self.tmp, reason + now.replace(":", ""))
            rc, out = _run(_env(state, now, **overrides))
            self.assertEqual(rc, 0, out)
            self.assertIn(reason, out)
            self.assertNotIn(" start ", out)
            self.assertEqual(_launches(state), [])
            self.assertFalse(os.path.exists(os.path.join(state, "2026-10-19-article.started")))
            self.assertFalse(os.path.exists(os.path.join(state, "2026-10-19-landing.started")))

    def test_poisoned_home_plist_is_not_read_in_test_mode(self):
        home = os.path.join(self.tmp, "home")
        agents = os.path.join(home, "Library", "LaunchAgents")
        os.makedirs(agents)
        bad = {
            "Label": "com.pati.genseo-daily",
            "ProgramArguments": ["/bin/echo", "--live"],
            "RunAtLoad": False,
            "EnvironmentVariables": {"GENSEO_TICKET_PREFIX": "MM"},
        }
        with open(os.path.join(agents, "com.pati.genseo-daily.plist"), "wb") as handle:
            plistlib.dump(bad, handle)
        state = os.path.join(self.tmp, "poison")
        rc, out = _run(_env(state, "08:09", HOME=home))
        self.assertEqual(rc, 0)
        self.assertIn("grokbot-genseo-daily.sh", out)
        self.assertNotIn("--live", out)
        self.assertEqual(_launches(state)[0]["env"]["GENSEO_TICKET_PREFIX"], "MB")

    def test_refused_command_is_not_started(self):
        path = os.path.join(self.tmp, "bad.plist")
        with open(path, "wb") as handle:
            plistlib.dump(
                {
                    "Label": "com.pati.genseo-daily",
                    "ProgramArguments": ["/bin/echo", "--live"],
                    "EnvironmentVariables": {},
                },
                handle,
            )
        state = os.path.join(self.tmp, "refused")
        rc, out = _run(_env(state, "08:09", GENSEO_CATCHUP_ARTICLE_PLIST=path))
        self.assertEqual(rc, 0)
        self.assertIn("article skip command-refused", out)
        self.assertNotIn("--live", out)
        self.assertFalse(os.path.exists(os.path.join(state, "2026-10-19-article.started")))

    def test_install_text_is_in_the_runbook(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.assertEqual(catchup.main(["--print-install"]), 0)
            self.assertEqual(catchup.main(["--print-uninstall"]), 0)
        text = buf.getvalue()
        self.assertIn(catchup.INSTALL_COMMAND, text)
        self.assertIn(catchup.UNINSTALL_COMMAND, text)
        with open(os.path.join(ROOT, "DAILY-RUN.md"), "r") as handle:
            runbook = handle.read()
        self.assertIn(catchup.INSTALL_COMMAND, runbook)
        self.assertIn(catchup.UNINSTALL_COMMAND, runbook)
        self.assertNotIn("shopify_publisher", catchup.INSTALL_COMMAND)


class PlistTests(unittest.TestCase):
    def test_only_the_catchup_agent_runs_at_load(self):
        deploy = os.path.join(ROOT, "deploy")
        seen = False
        for name in os.listdir(deploy):
            if not name.endswith(".plist"):
                continue
            with open(os.path.join(deploy, name), "rb") as handle:
                data = plistlib.load(handle)
            if name == "com.pati.genseo-catchup.plist":
                seen = True
                self.assertIs(data.get("RunAtLoad"), True)
                self.assertNotIn("StartCalendarInterval", data)
                self.assertIsNone(data.get("KeepAlive"))
                self.assertEqual(data.get("Label"), "com.pati.genseo-catchup")
                argv = data.get("ProgramArguments")
                self.assertEqual(argv[:3], ["/usr/bin/caffeinate", "-i", "-s"])
                self.assertTrue(argv[-1].endswith("scripts/genseo_boot_catchup.py"))
                blob = " ".join(argv)
                self.assertNotIn("--live", blob)
                self.assertNotIn("launchctl", blob)
            else:
                self.assertIs(data.get("RunAtLoad"), False, name)
        self.assertTrue(seen)
