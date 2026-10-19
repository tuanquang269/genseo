"""gen_png retries a dropped ima2 stream, and does not retry a real refusal.

Ticket #CA1009-3 on 2026-10-12 exited on one "Responses stream returned an
error". The daily wrapper counts that as a no-publish. These tests stub the
ima2 binary: no network, no OAuth, no Shopify.

    python3 -m unittest tests/test_ima2_retry.py
"""
import os
import stat
import subprocess
import sys
import tempfile
import time
import unittest
from contextlib import redirect_stdout
from io import StringIO

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _install_stub_bins():
    """article_images.py resolves ima2 and cwebp at import and exits if either
    is missing. Point PATH at no-op stubs before that import. gen_png tests
    never execute them: they replace subprocess.run."""
    stub = tempfile.mkdtemp(prefix="genseo-ima2-stub-")
    for name in ("ima2", "cwebp"):
        path = os.path.join(stub, name)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("#!/bin/sh\nexit 0\n")
        os.chmod(path, stat.S_IRWXU)
    os.environ["PATH"] = stub + os.pathsep + os.environ.get("PATH", "")
    return stub


_install_stub_bins()
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import article_images as ai  # noqa: E402


STREAM = "Responses stream returned an error"
MIN_BYTES = ai.IMA2_MIN_PNG_BYTES


class ScriptedRun(object):
    """Stand-in for _run_ima2. Each outcome is an exception, or a tuple
    (returncode, stderr, stdout, nbytes). nbytes > 0 writes that many bytes
    to the -o path. on_call(n, timeout_s) runs after the call is recorded
    and before the outcome, so a test clock can jump mid-attempt."""

    def __init__(self, outcomes, on_call=None):
        self.outcomes = list(outcomes)
        self.calls = []
        self.on_call = on_call

    def __call__(self, cmd, env, timeout_s):
        self.calls.append((cmd, {"env": env, "timeout": timeout_s}))
        if self.on_call:
            self.on_call(len(self.calls), timeout_s)
        if not self.outcomes:
            raise AssertionError("ima2 ran more times than the test scripted")
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, BaseException):
            raise outcome
        rc, err, out, nbytes = outcome
        if nbytes:
            out_path = cmd[cmd.index("-o") + 1]
            with open(out_path, "wb") as fh:
                fh.write(b"\x89PNG" + b"x" * (nbytes - 4))
        return subprocess.CompletedProcess(cmd, rc, stdout=out, stderr=err)


class Ima2ErrorClassTests(unittest.TestCase):
    def test_incident_stream_error_is_transient(self):
        samples = (
            STREAM,
            "ima2: Responses stream returned an error",
            "HTTP 502 bad gateway",
            "status 503",
            "error: 504",
            "code: 429",
            "connect ECONNRESET 127.0.0.1:443",
            "read ETIMEDOUT",
            "socket hang up",
            "The request timed out",
            "gateway timeout",
            "APIConnectionError: connection reset by peer",
            "APITimeoutError: Request timed out.",
            "rate limit reached",
            "fetch failed",
            "upstream error",
            "server disconnected",
            "overloaded",
        )
        for sample in samples:
            self.assertEqual(ai.ima2_error_class(sample), "transient", sample)

    def test_auth_policy_and_bad_request_are_permanent(self):
        samples = (
            "HTTP 401 Unauthorized",
            "error: 403 forbidden",
            "invalid_request_error: bad request",
            "content policy violation",
            "content_policy_violation",
            "invalid api key",
            "oauth session expired",
            "insufficient_quota",
            "billing hard limit",
            "not logged in",
            "HTTP 400 bad request",
            # A stream wrapper around an auth failure is still auth.
            "Responses stream returned an error: HTTP 401 Unauthorized",
            "rate limit reached; quota exceeded",
        )
        for sample in samples:
            self.assertEqual(ai.ima2_error_class(sample), "permanent", sample)

    def test_flag_oauth_word_and_dose_are_unknown(self):
        samples = (
            "",
            "provider oauth model gpt-6-sol",
            "--timeout 360",
            "500 mg creatine monohydrate",
            "the decoder rejected the pixels",
            "oauth",
        )
        for sample in samples:
            self.assertEqual(ai.ima2_error_class(sample), "unknown", sample)


class GenPngRetryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="genseo-ima2-out-")
        self.out = os.path.join(self.tmp, "hero.png")
        self.ref = os.path.join(self.tmp, "pack.png")
        with open(self.ref, "wb") as fh:
            fh.write(b"ref")
        self.saved_run = ai._run_ima2
        self.saved_serve = ai._ensure_serve
        self.saved_ima2 = ai.IMA2
        self.serve_calls = []
        ai.IMA2 = os.path.join(self.tmp, "ima2")
        ai._ensure_serve = lambda env: self.serve_calls.append(env)
        self.env = {
            "GENSEO_IMA2_PROVIDER": os.environ.get("GENSEO_IMA2_PROVIDER"),
            "GENSEO_IMA2_MODEL": os.environ.get("GENSEO_IMA2_MODEL"),
        }
        os.environ["GENSEO_IMA2_PROVIDER"] = "oauth"
        os.environ["GENSEO_IMA2_MODEL"] = "gpt-6-sol"
        self.sleeps = []

    def tearDown(self):
        ai._run_ima2 = self.saved_run
        ai._ensure_serve = self.saved_serve
        ai.IMA2 = self.saved_ima2
        for key, value in self.env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def _pause(self, seconds):
        self.sleeps.append(seconds)

    def _go(self, outcomes, refs=None, clock=None, on_call=None, sleeper=None,
            face_hint=None):
        runner = ScriptedRun(outcomes, on_call=on_call)
        ai._run_ima2 = runner
        buf = StringIO()
        caught = None
        with redirect_stdout(buf):
            try:
                ai.gen_png("a kitchen counter", "1536x1024", self.out,
                           [] if refs is None else refs, timeout=360,
                           sleeper=self._pause if sleeper is None else sleeper,
                           clock=clock, face_hint=face_hint)
            except SystemExit as exc:
                caught = exc
        return caught, buf.getvalue(), runner

    def test_stream_error_then_success_backs_off(self):
        caught, log, runner = self._go([
            (1, STREAM, "", 0),
            (1, "HTTP 503 service unavailable", "", 0),
            (0, "", "", MIN_BYTES),
        ])
        self.assertIsNone(caught)
        self.assertEqual(self.sleeps, [5, 15])
        self.assertEqual(len(runner.calls), 3)
        self.assertEqual(len(self.serve_calls), 3)
        self.assertGreaterEqual(os.path.getsize(self.out), MIN_BYTES)
        self.assertIn("attempt 1/3", log)
        self.assertIn(STREAM, log)
        self.assertIn("transient, retrying in 5s", log)
        self.assertIn("attempt 2/3", log)
        self.assertIn("retrying in 15s", log)
        self.assertNotIn("giving up", log)
        cmd = runner.calls[0][0]
        self.assertEqual(cmd[0], ai.IMA2)
        self.assertIn("--provider", cmd)
        self.assertEqual(cmd[cmd.index("--provider") + 1], "oauth")
        self.assertEqual(cmd[cmd.index("--model") + 1], "gpt-6-sol")
        self.assertIn("--timeout", cmd)
        self.assertEqual(runner.calls[0][1]["timeout"], 390)

    def test_three_stream_errors_exit_with_the_same_prefix(self):
        caught, log, runner = self._go([
            (1, STREAM, "", 0),
            (1, STREAM, "", 100),
            (1, STREAM, "", 0),
        ])
        self.assertIsNotNone(caught)
        self.assertIn("ima2 generation failed:", str(caught.code))
        self.assertIn(STREAM, str(caught.code))
        self.assertEqual(len(runner.calls), 3)
        self.assertEqual(self.sleeps, [5, 15])
        self.assertIn("attempt 3/3", log)
        self.assertIn("transient, giving up", log)
        self.assertFalse(os.path.isfile(self.out))

    def test_content_policy_is_not_retried(self):
        caught, log, runner = self._go([
            (1, "content policy violation", "", 0),
        ])
        self.assertIn("ima2 generation failed:", str(caught.code))
        self.assertIn("content policy", str(caught.code))
        self.assertEqual(len(runner.calls), 1)
        self.assertEqual(self.sleeps, [])
        self.assertIn("permanent, not retrying", log)
        self.assertNotIn("retrying in", log)
        self.assertNotIn("human no-face", str(caught.code))

    def test_face_refusal_names_the_human_fallback(self):
        caught, log, runner = self._go([
            (1, "content policy violation", "", 0),
        ], face_hint=ai.FACE_FALLBACK_HINT)
        self.assertIn("ima2 generation failed:", str(caught.code))
        self.assertIn("content policy", str(caught.code))
        self.assertIn("human no-face", str(caught.code))
        self.assertIn("empty pack-only", str(caught.code))
        self.assertIn("hand", str(caught.code))
        self.assertEqual(len(runner.calls), 1)
        self.assertEqual(self.sleeps, [])
        self.assertIn("permanent, not retrying", log)

    def test_unknown_error_is_not_retried(self):
        caught, log, runner = self._go([
            (1, "the decoder rejected the pixels", "", 0),
        ])
        self.assertIn("the decoder rejected the pixels", str(caught.code))
        self.assertEqual(len(runner.calls), 1)
        self.assertEqual(self.sleeps, [])
        self.assertIn("not retrying", log)
        self.assertNotIn("transient", log)

    def test_process_timeout_is_retried(self):
        timeout_exc = subprocess.TimeoutExpired(["ima2", "gen"], 390)
        caught, log, runner = self._go([
            timeout_exc,
            (0, "", "", MIN_BYTES),
        ])
        self.assertIsNone(caught)
        self.assertEqual(len(runner.calls), 2)
        self.assertEqual(self.sleeps, [5])
        self.assertIn("timed out after 390s", log)
        self.assertIn("transient, retrying in 5s", log)
        self.assertGreaterEqual(os.path.getsize(self.out), MIN_BYTES)

    def test_tiny_success_without_a_reason_is_retried(self):
        caught, log, runner = self._go([
            (0, "", "", 100),
            (0, "", "", MIN_BYTES),
        ])
        self.assertIsNone(caught)
        self.assertEqual(len(runner.calls), 2)
        self.assertEqual(self.sleeps, [5])
        self.assertIn("output 100B < %dB" % MIN_BYTES, log)
        self.assertGreaterEqual(os.path.getsize(self.out), MIN_BYTES)

    def test_tiny_output_with_policy_text_is_not_retried(self):
        caught, log, runner = self._go([
            (0, "content_policy_violation", "", 100),
        ])
        self.assertIn("content_policy_violation", str(caught.code))
        self.assertIn("output 100B", str(caught.code))
        self.assertEqual(len(runner.calls), 1)
        self.assertEqual(self.sleeps, [])
        self.assertIn("permanent, not retrying", log)

    def test_blank_stderr_reads_the_stream_error_on_stdout(self):
        caught, log, runner = self._go([
            (1, "\n  \n", STREAM, 0),
            (0, "", "", MIN_BYTES),
        ])
        self.assertIsNone(caught)
        self.assertEqual(len(runner.calls), 2)
        self.assertIn(STREAM, log)
        self.assertIn("retrying in 5s", log)

    def test_missing_ref_exits_before_ima2(self):
        missing = os.path.join(self.tmp, "no-such-pack.png")
        caught, log, runner = self._go([], refs=[missing])
        self.assertIn("ref image not found", str(caught.code))
        self.assertEqual(runner.calls, [])
        self.assertEqual(self.serve_calls, [])
        self.assertEqual(self.sleeps, [])
        self.assertEqual(log, "")

    def test_first_try_success_does_not_sleep(self):
        caught, log, runner = self._go([
            (0, "", "", MIN_BYTES),
        ])
        self.assertIsNone(caught)
        self.assertEqual(len(runner.calls), 1)
        self.assertEqual(len(self.serve_calls), 1)
        self.assertEqual(self.sleeps, [])
        self.assertEqual(log, "")

    def test_stale_png_is_not_treated_as_success(self):
        with open(self.out, "wb") as fh:
            fh.write(b"x" * MIN_BYTES)
        caught, log, runner = self._go([
            (1, "HTTP 401 Unauthorized", "", 0),
        ])
        self.assertIn("401", str(caught.code))
        self.assertEqual(len(runner.calls), 1)
        self.assertFalse(os.path.isfile(self.out))
        self.assertIn("permanent, not retrying", log)

    def test_auth_after_one_stream_error_stops(self):
        caught, log, runner = self._go([
            (1, STREAM, "", 0),
            (1, "invalid api key", "", 0),
        ])
        self.assertIn("invalid api key", str(caught.code))
        self.assertEqual(len(runner.calls), 2)
        self.assertEqual(self.sleeps, [5])
        self.assertIn("permanent, not retrying", log)

    def test_four_images_stay_under_half_the_ticket_cap(self):
        wrapper = os.path.join(ROOT, "deploy", "grokbot-genseo-daily.sh")
        with open(wrapper, encoding="utf-8") as fh:
            text = fh.read()
        marker = "GENSEO_TICKET_TIMEOUT_SEC:-"
        self.assertIn(marker, text)
        cap = int(text.split(marker, 1)[1].split("}", 1)[0])
        self.assertEqual(cap, ai.TICKET_CAP_SEC)
        self.assertEqual(ai.IMA2_BACKOFF_SEC, (5, 15))
        self.assertLessEqual(sum(ai.IMA2_BACKOFF_SEC), 20)
        self.assertGreaterEqual(
            ai.IMA2_CALL_BUDGET_SEC, 360 + ai.IMA2_TIMEOUT_PAD_SEC)
        # Hero + 3 inline. Each call may burn the whole budget. That total
        # stays under half of the 90-minute ticket so the writer still fits.
        self.assertLessEqual(4 * ai.IMA2_CALL_BUDGET_SEC, cap // 2)

    def test_call_budget_stops_before_another_attempt(self):
        self.t = 0

        def clock():
            return self.t

        def on_call(n, timeout_s):
            if n == 1:
                self.t = ai.IMA2_CALL_BUDGET_SEC

        timeout_exc = subprocess.TimeoutExpired(["ima2", "gen"], 390)
        caught, log, runner = self._go([timeout_exc, (0, "", "", MIN_BYTES)],
                                        clock=clock, on_call=on_call)
        self.assertIn("ima2 generation failed:", str(caught.code))
        self.assertIn("call budget", str(caught.code))
        self.assertEqual(len(runner.calls), 1)
        self.assertEqual(runner.calls[0][1]["timeout"], 390)
        self.assertEqual(self.sleeps, [])
        self.assertIn("call budget, not retrying", log)
        self.assertNotIn("retrying in", log)

    def test_second_attempt_timeout_is_clamped_to_the_budget(self):
        self.t = 0

        def clock():
            return self.t

        def pause(seconds):
            self.sleeps.append(seconds)
            self.t += seconds

        def on_call(n, timeout_s):
            if n == 1:
                self.t = 500

        timeout_exc = subprocess.TimeoutExpired(["ima2", "gen"], 390)
        caught, log, runner = self._go(
            [timeout_exc, (0, "", "", MIN_BYTES)],
            clock=clock, on_call=on_call, sleeper=pause)
        self.assertIsNone(caught)
        self.assertEqual(len(runner.calls), 2)
        self.assertEqual(runner.calls[0][1]["timeout"], 390)
        # 500s already spent, plus the 5s backoff, leaves 95s of the 600s budget.
        self.assertEqual(runner.calls[1][1]["timeout"], 95)
        self.assertEqual(self.sleeps, [5])
        self.assertGreaterEqual(os.path.getsize(self.out), MIN_BYTES)
        self.assertIn("retrying in 5s", log)

    def test_timeout_kills_sigterm_ignoring_sleeper_tree(self):
        pidfile = os.path.join(self.tmp, "grand.pid")
        script = os.path.join(self.tmp, "ima2-hang")
        with open(script, "w", encoding="utf-8") as fh:
            fh.write(
                "#!/usr/bin/perl\n"
                "use POSIX qw(setsid);\n"
                "my $grandf = $ARGV[0];\n"
                "my $pid = fork();\n"
                "die \"fork\\n\" unless defined $pid;\n"
                "if ($pid == 0) {\n"
                "  setsid() or die \"setsid\\n\";\n"
                "  $SIG{TERM} = \"IGNORE\";\n"
                "  $SIG{HUP} = \"IGNORE\";\n"
                "  $SIG{INT} = \"IGNORE\";\n"
                "  open my $f, \">\", $grandf or die $!;\n"
                "  print $f \"$$\\n\";\n"
                "  close $f;\n"
                "  while (1) { sleep 30; }\n"
                "  exit 0;\n"
                "}\n"
                "$SIG{TERM} = \"IGNORE\";\n"
                "$SIG{HUP} = \"IGNORE\";\n"
                "$SIG{INT} = \"IGNORE\";\n"
                "while (1) { sleep 30; }\n"
            )
        os.chmod(script, stat.S_IRWXU)
        sibling = subprocess.Popen(["/bin/sleep", "60"])
        grand = None
        try:
            with self.assertRaises(subprocess.TimeoutExpired):
                ai._run_ima2([script, pidfile], os.environ.copy(), 1)
            self.assertTrue(os.path.isfile(pidfile))
            with open(pidfile, encoding="utf-8") as fh:
                grand = int(fh.read().strip())
            self.assertTrue(self._stopped(grand), "sleeper grandchild still running")
            self.assertIsNone(sibling.poll())
        finally:
            if sibling.poll() is None:
                sibling.kill()
                sibling.wait()
            if grand and ai._pid_alive(grand):
                try:
                    os.kill(grand, 9)
                except OSError:
                    pass

    def _stopped(self, pid):
        deadline = time.time() + 2
        while time.time() < deadline:
            if not ai._pid_alive(pid):
                return True
            state = _proc_state(pid)
            if state in ("Z", None):
                return True
            time.sleep(0.05)
        return False


def _proc_state(pid):
    path = "/proc/%s/stat" % pid
    try:
        raw = open(path, encoding="utf-8", errors="replace").read()
    except OSError:
        return None
    mark = raw.rfind(")")
    if mark < 0 or mark + 2 >= len(raw):
        return None
    return raw[mark + 2]


if __name__ == "__main__":
    unittest.main()
