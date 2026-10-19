"""Landing-ticket product rotation.

Undated specs are not a use. A same-day draft is that day's landing, not a
multi-day ban and not a reason to repeat the first catalog product. ShilaSource
resin and AgeAura NMN + TMG stay at least as frequent as any other product in
every 7-day window the builder fills.
"""
import datetime as dt
import json
import os
import sys
import tempfile
import unittest
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import brand_rules as br
import build_landing_tickets as landing

FUSI = "fusiforce-creatine-gummies"
AGE = "ageaura-pure-nmn-tmg-nad-complex"
FLORA = "florafresh-vaginal-probiotics-gummies"
SHILA = "shilasource-himalayan-shilajit-resin"
GOLD = "pure-shilajit-gold-resin"
GUM = "premium-himalayan-shilajit-gummies"
TURK = "turkesterone-advanced-formula"
SHOCK = "shilajit-shockwave"
ORDER = [FUSI, AGE, FLORA, SHILA, GOLD, GUM, TURK, SHOCK]
ON = dt.date(2026, 10, 17)


def url(handle):
    return "https://wellnessnest.co/products/" + handle


def dated(handle, day):
    return {"created": day, "hero": {"cta": {"href": url(handle)}}}


def undated(handle):
    return {"hero": {"cta": {"href": url(handle)}}}


def fill(uses, n, on=ON, eligible=None):
    picks = []
    for _ in range(n):
        handle, day = landing.next_product(uses, eligible or ORDER, ORDER, on=on)
        picks.append((day, handle))
        uses["open"].append(handle)
    return picks


def window_gaps(events, start=None):
    """Days whose 7-day window leaves a priority behind the busiest other product."""
    gaps = []
    days = sorted({day for day, _handle in events})
    priority = set(landing.PRIORITY_HANDLES)
    for end in days:
        if start is not None and end < start:
            continue
        window_start = end - dt.timedelta(days=landing.FAIRNESS_DAYS - 1)
        counts = {}
        for day, handle in events:
            if window_start <= day <= end:
                counts[handle] = counts.get(handle, 0) + 1
        busiest = max((n for handle, n in counts.items() if handle not in priority), default=0)
        for handle in landing.PRIORITY_HANDLES:
            if counts.get(handle, 0) < busiest:
                gaps.append((end, handle, counts.get(handle, 0), busiest))
    return gaps


class UndatedSpecTests(unittest.TestCase):
    def test_undated_spec_is_not_a_landing(self):
        spec = undated(SHILA)
        self.assertIsNone(landing.created_day(spec))
        self.assertEqual(landing.spec_landings(spec), [])
        uses = landing.collect_uses("", [spec, dated(SHILA, "2026-10-08"), undated(FUSI)])
        self.assertEqual(uses["real"], [(dt.date(2026, 10, 8), SHILA)])

    def test_history_ignores_mtime_of_an_undated_spec(self):
        with tempfile.TemporaryDirectory() as tmp:
            drafts = os.path.join(tmp, "drafts")
            os.makedirs(drafts)
            queue = os.path.join(tmp, "queue.md")
            with open(queue, "w", encoding="utf-8") as fh:
                fh.write("")
            undated_path = os.path.join(drafts, "shilasource-resin-advertorial.json")
            with open(undated_path, "w", encoding="utf-8") as fh:
                json.dump(undated(SHILA), fh)
            os.utime(undated_path, None)
            with open(os.path.join(drafts, "dated.json"), "w", encoding="utf-8") as fh:
                json.dump(dated(SHILA, "2026-10-08"), fh)
            uses = landing.history(queue_path=queue, drafts_dir=drafts)
        self.assertEqual([day for day, handle in uses["real"] if handle == SHILA], [dt.date(2026, 10, 8)])

    def test_known_undated_repo_specs_do_not_count(self):
        for name in ("shilasource-resin-advertorial.json", "fusiforce-creatine-gummies-listicle.json"):
            with open(os.path.join(ROOT, "landing_drafts", name), encoding="utf-8") as fh:
                spec = json.load(fh)
            self.assertIsNone(landing.created_day(spec), name)
            self.assertEqual(landing.spec_landings(spec), [], name)

    def test_rotation_source_does_not_read_mtime(self):
        with open(os.path.join(ROOT, "scripts", "build_landing_tickets.py"), encoding="utf-8") as fh:
            source = fh.read()
        self.assertNotIn("getmtime", source)
        self.assertNotIn("GENSEO_LANDING_NO_REPEAT_DAYS", source)


class SameDayDraftTests(unittest.TestCase):
    def test_same_day_ageaura_draft_does_not_hand_the_next_day_to_fusiforce(self):
        specs = [
            dated(AGE, "2026-10-17"),
            dated(SHILA, "2026-10-08"),
            undated(SHILA),
            undated(FUSI),
            dated(FUSI, "2026-10-15"),
        ]
        uses = landing.collect_uses("", specs)
        handle, day = landing.next_product(uses, ORDER, ORDER, on=ON)
        self.assertEqual(day, dt.date(2026, 10, 18))
        self.assertEqual(handle, SHILA)
        self.assertNotEqual(handle, FUSI)
        self.assertNotEqual(handle, AGE)

    def test_reported_refill_does_not_stack_fusiforce(self):
        """The 2026-10-17 refill shape: today's AgeAura draft, undated specs, then 8 picks.

        The old picker dated undated specs from mtime, treated AgeAura as used today,
        and once every age tied it repeated FusiForce because that handle is first
        in the angle catalog.
        """
        specs = [
            dated(AGE, "2026-10-08"), dated(AGE, "2026-10-17"),
            dated(FUSI, "2026-10-08"), dated(FUSI, "2026-10-15"), undated(FUSI),
            dated(SHILA, "2026-10-08"), undated(SHILA),
            dated(GUM, "2026-10-08"), dated(FLORA, "2026-10-09"),
            dated(GOLD, "2026-10-12"), dated(TURK, "2026-10-16"),
        ]
        queue = "\n".join([
            "- [ ] listicle | wellnessnest | product=%s · angle: a (added 2026-10-16)" % GUM,
            "- [ ] listicle | wellnessnest | product=%s · angle: b (added 2026-10-16)" % FLORA,
        ])
        uses = landing.collect_uses(queue, specs)
        fusi_days = [day for day, handle in uses["real"] if handle == FUSI]
        shila_days = [day for day, handle in uses["real"] if handle == SHILA]
        self.assertEqual(max(fusi_days), dt.date(2026, 10, 15))
        self.assertEqual(max(shila_days), dt.date(2026, 10, 8))
        self.assertNotIn(ON, fusi_days)
        self.assertNotIn(ON, shila_days)
        picks = [handle for _day, handle in fill(uses, 8)]
        self.assertEqual(picks[0], SHILA)
        self.assertIn(AGE, picks)
        self.assertEqual(picks.count(FUSI), 1)
        self.assertGreaterEqual(picks.count(SHILA), picks.count(FUSI))
        self.assertGreaterEqual(picks.count(AGE), picks.count(FUSI))
        self.assertTrue(all(a != b for a, b in zip(picks, picks[1:])))
        events, _next = landing.schedule(uses, ON)
        self.assertEqual(window_gaps(events, start=dt.date(2026, 10, 20)), [])

    def test_pick_uses_the_same_rule_without_calling_the_store(self):
        with open(os.path.join(ROOT, "templates", "landing", "listicle-angles.json"), encoding="utf-8") as fh:
            angles = json.load(fh)
        products = {
            handle: {"product_type": "Supplement", "variants": [{"available": True}]}
            for handle in ORDER
        }
        uses = landing.collect_uses("", [
            dated(AGE, "2026-10-17"),
            undated(SHILA),
            undated(FUSI),
            dated(SHILA, "2026-10-08"),
        ])
        handle, _meta, _angle, slot, _age, _why = landing.pick(products, angles, uses, on=ON)
        self.assertEqual((handle, slot), (SHILA, dt.date(2026, 10, 18)))


class RepeatedFusiForceTests(unittest.TestCase):
    def test_tied_today_does_not_repeat_the_first_catalog_product(self):
        uses = landing.collect_uses("", [dated(handle, "2026-10-17") for handle in ORDER])
        picks = [handle for _day, handle in fill(uses, 8)]
        self.assertEqual(picks[0], SHILA)
        self.assertEqual(picks[1], AGE)
        self.assertEqual(picks.count(FUSI), 1)
        self.assertTrue(all(a != b for a, b in zip(picks, picks[1:])))
        second_shila = picks.index(SHILA, picks.index(SHILA) + 1)
        self.assertLess(picks.index(FUSI), second_shila)


class PriorityWeightTests(unittest.TestCase):
    def test_priorities_match_the_busiest_other_across_three_weeks(self):
        uses = {"real": [], "open": []}
        picks = fill(uses, 21)
        handles = [handle for _day, handle in picks]
        self.assertEqual(handles[:4], [SHILA, AGE, FUSI, FLORA])
        self.assertTrue(all(a != b for a, b in zip(handles, handles[1:])))
        events, _next = landing.schedule(uses, ON)
        self.assertEqual(window_gaps(events), [])
        counts = {}
        for handle in handles:
            counts[handle] = counts.get(handle, 0) + 1
        busiest = max(n for handle, n in counts.items() if handle not in landing.PRIORITY_HANDLES)
        for handle in landing.PRIORITY_HANDLES:
            self.assertGreaterEqual(counts[handle], busiest, handle)

    def test_a_busier_other_product_pulls_a_priority_forward(self):
        specs = [dated(FUSI, "2026-10-15"), dated(FUSI, "2026-10-16")]
        uses = landing.collect_uses("", specs)
        first, day = landing.next_product(uses, ORDER, ORDER, on=ON)
        self.assertEqual(day, ON)
        self.assertIn(first, landing.PRIORITY_HANDLES)
        self.assertNotEqual(first, FUSI)


class BackToBackTests(unittest.TestCase):
    def test_previous_day_is_skipped_while_another_product_exists(self):
        events = [(dt.date(2026, 10, 17), FUSI)]
        chosen = landing.choose_product(ORDER, events, dt.date(2026, 10, 18), ORDER)
        self.assertNotEqual(chosen, FUSI)

    def test_back_to_back_when_the_catalog_has_one_product(self):
        events = [(dt.date(2026, 10, 17), FUSI)]
        chosen = landing.choose_product([FUSI], events, dt.date(2026, 10, 18), [FUSI])
        self.assertEqual(chosen, FUSI)


class QueueDateTests(unittest.TestCase):
    def test_draft_date_counts_and_added_date_does_not_replace_it(self):
        text = (
            "- [DRAFT 2026-10-17 page 1] listicle | ageaura | product=%s · angle: a (added 2026-10-16)"
            % AGE
        )
        real, open_handles = landing.parse_queue(text)
        self.assertEqual(real, [(ON, AGE)])
        self.assertEqual(open_handles, [])

    def test_failed_line_is_not_a_landing(self):
        text = (
            "- [FAILED 2026-10-15 no spec] listicle | wellnessnest | product=%s · angle: a (added 2026-10-15)"
            % SHOCK
        )
        real, open_handles = landing.parse_queue(text)
        self.assertEqual(real, [])
        self.assertEqual(open_handles, [])

    def test_draft_qa_fail_and_published_count(self):
        text = "\n".join([
            "- [DRAFT-QA-FAIL 2026-10-12 page 9] listicle | wellnessnest | product=%s · angle: a (added 2026-10-09)" % GOLD,
            "- [PUBLISHED 2026-10-11 page 3] listicle | wellnessnest | product=%s · angle: b (added 2026-10-11)" % SHILA,
        ])
        real, _open = landing.parse_queue(text)
        self.assertEqual(real, [
            (dt.date(2026, 10, 12), GOLD),
            (dt.date(2026, 10, 11), SHILA),
        ])

    def test_open_tickets_are_upcoming_days_not_one_added_stamp(self):
        text = "\n".join([
            "- [ ] listicle | wellnessnest | product=%s · angle: a (added 2026-10-17)" % FUSI,
            "- [ ] listicle | wellnessnest | product=%s · angle: b (added 2026-10-17)" % FUSI,
        ])
        uses = landing.collect_uses(text, [])
        self.assertEqual(uses["real"], [])
        events, day = landing.schedule(uses, ON)
        self.assertEqual(events, [(ON, FUSI), (dt.date(2026, 10, 18), FUSI)])
        self.assertEqual(day, dt.date(2026, 10, 19))
        handle, _slot = landing.next_product(uses, ORDER, ORDER, on=ON)
        self.assertNotEqual(handle, FUSI)


class PaletteTests(unittest.TestCase):
    def test_priority_ticket_lines_keep_the_pack_palette(self):
        shila = br.prepare_ticket(landing.ticket_line(
            SHILA, "wellnessnest",
            "Shilajit resin, honestly: N questions first-time buyers ask",
            "adults new to shilajit", "2026-10-17"))
        age = br.prepare_ticket(landing.ticket_line(
            AGE, "ageaura",
            "N questions to ask before you buy an NMN supplement (form, what is on the panel, what human trials tested)",
            "adults 40+ curious about NAD+", "2026-10-17"))
        for line, handle in ((shila, SHILA), (age, AGE)):
            self.assertIn("product=" + handle, line)
            self.assertIn(handle + ".palette.json", line)
            self.assertIn("Do not force a chromatic hue.", line)
            self.assertEqual(br.violations(line), [])
            self.assertNotIn("urolithin", line.lower())


class EnsureOpenTests(unittest.TestCase):
    def _angles(self):
        with open(os.path.join(ROOT, "templates", "landing", "listicle-angles.json"), encoding="utf-8") as fh:
            return json.load(fh)

    def _products(self, handles=None):
        return {
            handle: {"product_type": "Supplement", "variants": [{"available": True}]}
            for handle in (handles or ORDER)
        }

    def test_two_open_lines_from_an_empty_queue_are_the_priorities(self):
        text, added = landing.ensure_open("", self._products(), self._angles(), 2, specs=[], on=ON)
        handles = []
        for line in added:
            found = landing._PRODUCT.search(line)
            self.assertIsNotNone(found, line)
            handles.append(found.group(1))
        self.assertEqual(handles, [SHILA, AGE])
        again, more = landing.ensure_open(text, self._products(), self._angles(), 2, specs=[], on=ON)
        self.assertEqual(more, [])
        self.assertEqual(again, text)

    def test_one_product_stops_when_its_angles_are_already_open(self):
        angles = {SHILA: self._angles()[SHILA]}
        products = self._products([SHILA])
        text, added = landing.ensure_open("", products, angles, 5, specs=[], on=ON)
        self.assertEqual(len(added), 3)
        self.assertEqual(len({landing._angle_of(line) for line in added}), 3)
        _text, more = landing.ensure_open(text, products, angles, 5, specs=[], on=ON)
        self.assertEqual(more, [])

    def test_ensure_open_does_not_fetch_the_store(self):
        def boom():
            raise AssertionError("live_products")

        with mock.patch.object(landing, "live_products", boom):
            text, added = landing.ensure_open("", {}, {}, 2, specs=[], on=ON)
        self.assertEqual(added, [])
        self.assertEqual(text, "")

    def test_main_ensure_when_stocked_does_not_fetch_or_write(self):
        def boom():
            raise AssertionError("live_products")

        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "daily-landing-tickets.md")
            body = (
                "- [ ] listicle | wellnessnest | product=%s · angle: a (added 2026-10-17)\n"
                "- [ ] listicle | wellnessnest | product=%s · angle: b (added 2026-10-17)\n"
            ) % (SHILA, AGE)
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(body)
            with mock.patch.object(landing, "live_products", boom), \
                    mock.patch.object(landing, "QUEUE", path):
                old = sys.argv
                try:
                    sys.argv = ["build_landing_tickets.py", "--ensure", "2"]
                    self.assertEqual(landing.main(), 0)
                finally:
                    sys.argv = old
            with open(path, encoding="utf-8") as fh:
                self.assertEqual(fh.read(), body)

    def test_ensure_rejects_a_non_integer(self):
        old = sys.argv
        try:
            sys.argv = ["build_landing_tickets.py", "--ensure", "nope"]
            with self.assertRaises(SystemExit) as caught:
                landing.main()
        finally:
            sys.argv = old
        self.assertIn("--ensure", str(caught.exception))


class OpenQueueTests(unittest.TestCase):
    def test_rebalanced_open_tickets_include_both_priorities(self):
        path = os.path.join(ROOT, "daily-landing-tickets.md")
        with open(path, encoding="utf-8") as fh:
            lines = fh.read().splitlines()
        open_lines = [line for line in lines if line.startswith("- [ ] ")]
        draft_lines = [line for line in lines if line.startswith("- [DRAFT")]
        failed_lines = [line for line in lines if line.startswith("- [FAILED")]
        self.assertGreaterEqual(len(open_lines), 7)
        self.assertEqual(len(draft_lines), 9)
        self.assertEqual(len(failed_lines), 4)
        self.assertTrue(any("page 166279512379" in line and AGE in line for line in draft_lines))
        self.assertTrue(any(
            "page 166299173179" in line and GUM in line and "choose shilajit gummies over resin" in line
            for line in draft_lines
        ))
        self.assertTrue(any(
            "page 166314115387" in line and FLORA in line and "easier to stick with" in line
            for line in draft_lines
        ))
        handles = []
        for line in open_lines:
            found = landing._PRODUCT.search(line)
            self.assertIsNotNone(found, line)
            handles.append(found.group(1))
            if found.group(1) in landing.PRIORITY_HANDLES:
                self.assertIn(found.group(1) + ".palette.json", line)
                self.assertEqual(br.violations(line), [])
        self.assertEqual(handles, [
            GOLD, SHOCK, FLORA, GUM, TURK, SHILA, AGE, SHILA,
        ])
        self.assertGreaterEqual(handles.count(SHILA), 2)
        self.assertGreaterEqual(handles.count(AGE), 1)
        self.assertEqual(handles.count(FUSI), 0)
        self.assertTrue(all(a != b for a, b in zip(handles, handles[1:])))


if __name__ == "__main__":
    unittest.main()
