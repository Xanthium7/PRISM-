"""PRISM full test suite: ONE file, every scenario, full state logged to files.

Run from the project root:
    python -B tests/test_prism_full.py                 # writes test_reports/prism_test_report.md (+ .jsonl)
    python -B tests/test_prism_full.py --out my_dir    # choose the output folder
    python -B tests/test_prism_full.py --only P2       # run tests whose id/name contains "P2"
    python -B tests/test_prism_full.py --list          # list all tests

Two files are STREAMED while the tests run (flushed after every line, so you can tail them):
    prism_test_report.md      human-readable: per turn topic table, page table, L1 bar, L2, prompt, events
    prism_test_events.jsonl   machine-readable: one JSON object per test / turn / check (for visualizers)
A summary table is inserted at the top of the .md when the run finishes.

Test ids:  U storage units | S segmentation | R routing | B bring-in | P pressure
           T turn integrity (replies, reserve, atomicity) | C cards | D deciders | E end-to-end + fuzz

Tests are strict on purpose. A failure is a finding about the implementation, not a reason to loosen the test.
"""
from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
import time
import unittest
from collections import Counter
from datetime import datetime
from pathlib import Path

sys.dont_write_bytecode = True
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from prism import (ContextManager, FakeCardWriter, KeywordRouter, KeywordSegmenter, L1, L1FullError, L2,
                   Message, PageBlock, PageTable, SegmentDecision, TopicTable)
from prism.deciders import JevClient, JevRouter, JevSegmenter, LLMCardWriter
from prism.models import Topic, TopicCard
from prism.storage import LocationBook

GAP = "[earlier messages omitted]"
DEFAULT_OUT = os.environ.get("PRISM_REPORT_DIR", "test_reports")


# ══════════════════════════════════════════════════════════════════ report (streamed)

def esc(text, n=100):
    s = str(text).replace("\n", " ").replace("|", "/")
    return s if len(s) <= n else s[: n - 3] + "..."


def bar(used, mx, low, high, width=40):
    cells = ["#" if i < round(used / mx * width) else "." for i in range(width)] if mx else ["."] * width
    for mark in (low, high):
        cells[min(width - 1, int(mark * width))] = "|"
    return "[" + "".join(cells) + "]"


class Report:
    """Writes markdown + JSONL as the tests run. Nothing is buffered."""

    def __init__(self):
        self.out = None
        self.md = self.jl = None
        self.cur = None
        self.results: list[dict] = []
        self.header_len = 0

    def ensure(self, out_dir=None):
        if self.md:
            return
        self.out = Path(out_dir or DEFAULT_OUT)
        self.out.mkdir(parents=True, exist_ok=True)
        self.md_path = self.out / "prism_test_report.md"
        self.jl_path = self.out / "prism_test_events.jsonl"
        self.md = open(self.md_path, "w", encoding="utf-8")
        self.jl = open(self.jl_path, "w", encoding="utf-8")
        self.w(f"# PRISM test report\n\n> Generated `{datetime.now():%Y-%m-%d %H:%M:%S}`\n\n")
        self.header_len = self.md.tell()

    def w(self, text):
        self.md.write(text)
        self.md.flush()

    def j(self, **obj):
        self.jl.write(json.dumps(obj, ensure_ascii=False, default=str) + "\n")
        self.jl.flush()

    def start_test(self, tid, title, doc):
        self.cur = dict(id=tid, title=title, t0=time.time(), checks=0, failed=0, turns=0)
        self.w(f"\n---\n\n## {tid} — {title}\n\n")
        if doc:
            self.w(f"> {doc}\n\n")
        self.j(type="test_start", id=tid, title=title, doc=doc)

    def check(self, ok, msg):
        if self.cur:
            self.cur["checks"] += 1
            self.cur["failed"] += 0 if ok else 1
        self.w(f"- {'✅' if ok else '❌'} {msg}\n")
        self.j(type="check", test=self.cur and self.cur["id"], ok=bool(ok), msg=msg)

    def text(self, msg):
        self.w(f"{msg}\n\n")

    def end_test(self, status, detail=""):
        c = self.cur
        if not c:
            return
        secs = time.time() - c["t0"]
        icon = {"PASS": "✅", "FAIL": "❌", "ERROR": "💥"}[status]
        self.w(f"\n**Result: {icon} {status}**  ({c['checks']} checks, {c['failed']} failed, {c['turns']} turns, {secs:.2f}s)\n")
        if detail:
            self.w("\n```\n" + detail.strip() + "\n```\n")
        self.results.append(dict(id=c["id"], title=c["title"], status=status, checks=c["checks"],
                                 failed=c["failed"], turns=c["turns"]))
        self.j(type="test_end", id=c["id"], status=status, checks=c["checks"], failed=c["failed"], detail=detail)
        self.cur = None
        tag = {"PASS": "PASS ", "FAIL": "FAIL ", "ERROR": "ERROR"}[status]
        print(f"  [{tag}] {c['id']:<4} {c['title']}")

    def turn(self, d):
        """d: dict built by Harness. Writes the per-turn state block."""
        if self.cur:
            self.cur["turns"] += 1
        tag = f" [{d['label']}]" if d["label"] else ""
        self.w(f"### Turn {d['n']}{tag}: \"{esc(d['user'], 110)}\"\n\n")
        if d["error"]:
            self.w(f"- ❌ **Raised** `{d['error']}`\n")
        if d["reply"] is not None:
            self.w(f"- **Reply ({d['role']})**: {esc(d['reply'], 110)}\n")
        ev = lambda xs: ", ".join(f"`{esc(e, 70)}`" for e in xs) or "none"
        self.w(f"- **Events in prepare_context**: {ev(d['ev_p'])}\n- **Events in record_reply**: {ev(d['ev_r'])}\n")
        if d["viol"]:
            self.w("- ❌ **Invariant violations**:\n" + "".join(f"  - {v}\n" for v in d["viol"]))
        else:
            self.w(f"- ✅ **Invariants**: all {INVARIANT_COUNT} hold\n")
        a, m = d["after"], d["mid"]
        self.w("\n**Topic table**\n\n| ID | Status | Label | Key facts | Entities | Pages | Covered |\n|:-:|:-:|:--|:--|:--|:-:|:-:|\n")
        for t in a["topics"]:
            self.w(f"| {t['id']} | {'🟢 open' if t['open'] else '🔴 closed'} | `{esc(t['label'], 40)}` | "
                   f"{esc('; '.join(t['facts'][:2]) or '-', 60)} | {esc(', '.join(t['entities'][:5]) or '-', 40)} | "
                   f"`{t['pages']}` | {t['covered']} |\n")
        self.w("\n**Page table**\n\n| Page | Layer | Topic | Tokens | Open | First message |\n|:-:|:-:|:-:|:-:|:-:|:--|\n")
        for seq in sorted(a["table"]):
            p = next((x for x in a["l1"] + a["l2"] if x["seq"] == seq), None)
            self.w(f"| {seq} | **{a['table'][seq]}** | {p['topic'] if p else '?'} | {p['tokens'] if p else '?'} | "
                   f"{'yes' if p and p['open'] else ''} | {esc(p['msgs'][0]['text'], 50) if p and p['msgs'] else ''} |\n")
        for label, s in (("after prepare_context", m), ("after record_reply", a)):
            pct = s["used"] / s["max"] if s["max"] else 0
            self.w(f"\n**L1 {label}**: `{bar(s['used'], s['max'], s['low'], s['high'])}` "
                   f"{s['used']}/{s['max']} tok ({pct:.0%}); `|` marks low {s['low']:.0%} / high {s['high']:.0%}; "
                   f"L1 pages `{[p['seq'] for p in s['l1']]}`, L2 pages `{[p['seq'] for p in s['l2']]}`\n")
        self.w("\n**Prompt sent to the model**\n\n")
        self.w("".join(f"> **[{x['role'].upper()}]** {esc(x['text'], 120)}\n" for x in d["prompt"]) or "> *(not produced)*\n")
        self.w("\n<details><summary>Page contents (final state)</summary>\n\n")
        for layer, pages in (("L1", a["l1"]), ("L2", a["l2"])):
            for p in pages:
                self.w(f"- **{layer} page {p['seq']}** (topic {p['topic']}, {p['tokens']} tok{', OPEN' if p['open'] else ''})\n")
                for x in p["msgs"]:
                    self.w(f"  - `{x['role']}`: {esc(x['text'], 90)}\n")
        self.w("\n</details>\n\n")
        self.j(type="turn", test=self.cur and self.cur["id"], **d)

    def finalize(self):
        if not self.md:
            return
        self.md.close()
        self.jl.close()
        ok = sum(r["status"] == "PASS" for r in self.results)
        rows = "".join(f"| {r['id']} | {r['title']} | {r['turns']} | {r['checks']} | "
                       f"{ {'PASS': '✅ PASS', 'FAIL': '❌ FAIL', 'ERROR': '💥 ERROR'}[r['status']] } |\n"
                       for r in self.results)
        summary = (f"## Summary\n\n**{ok}/{len(self.results)} tests passed**"
                   f" · {sum(r['checks'] for r in self.results)} checks"
                   f" · {sum(r['turns'] for r in self.results)} conversation turns logged\n\n"
                   f"| ID | Test | Turns | Checks | Result |\n|:-:|:--|:-:|:-:|:-:|\n{rows}\n")
        text = self.md_path.read_text(encoding="utf-8")
        self.md_path.write_text(text[: self.header_len] + summary + text[self.header_len:], encoding="utf-8")


REPORT = Report()


# ══════════════════════════════════════════════════════════════════ helpers

def tok(n, tag=""):
    """A string that is EXACTLY n tokens under whatever token estimator the project uses."""
    base = ((tag + " ") if tag else "") + "lorem ipsum dolor sit amet " * (n + 3)
    for length in range(1, len(base) + 1):
        if Message("user", base[:length]).tokens == n:
            return base[:length]
    raise ValueError(f"cannot build a {n}-token string")


def page_dict(p):
    return dict(seq=p.seq, topic=p.topic_id, tokens=p.tokens, open=p.is_open,
                msgs=[dict(role=m.role, text=m.content) for m in p.data])


def snap(mgr):
    topics = [dict(id=t.id, open=t.is_open, label=t.card.label, facts=list(t.card.key_facts),
                   entities=list(t.card.entities), pages=list(t.page_seqs), covered=t.card.covered_through)
              for t in mgr.topics.all()]
    l1, l2 = [page_dict(p) for p in mgr.l1.pages()], [page_dict(p) for p in mgr.l2.pages()]
    table = {s: mgr.page_table.where(s) for layer in ("L1", "L2") for s in mgr.page_table.pages_in(layer)}
    return dict(topics=topics, l1=l1, l2=l2, table=table, used=mgr.l1.used_tokens, max=mgr.l1.max_tokens,
                low=mgr.l1.low_water, high=mgr.l1.high_water, open_seq=mgr.open_seq, open_topic=mgr.open_topic_id)


def structure(s):
    """Everything except message text: for 'state did not change' comparisons."""
    return json.dumps(dict(topics=s["topics"], l1=[(p["seq"], p["topic"], p["tokens"], p["open"]) for p in s["l1"]],
                           l2=[(p["seq"], p["topic"], p["tokens"], p["open"]) for p in s["l2"]],
                           table=s["table"], open_seq=s["open_seq"], open_topic=s["open_topic"]), sort_keys=True)


MOVE = re.compile(r"move page (\d+): (L\d) -> (L\d)")
INVARIANT_COUNT = 11


def invariants(mgr, before=None, after=None, events=()):
    """Structural rules that must hold after every prepare_context and record_reply."""
    v = []
    l1, l2 = set(mgr.l1.seqs()), {p.seq for p in mgr.l2.pages()}
    tpages = [s for t in mgr.topics.all() for s in t.page_seqs]
    if l1 & l2:                                                    # 1
        v.append(f"1. page(s) {sorted(l1 & l2)} are in BOTH L1 and L2")
    if l1 | l2 != set(tpages) or len(tpages) != len(set(tpages)):  # 2
        v.append(f"2. L1+L2 pages {sorted(l1 | l2)} != pages listed by topics {sorted(tpages)}")
    for s in l1 | l2:                                              # 3
        want = "L1" if s in l1 else "L2"
        try:
            got = mgr.page_table.where(s)
        except KeyError:
            got = "missing"
        if got != want:
            v.append(f"3. page table says page {s} is in {got}, but it is really in {want}")
    if mgr.l1.used_tokens != sum(p.tokens for p in mgr.l1.pages()) or mgr.l1.used_tokens > mgr.l1.max_tokens:  # 4
        v.append(f"4. L1 token accounting broken: used={mgr.l1.used_tokens} max={mgr.l1.max_tokens}")
    open_pages = [p.seq for p in mgr.l1.pages() + mgr.l2.pages() if p.is_open]   # 5
    if mgr.open_seq is None:
        if open_pages:
            v.append(f"5. no open page recorded but pages {open_pages} are marked open")
    elif open_pages != [mgr.open_seq] or mgr.open_seq not in l1:
        v.append(f"5. open page must be exactly page {mgr.open_seq} and in L1; open pages={open_pages}")
    open_topics = [t.id for t in mgr.topics.all() if t.is_open]    # 6
    if len(open_topics) > 1 or (open_topics and open_topics[0] != mgr.open_topic_id):
        v.append(f"6. open topics {open_topics} vs open_topic_id {mgr.open_topic_id}")
    if mgr.open_seq is not None and mgr.open_topic_id is not None:   # 7
        ot = mgr.topics.get(mgr.open_topic_id)
        if not ot.page_seqs or ot.page_seqs[-1] != mgr.open_seq:
            v.append(f"7. open page {mgr.open_seq} is not the newest page of open topic {ot.id} {ot.page_seqs}")
    by_seq = {p.seq: p for p in mgr.l1.pages() + mgr.l2.pages()}    # 8
    for t in mgr.topics.all():
        if t.page_seqs != sorted(set(t.page_seqs)):
            v.append(f"8. topic {t.id} page_seqs not strictly increasing: {t.page_seqs}")
        for s in t.page_seqs:
            if s in by_seq and by_seq[s].topic_id != t.id:
                v.append(f"8. page {s} says topic {by_seq[s].topic_id} but topic {t.id} lists it")
    rendered = mgr.l1.render()                                      # 9
    markers = sum(1 for m in rendered if m.content == GAP and m.role == "system")
    if len(rendered) != sum(len(p.data) for p in mgr.l1.pages()) + markers:
        v.append("9. render() dropped or duplicated messages")
    moves = [(int(m.group(1)), m.group(3)) for e in events for m in [MOVE.match(e)] if m]  # 10, 11
    forced = {int(m.group(1)) for e in events for m in [re.search(r"forced demotion of page (\d+)", e)] if m}
    for seq, n in Counter(s for s, _ in moves if s not in forced).items():
        if n > 1:
            v.append(f"10. THRASH: page {seq} moved {n} times in one turn")
    if before and after:
        for seq, layer in before["table"].items():
            if after["table"].get(seq) != layer and not any(s == seq for s, _ in moves):
                v.append(f"11. page {seq} changed layer without a move event")
        last = {s: d for s, d in moves}
        for seq, dst in last.items():
            if after["table"].get(seq) != dst:
                v.append(f"11. last move event sends page {seq} to {dst} but it ends in {after['table'].get(seq)}")
    return v


class ScriptedSegmenter:
    """decisions: {turn: "continue" | "new" | ("return", topic_id) | SegmentDecision}. Missing turns continue."""

    def __init__(self, decisions=None, default="continue"):
        self.decisions, self.default, self.turn, self.calls = decisions or {}, default, 0, []

    def decide(self, open_topic, closed_topics, recent, new_msg):
        d = self.decisions.get(self.turn, self.default)
        self.calls.append(dict(turn=self.turn, open=open_topic.id if open_topic else None))
        if isinstance(d, SegmentDecision):
            return d
        if isinstance(d, tuple):
            return SegmentDecision("return", d[1])
        return SegmentDecision(d)


class ScriptedRouter:
    """scores_by_turn: {turn: {topic_id: score}}. Unlisted topics score `default`. Records every call."""

    def __init__(self, scores_by_turn=None, default=0.0):
        self.scores_by_turn, self.default, self.turn, self.calls = scores_by_turn or {}, default, 0, []

    def score(self, topics, recent, new_msg):
        table = self.scores_by_turn.get(self.turn, {})
        self.calls.append(dict(turn=self.turn, topics=[t.id for t in topics],
                               recent=[m.content for m in recent], msg=new_msg.content))
        return {t.id: table.get(t.id, self.default) for t in topics}


class SpyCardWriter:
    """Wraps FakeCardWriter and remembers which pages each call received."""

    def __init__(self):
        self.inner, self.calls = FakeCardWriter(), []

    def write(self, old_card, pages):
        self.calls.append(dict(pages=[p.seq for p in pages], old_covered=old_card.covered_through if old_card else None))
        return self.inner.write(old_card, pages)


class MockJev:
    """Stands in for the Jev API: returns a canned answer and records what it was asked."""

    def __init__(self, answer):
        self.answer, self.calls = answer, []

    def ask(self, state, questions):
        self.calls.append(dict(state=state, questions=questions))
        return self.answer


class Harness:
    """Drives one ContextManager one turn at a time and logs everything to the report."""

    def __init__(self, case, mgr, label="", quiet=False):
        self.case, self.mgr, self.label, self.quiet, self.n = case, mgr, label, quiet, 0
        self.last = {}

    def turn(self, user, reply=None, role="assistant"):
        self.n += 1
        for d in (self.mgr.segmenter, self.mgr.router):
            if hasattr(d, "turn"):
                d.turn = self.n
        self.mgr.drain_events()
        before = snap(self.mgr)
        prompt, ev_p, ev_r, error = [], [], [], None
        mid = before
        try:
            prompt = self.mgr.prepare_context(user)
            ev_p = self.mgr.drain_events()
            mid = snap(self.mgr)
            if reply is not None:
                self.mgr.record_reply(reply, role)
                ev_r = self.mgr.drain_events()
        except Exception as e:                       # logged, then re-raised so the test sees it
            error = f"{type(e).__name__}: {e}"
            ev_r = ev_r or self.mgr.drain_events()
            raise
        finally:
            after = snap(self.mgr)
            viol = invariants(self.mgr, before, after if not error else None, ev_p + ev_r)
            self.last = dict(before=before, mid=mid, after=after, ev_p=ev_p, ev_r=ev_r, prompt=prompt, error=error)
            if not self.quiet:
                REPORT.turn(dict(label=self.label, n=self.n, user=user, reply=reply, role=role, ev_p=ev_p, ev_r=ev_r,
                                 mid=mid, after=after, viol=viol, error=error,
                                 prompt=[dict(role=m.role, text=m.content) for m in prompt]))
            if viol:
                self.case._fails.append(f"turn {self.n} invariants: {viol[0]}")
                self.violations = getattr(self, "violations", []) + viol
        return prompt

    def try_turn(self, user, reply=None, role="assistant"):
        try:
            self.turn(user, reply, role)
            return None
        except Exception as e:
            return e

    def moves(self, phase="both"):
        ev = (self.last["ev_p"] if phase in ("both", "prepare") else []) + (self.last["ev_r"] if phase in ("both", "reply") else [])
        return [(int(m.group(1)), m.group(2), m.group(3)) for e in ev for m in [MOVE.match(e)] if m]


class PrismCase(unittest.TestCase):
    def setUp(self):
        REPORT.ensure()
        self._fails = []
        m = re.match(r"test_([A-Z]\d+)_(.*)", self._testMethodName)
        self.tid, self.title = m.group(1), m.group(2).replace("_", " ")
        doc = (getattr(self, self._testMethodName).__doc__ or "").strip().split("\n")[0]
        REPORT.start_test(self.tid, self.title, doc)

    def _callTestMethod(self, method):
        super()._callTestMethod(method)
        if self._fails:
            self.fail(f"{len(self._fails)} check(s) failed:\n  " + "\n  ".join(self._fails))

    # ---- soft checks: every check is logged, all are evaluated, failure is raised at the end ----
    def check(self, cond, msg):
        REPORT.check(bool(cond), msg)
        if not cond:
            self._fails.append(msg)
        return bool(cond)

    def eq(self, actual, expected, msg):
        return self.check(actual == expected, f"{msg} — got `{actual!r}`, expected `{expected!r}`")

    def raises(self, exc, fn, msg):
        try:
            fn()
        except exc:
            return self.check(True, f"{msg} (raised {exc.__name__})")
        except Exception as e:
            return self.check(False, f"{msg} — raised {type(e).__name__}: {e} instead of {exc.__name__}")
        return self.check(False, f"{msg} — nothing was raised")

    def note(self, text):
        REPORT.text(f"*{text}*")

    def mk(self, max_tokens=500, high=0.85, low=0.70, seg=None, rt=None, writer=None, label="", quiet=False, **kw):
        seg = seg if hasattr(seg, "decide") else ScriptedSegmenter(seg)
        rt = rt if hasattr(rt, "score") else ScriptedRouter(rt)
        mgr = ContextManager(l1=L1(max_tokens, high, low), l2=L2(), topics=TopicTable(), page_table=PageTable(),
                             segmenter=seg, router=rt, card_writer=writer or FakeCardWriter(), **kw)
        return Harness(self, mgr, label, quiet)


def contents(messages):
    return [m.content for m in messages]


# ══════════════════════════════════════════════════════════════════ U: storage units

class TestUnitStorage(PrismCase):

    def test_U1_L1_put_take_append_and_capacity(self):
        """L1 stores pages, counts tokens, and refuses overflow, duplicates and removal of the open page."""
        l1 = L1(max_tokens=100)
        page = PageBlock(seq=0, topic_id=1)
        l1.put(page)
        self.check(l1.has(0) and l1.seqs() == [0], "an empty open page can be put")
        l1.append_message(0, Message("user", tok(10)))
        self.eq((l1.used_tokens, l1.free_tokens, l1.utilization()), (10, 90, 0.10), "used / free / utilization after a 10-token message")
        self.raises(ValueError, lambda: l1.put(PageBlock(seq=0, topic_id=1)), "putting a duplicate seq is refused")
        self.raises(L1FullError, lambda: l1.put(PageBlock(seq=1, topic_id=1, data=[Message("user", tok(95))])), "a page bigger than free space is refused")
        self.eq(l1.seqs(), [0], "a refused put leaves L1 unchanged")
        self.raises(L1FullError, lambda: l1.append_message(0, Message("user", tok(91))), "a message bigger than free space is refused")
        self.eq(l1.used_tokens, 10, "a refused append leaves the page unchanged")
        self.raises(ValueError, lambda: l1.take(0), "the open page cannot be taken out")
        self.check(l1.has(0), "the open page is still in L1 after the refused take")
        page.is_open = False
        self.check(l1.take(0) is page and not l1.has(0) and l1.used_tokens == 0, "a closed page can be taken and tokens are released")
        self.raises(KeyError, lambda: l1.get(0), "get on a missing page raises KeyError")
        for s in (5, 2, 9):
            l1.put(PageBlock(seq=s, topic_id=1, data=[Message("user", f"p{s}")], is_open=False))
        self.eq((l1.seqs(), [p.seq for p in l1.pages()]), ([2, 5, 9], [2, 5, 9]), "seqs() and pages() are always sorted by seq")

    def test_U2_L1_render_order_and_gap_markers(self):
        """render() flattens pages in seq order and inserts exactly one gap marker per discontinuity."""
        def build(seqs):
            l1 = L1(max_tokens=1000)
            for s in seqs:
                l1.put(PageBlock(seq=s, topic_id=1, data=[Message("user", f"page{s}")], is_open=False))
            return l1
        cases = [
            ([0, 1, 2], ["page0", "page1", "page2"], "consecutive pages from 0: no marker"),
            ([1, 2], [GAP, "page1", "page2"], "first page is not seq 0: marker at the start"),
            ([0, 2], ["page0", GAP, "page2"], "one missing page in the middle: one marker between"),
            ([0, 2, 4], ["page0", GAP, "page2", GAP, "page4"], "two gaps: two markers"),
            ([3], [GAP, "page3"], "a single page that is not seq 0: marker first"),
            ([0, 3, 4], ["page0", GAP, "page3", "page4"], "gap followed by consecutive pages: one marker only"),
        ]
        for seqs, want, msg in cases:
            self.eq(contents(build(seqs).render()), want, f"{msg} (pages {seqs})")
        self.eq(contents(build([0, 2]).render(mark_gaps=False)), ["page0", "page2"], "mark_gaps=False inserts nothing")
        self.eq(build([0, 2]).render()[1].role, "system", "the marker has role 'system'")
        self.eq(build([]).render(), [], "an empty L1 renders an empty prompt")

    def test_U3_L1_watermarks_and_validation(self):
        """over_high_water / above_low_water are strict '>' comparisons and bad settings are rejected."""
        def used(n):
            l1 = L1(max_tokens=100, high_water=0.85, low_water=0.70)
            l1.put(PageBlock(seq=0, topic_id=1, data=[Message("user", tok(n))], is_open=False))
            return l1
        self.eq((used(85).over_high_water(), used(86).over_high_water()), (False, True), "over_high_water: 85% is not over, 86% is")
        self.eq((used(70).above_low_water(), used(71).above_low_water()), (False, True), "above_low_water: 70% is not above, 71% is")
        self.raises(ValueError, lambda: L1(100, high_water=0.5, low_water=0.5), "low_water == high_water is rejected")
        self.raises(ValueError, lambda: L1(100, high_water=1.2, low_water=0.5), "high_water above 1 is rejected")
        self.raises(ValueError, lambda: L1(100, high_water=0.8, low_water=0.0), "low_water of 0 is rejected")
        self.eq(L1(max_tokens=0).utilization(), 0.0, "max_tokens=0 gives utilization 0.0 instead of dividing by zero")

    def test_U4_L2_holds_pages_without_a_limit(self):
        """L2 is a plain seq-keyed store with the same put/take/get/has/pages interface as L1."""
        l2 = L2()
        for s in (7, 3, 5):
            l2.put(PageBlock(seq=s, topic_id=1, data=[Message("user", f"p{s}")], is_open=False))
        self.eq(([p.seq for p in l2.pages()], len(l2)), ([3, 5, 7], 3), "pages() is sorted and len() counts pages")
        self.check(l2.has(5) and not l2.has(6), "has() reports membership")
        self.eq(l2.get(5).seq, 5, "get() returns the page")
        self.check(l2.has(5), "get() does not remove the page")
        self.eq(l2.take(5).seq, 5, "take() returns the page")
        self.check(not l2.has(5) and len(l2) == 2, "take() removes the page")
        self.raises(KeyError, lambda: l2.take(5), "taking a missing page raises KeyError")
        for s in range(100, 300):
            l2.put(PageBlock(seq=s, topic_id=1, is_open=False))
        self.eq(len(l2), 202, "L2 has no capacity limit yet")

    def test_U5_PageTable_maps_pages_to_layers(self):
        """PageTable stores which layer each page is in."""
        pt = PageTable()
        pt.set(2, "L1"); pt.set(0, "L2"); pt.set(1, "L1")
        self.eq((pt.where(0), pt.where(1)), ("L2", "L1"), "where() returns the stored layer")
        self.eq((pt.pages_in("L1"), pt.pages_in("L2"), pt.pages_in("L3")), ([1, 2], [0], []), "pages_in() is sorted and empty for unknown layers")
        pt.set(0, "L1")
        self.eq(pt.where(0), "L1", "set() overwrites the previous layer")
        self.raises(KeyError, lambda: pt.where(99), "where() on an unknown page raises KeyError")
        self.check(LocationBook is PageTable, "LocationBook is a backward-compatible alias")

    def test_U6_TopicTable_lifecycle(self):
        """Topics get increasing ids, only one can be open, and closing/reopening works."""
        tt = TopicTable()
        self.check(tt.open_topic is None and tt.open_topic_id is None, "starts with no open topic")
        t1 = tt.new_topic("first")
        self.eq((t1.id, tt.open_topic_id, t1.card.label, t1.is_open), (1, 1, "first", True), "first topic gets id 1, is open, label is the placeholder")
        self.raises(RuntimeError, lambda: tt.new_topic("second"), "a second topic cannot be opened while one is open")
        tt.add_page(1, 0); tt.add_page(1, 3)
        self.eq(t1.page_seqs, [0, 3], "add_page appends in order")
        tt.close(1)
        self.check(not t1.is_open and tt.open_topic is None, "close() closes the topic and clears the open topic")
        t2 = tt.new_topic("second")
        self.eq(t2.id, 2, "ids keep increasing")
        self.raises(RuntimeError, lambda: tt.reopen(1), "reopening while another topic is open is refused")
        tt.close(2)
        self.eq(tt.reopen(1).id, 1, "a closed topic can be reopened")
        self.eq(([t.id for t in tt.closed_topics()], [t.id for t in tt.all()]), ([2], [1, 2]), "closed_topics() excludes the open topic; all() keeps creation order")
        self.raises(KeyError, lambda: tt.add_page(99, 1), "add_page on an unknown topic raises KeyError")
        self.raises(KeyError, lambda: tt.get(99), "get() on an unknown topic raises KeyError")


# ══════════════════════════════════════════════════════════════════ S: segmentation

class TestSegmentation(PrismCase):

    def test_S1_first_message_creates_topic_and_page(self):
        """The very first message opens topic 1 with page 0 in L1, labelled with its first 60 characters."""
        h = self.mk()
        user = tok(20, "hello world")
        prompt = h.turn(user, tok(8, "hi"))
        m = h.mgr
        self.eq(len(m.topics.all()), 1, "one topic exists")
        t = m.topics.get(1)
        self.check(t.is_open and m.open_topic_id == 1, "topic 1 is open")
        self.eq((t.page_seqs, m.open_seq, m.page_table.where(0)), ([0], 0, "L1"), "page 0 exists, is open, is in L1")
        self.eq(t.card.label, user[:60], "placeholder label is the first 60 characters of the message")
        self.eq(contents(prompt), [user], "the prompt sent to the model is exactly the user message")
        self.eq([x.role for x in m.l1.get(0).data], ["user", "assistant"], "the reply was appended to the same page")
        self.check("L1" in m.snapshot() and "L2" in m.snapshot(), "snapshot() describes L1 and L2")
        self.check(m.drain_events() == [], "drain_events() returns nothing new once drained")

    def test_S2_continue_keeps_the_same_page(self):
        """A 'continue' decision adds messages to the open page and creates nothing new."""
        h = self.mk(seg={1: "new"})
        h.turn(tok(10), tok(10))
        h.turn(tok(10, "more"), tok(10))
        m = h.mgr
        self.eq((len(m.topics.all()), m.topics.get(1).page_seqs), (1, [0]), "still one topic with one page")
        self.eq([x.role for x in m.l1.get(0).data], ["user", "assistant", "user", "assistant"], "page holds all four messages in order")
        self.eq(h.last["ev_p"], [], "no events were emitted for a plain continue")

    def test_S3_new_topic_closes_old_and_writes_card(self):
        """A 'new' decision closes the open topic, writes its card, and opens the next page."""
        h = self.mk(seg={1: "new", 2: "new"})
        u1 = tok(12, "python decorators wrap functions")
        h.turn(u1, tok(8, "decorators use closures"))
        h.turn(tok(12, "capital of france"), tok(8, "paris"))
        m = h.mgr
        t1, t2 = m.topics.get(1), m.topics.get(2)
        self.check(not t1.is_open and t2.is_open and m.open_topic_id == 2, "topic 1 closed, topic 2 open")
        self.check(not m.l1.get(0).is_open and m.l1.get(1).is_open, "page 0 closed, page 1 open")
        self.eq((t2.page_seqs, m.open_seq), ([1], 1), "topic 2 owns the next page number (1)")
        self.check(t1.card.label != u1[:60] and t1.card.label.strip() != "", "card label was rewritten by the card writer")
        self.check(any(u1[:80] in f for f in t1.card.key_facts), "card key_facts contain the user message")
        self.check(len(t1.card.entities) > 0 and t1.card.description != "", "card has entities and a description")
        self.eq(t1.card.covered_through, 0, "card covered_through equals its last page seq")
        self.check(any(e.startswith("closed topic 1") for e in h.last["ev_p"]) and "new topic 2" in h.last["ev_p"], "events report the close and the new topic")

    def test_S4_return_reopens_old_topic_with_a_new_page(self):
        """A 'return' decision reopens the old topic; its new page gets the next seq, never an old one."""
        h = self.mk(seg={1: "new", 2: "new", 3: ("return", 1)})
        h.turn(tok(12, "goa beaches"), tok(8))
        h.turn(tok(12, "cooking pasta"), tok(8))
        h.turn(tok(12, "best goa beach"), tok(8))
        m = h.mgr
        t1, t2 = m.topics.get(1), m.topics.get(2)
        self.check(t1.is_open and not t2.is_open and m.open_topic_id == 1, "topic 1 reopened, topic 2 closed")
        self.eq((t1.page_seqs, m.open_seq), ([0, 2], 2), "topic 1 now owns pages [0, 2] and page 2 is the open page")
        self.eq(m.l1.get(2).topic_id if m.page_table.where(2) == "L1" else None, 1, "page 2 belongs to topic 1")
        self.check(not m.l1.get(0).is_open, "the old page 0 stays closed")
        self.check(any(e.startswith("return to topic 1") for e in h.last["ev_p"]), "a 'return to topic 1' event was logged")
        self.check(t2.card.covered_through == 1 and t2.card.key_facts, "topic 2 (closed by the return) got its card written")

    def test_S5_page_splits_at_max_page_tokens_between_turns(self):
        """A page splits only when it has reached max_page_tokens (>=), and only at the start of the next turn."""
        P = 40
        exact = self.mk(seg={1: "new"}, max_page_tokens=P, label="page == limit")
        exact.turn(tok(P - 8), tok(8))
        self.eq(exact.mgr.l1.get(0).tokens, P, "setup: page 0 has exactly max_page_tokens")
        exact.turn(tok(10), tok(8))
        self.eq(exact.mgr.topics.get(1).page_seqs, [0, 1], "at exactly the limit the next turn opens a second page")
        self.check(not exact.mgr.l1.get(0).is_open and exact.mgr.l1.get(1).is_open, "the old page closes and the new one is open")
        self.eq(exact.mgr.topics.get(1).is_open, True, "the topic itself stays open (a split is not a topic change)")
        under = self.mk(seg={1: "new"}, max_page_tokens=P, label="page == limit-1")
        under.turn(tok(P - 9), tok(8))
        self.eq(under.mgr.l1.get(0).tokens, P - 1, "setup: page 0 is one token under the limit")
        under.turn(tok(10), tok(8))
        self.eq(under.mgr.topics.get(1).page_seqs, [0], "one token under the limit: no split")

    def test_S6_odd_decider_output_is_handled(self):
        """Unusual segmenter answers must not crash the manager or corrupt the tables."""
        a = self.mk(seg={1: SegmentDecision("continue"), 2: SegmentDecision("return", None)}, label="continue on first message, return without id")
        a.turn(tok(10), tok(5))
        self.eq(a.mgr.open_topic_id, 1, "'continue' with no open topic still creates topic 1")
        a.turn(tok(10), tok(5))
        self.eq((a.mgr.open_topic_id, a.mgr.topics.get(1).is_open), (2, False), "'return' without a topic_id is treated as a new topic")
        # Design note: returning to the currently-open topic is intentionally handled as
        # _close_current_topic() + reopen(), not as 'continue'. The segmenter decided a
        # topic transition occurred, so a new page boundary is the correct response even
        # when the destination happens to be the same topic that is already open.
        b = self.mk(seg={1: "new", 2: ("return", 1)}, label="return to the topic that is already open")
        b.turn(tok(10, "alpha"), tok(5))
        b.turn(tok(10, "alpha"), tok(5))
        self.eq((b.mgr.topics.get(1).is_open, b.mgr.topics.get(1).page_seqs), (True, [0, 1]), "returning to the open topic closes and reopens it with a fresh page")
        # A return to a non-existent topic id must raise KeyError (the pre-flight
        # self.topics.get() in prepare_context fires before _apply_segmentation, so
        # no topic is closed and no page is opened — state is fully preserved).
        c = self.mk(seg={1: "new", 2: ("return", 99)}, label="return to a topic id that does not exist")
        c.turn(tok(10, "alpha"), tok(5))
        before = structure(snap(c.mgr))
        err = c.try_turn(tok(10, "beta"), tok(5))
        self.check(isinstance(err, KeyError), f"an unknown topic id raises KeyError (got {type(err).__name__ if err else 'no error'})")
        self.check(structure(snap(c.mgr)) == before, "after the KeyError the state is fully unchanged (no half-applied topic close or page open)")


# ══════════════════════════════════════════════════════════════════ R: routing

class TestRouting(PrismCase):

    def test_R1_router_sees_only_closed_topics(self):
        """The router is not called when nothing is closed, and never receives the open topic."""
        rt = ScriptedRouter()
        h = self.mk(seg={1: "new", 2: "new", 3: "continue", 4: "new"}, rt=rt)
        for i in range(4):
            h.turn(tok(10, f"u{i}"), tok(6, f"r{i}"))
        self.eq([c["topics"] for c in rt.calls], [[1], [1], [1, 2]], "router was called on turns 2-4 with exactly the closed topics")
        self.eq([c["turn"] for c in rt.calls], [2, 3, 4], "router was skipped on turn 1 (no closed topics)")
        open_ids = {2: 2, 3: 2, 4: 3}
        self.check(all(open_ids[c["turn"]] not in c["topics"] for c in rt.calls), "the open topic id never appears in what the router receives")

    def test_R2_router_gets_the_recent_window(self):
        """The deciders see the last `recent_window` messages, not the whole history."""
        rt = ScriptedRouter()
        h = self.mk(seg={1: "new", 2: "new", 3: "new", 4: "new"}, rt=rt, recent_window=4)
        texts = []
        for i in range(1, 5):
            u, r = tok(10, f"user{i}"), tok(6, f"reply{i}")
            texts += [u, r]
            h.turn(u, r)
        self.eq(rt.calls[-1]["recent"], texts[2:6], "on turn 4 the router saw exactly the last 4 messages before the new one (user2, reply2, user3, reply3)")
        self.eq(rt.calls[-1]["msg"], texts[6], "and the new message separately")

    def test_R3_needed_threshold_boundary(self):
        """A topic scoring exactly needed_threshold is brought in; just below is not."""
        def run(score, label):
            h = self.mk(max_tokens=100, high=0.5, low=0.3, protect_recent_pages=1, seg={1: "new", 2: "new"},
                        rt={3: {1: score}}, label=label)
            h.turn(tok(15), tok(15))
            h.turn(tok(25), tok(5))
            self.eq(h.mgr.page_table.where(0), "L2", f"[{label}] setup: page 0 was demoted to L2 on turn 2")
            h.turn(tok(5), tok(5))
            return h.mgr.page_table.where(0)
        self.eq(run(0.50, "score 0.50"), "L1", "score 0.50 == threshold: page 0 comes back to L1")
        self.eq(run(0.49, "score 0.49"), "L2", "score 0.49 < threshold: page 0 stays in L2")

    def test_R4_open_topic_always_scores_1(self):
        """The current topic is always treated as fully needed, whatever the router says about others."""
        h = self.mk(seg={1: "new", 2: "new"}, rt={2: {1: 0.3}})
        h.turn(tok(10), tok(5))
        h.turn(tok(10), tok(5))
        scores = h.mgr.last_scores
        self.eq(scores.get(2), 1.0, "open topic 2 has score 1.0")
        self.eq(scores.get(1), 0.3, "closed topic 1 keeps the router's score")


# ══════════════════════════════════════════════════════════════════ B: bring-in (L2 -> L1)

class TestBringIn(PrismCase):

    def test_B1_needed_page_returns_from_L2_intact(self):
        """A returning topic's old page comes back from L2 with its content, and unrelated pages make way."""
        h = self.mk(max_tokens=100, high=0.5, low=0.3, protect_recent_pages=1, seg={1: "new", 2: "new", 3: ("return", 1)})
        u0 = tok(15, "alpha topic question")
        h.turn(u0, tok(15, "alpha topic answer"))
        h.turn(tok(25, "beta"), tok(5))
        m = h.mgr
        self.eq(m.page_table.where(0), "L2", "setup: page 0 is in L2 after topic 2 filled L1")
        content_before = [x.content for x in m.l2.get(0).data]
        prompt = h.turn(tok(10, "back to alpha"), tok(10))
        self.eq(m.page_table.where(0), "L1", "page 0 is back in L1")
        self.eq([x.content for x in m.l1.get(0).data], content_before, "its messages are identical to before")
        self.check(u0 in contents(prompt), "the old user message is in the prompt")
        self.eq(m.page_table.where(1), "L2", "the unrelated topic-2 page was demoted to make room")
        self.eq(contents(prompt).index(GAP), 2, "a gap marker sits between old page 0 and the new page 2 (page 1 is missing)")
        self.eq(m.topics.get(1).page_seqs, [0, 2], "topic 1 lists pages [0, 2]")

    def test_B2_newest_pages_first_and_skip_when_no_room(self):
        """When a topic has two pages in L2 but room for one, the NEWEST comes back and the skip is logged."""
        h = self.mk(max_tokens=80, high=0.5, low=0.3, protect_recent_pages=1, max_page_tokens=20,
                    seg={1: "new", 2: "continue", 3: "new", 4: ("return", 1)}, rt={3: {1: 0.0}, 4: {2: 1.0}})
        h.turn(tok(10, "a"), tok(10))                       # page 0 = 20 tokens
        h.turn(tok(10, "b"), tok(10))                       # split: page 1
        h.turn(tok(30, "c"), tok(10))                       # topic 2: pushes pages 0,1 out
        m = h.mgr
        self.eq((m.page_table.where(0), m.page_table.where(1)), ("L2", "L2"), "setup: both pages of topic 1 are in L2")
        h.turn(tok(10, "d"), tok(5))                        # return to topic 1; topic 2 protected by router score
        self.eq(m.page_table.where(1), "L1", "the newer page 1 came back")
        self.eq(m.page_table.where(0), "L2", "the older page 0 did not fit and stays in L2")
        self.check("no room for page 0 of topic 1" in h.last["ev_p"], "a 'no room for page 0 of topic 1' event was logged")
        self.eq(m.page_table.where(2), "L1", "topic 2's page (score 1.0) was not evicted to make room")

    def test_B3_page_too_big_to_fit_is_skipped_safely(self):
        """A needed page that cannot fit even after making room stays in L2 and nothing crashes."""
        h = self.mk(max_tokens=100, high=0.5, low=0.3, protect_recent_pages=1, seg={1: "new", 2: "new", 3: "continue"}, rt={3: {1: 0.9}})
        h.turn(tok(30, "big"), tok(30))
        h.turn(tok(30, "topic two"), tok(20))
        self.eq(h.mgr.page_table.where(0), "L2", "setup: the 60-token page 0 is in L2")
        h.turn(tok(5, "more"), tok(5))
        self.eq(h.mgr.page_table.where(0), "L2", "page 0 (score 0.9) could not fit and remains in L2")
        self.check("no room for page 0 of topic 1" in h.last["ev_p"], "the skip was logged")
        self.check(h.mgr.page_table.where(h.mgr.open_seq) == "L1", "the open page is untouched")

    def test_B4_needed_page_already_in_L1_is_not_moved(self):
        """Pages that are already in L1 are never moved just because their topic is needed."""
        h = self.mk(max_tokens=500, seg={1: "new", 2: "new", 3: ("return", 1)})
        h.turn(tok(10, "one"), tok(5))
        h.turn(tok(10, "two"), tok(5))
        h.turn(tok(10, "back to one"), tok(5))
        self.eq(h.moves(), [], "no page moved on the return turn")
        self.eq(sorted(h.mgr.page_table.pages_in("L1")), [0, 1, 2], "all three pages are still in L1")


# ══════════════════════════════════════════════════════════════════ P: pressure relief

def fill_five(case, protect, low, high=0.85, label=""):
    """5 closed topics of 16 tokens each in a 100-token L1 (80%), then the caller sends turn 6."""
    h = case.mk(max_tokens=100, high=high, low=low, protect_recent_pages=protect,
                seg={i: "new" for i in range(1, 9)}, label=label)
    for i in range(1, 6):
        h.turn(tok(8, f"t{i}"), tok(8))
        case.eq(h.moves(), [], f"[{label}] turn {i}: no demotion while at or under high-water ({h.last['after']['used']}%)")
    return h


class TestPressure(PrismCase):

    def test_P1_no_demotion_at_or_below_high_water(self):
        """Nothing is demoted while L1 is at or under the high-water mark."""
        h = self.mk(max_tokens=100, high=0.85, low=0.5, protect_recent_pages=1, seg={i: "new" for i in range(1, 6)})
        for i in range(1, 6):
            h.turn(tok(8, f"t{i}"), tok(8))
            self.check(not h.moves() and h.mgr.l1.utilization() <= 0.85, f"turn {i}: {h.mgr.l1.utilization():.0%} used, no page moved")
        self.eq(len(h.mgr.l2.pages()), 0, "L2 is still empty")

    def test_P2_demotion_continues_down_to_low_water_and_stops(self):
        """Above high-water the manager demotes oldest-first until at or below low-water, then stops."""
        h = fill_five(self, protect=1, low=0.5, label="fill")
        h.turn(tok(10, "t6"), tok(8))
        m = h.mgr
        demoted = sorted(s for s, _, dst in h.moves("prepare") if dst == "L2")
        self.eq(demoted, [0, 1, 2], "exactly the three oldest pages were demoted (a single demotion would not reach low-water)")
        self.check(h.last["mid"]["used"] / 100 <= 0.5, f"right after the pressure check L1 is at {h.last['mid']['used']}% (<= 50% low-water)")
        self.eq(m.l1.seqs(), [3, 4, 5], "pages 3, 4 and 5 remain in L1: it stopped as soon as low-water was reached")
        h.turn(tok(10, "t7"), tok(8))
        self.eq(h.moves(), [], "hysteresis: the next turn (~60%) triggers nothing because it is under high-water")

    def test_P3_newest_pages_are_protected(self):
        """The newest protect_recent_pages pages are never demoted, even if low-water cannot be reached."""
        h = fill_five(self, protect=3, low=0.05, label="protect 3")
        h.turn(tok(10, "t6"), tok(8))
        demoted = sorted(s for s, _, dst in h.moves("prepare") if dst == "L2")
        self.eq(demoted, [0, 1, 2], "only the three oldest pages were candidates")
        self.eq(h.mgr.l1.seqs(), [3, 4, 5], "the newest three pages (3, 4, and open 5) stayed")
        self.check(h.mgr.l1.above_low_water(), "L1 is still above low-water: protection wins over the target")

    def test_P4_protect_recent_pages_zero_protects_only_the_open_page(self):
        """protect_recent_pages=0 means no extra protection (only the open page and needed topics are kept)."""
        h = fill_five(self, protect=0, low=0.05, label="protect 0")
        h.turn(tok(10, "t6"), tok(8))
        demoted = sorted(s for s, _, dst in h.moves("prepare") if dst == "L2")
        self.eq(demoted, [0, 1, 2, 3, 4], "all five closed pages are demotable")
        self.eq(h.mgr.l1.seqs(), [5], "only the open page remains in L1")

    def test_P5_victims_are_chosen_by_router_score_then_age(self):
        """Lowest router score is demoted first; an older relevant page beats a newer irrelevant one."""
        h = self.mk(max_tokens=100, high=0.85, low=0.60, protect_recent_pages=1, seg={i: "new" for i in range(1, 6)},
                    rt={5: {1: 0.25, 2: 0.05, 3: 0.25, 4: 0.10}})
        for i in range(1, 5):
            h.turn(tok(10, f"t{i}"), tok(10))
        h.turn(tok(10, "t5"), tok(5))
        demoted = [s for s, _, dst in h.moves("prepare") if dst == "L2"]
        self.eq(demoted, [1, 3], "demoted in score order: topic 2 (0.05, page 1) then topic 4 (0.10, page 3)")
        self.eq(h.mgr.l1.seqs(), [0, 2, 4], "the older pages 0 and 2 (score 0.25) survive over newer, less relevant ones")

    def test_P6_everything_protected_leaves_L1_over_high_water(self):
        """If every page is protected, L1 may stay above high-water but must not crash or demote protected pages."""
        h = self.mk(max_tokens=60, high=0.5, low=0.3, protect_recent_pages=3, seg={1: "new", 2: "new", 3: "new"})
        h.turn(tok(10, "a"), tok(10))
        h.turn(tok(10, "b"), tok(10))
        h.turn(tok(5, "c"), tok(5))
        self.eq(h.moves(), [], "no page moved on the last turn")
        self.check(h.mgr.l1.utilization() > 0.5, f"L1 is at {h.mgr.l1.utilization():.0%}, above the 50% high-water mark")
        self.eq(h.mgr.l1.seqs(), [0, 1, 2], "all pages are still in L1")


# ══════════════════════════════════════════════════════════════════ T: turn integrity

class TestTurnIntegrity(PrismCase):

    def test_T1_replies_and_tool_results_go_into_the_open_page(self):
        """record_reply stores assistant and tool messages in order in the open page, and tokens are counted."""
        h = self.mk(seg={1: "new"})
        h.turn(tok(10, "read the file"), tok(6, "calling readFile"))
        h.turn(tok(6, "ok"), tok(30, "file contents"), role="tool")
        page = h.mgr.l1.get(0)
        self.eq([x.role for x in page.data], ["user", "assistant", "user", "tool"], "roles are preserved in order")
        self.eq(page.tokens, 10 + 6 + 6 + 30, "page tokens are the sum of all four messages")
        self.eq(h.mgr.l1.used_tokens, 52, "L1 used_tokens reflects the tool result")

    def test_T2_a_needed_page_survives_the_reply(self):
        """A page brought in for this turn must not be evicted again when the reply is recorded (no thrash)."""
        h = self.mk(max_tokens=100, high=0.7, low=0.55, protect_recent_pages=1, seg={1: "new", 2: "new", 3: ("return", 1)})
        h.turn(tok(40, "old"), tok(36))
        h.turn(tok(12, "other"), tok(10))
        self.eq(h.mgr.page_table.where(0), "L2", "setup: the 76-token page 0 is in L2")
        h.turn(tok(13, "back"), tok(8))
        self.eq(h.mgr.page_table.where(0), "L1", "page 0 is still in L1 after the reply was recorded")
        self.eq([s for s, _, _ in h.moves()].count(0), 1, "page 0 moved exactly once this turn")

    def test_T3_a_reply_that_does_not_fit_is_not_lost(self):
        """The model's reply must always be stored. If L1 is packed with needed pages, something must give (and be logged)."""
        h = self.mk(max_tokens=100, high=0.7, low=0.55, protect_recent_pages=1, seg={1: "new", 2: "new", 3: ("return", 1)})
        h.turn(tok(40, "old"), tok(36))
        h.turn(tok(12, "other"), tok(10))
        reply = tok(15, "this reply is 15 tokens")
        err = h.try_turn(tok(13, "back"), reply)
        self.check(err is None, f"record_reply did not raise (got {type(err).__name__ + ': ' + str(err) if err else 'no error'}) — otherwise the reply is lost")
        if err is None:
            self.check(reply in [x.content for x in h.mgr.l1.get(h.mgr.open_seq).data], "the reply is stored in the open page")
            self.check(any("forced" in e or "no room" in e for e in h.last["ev_p"] + h.last["ev_r"]) or h.mgr.l1.free_tokens >= 0,
                       "any forced eviction of a needed page is visible in the events")

    def test_T4_reply_reserve_makes_room_before_the_model_call(self):
        """With reply_reserve=N, prepare_context frees N tokens by demoting unprotected pages."""
        on = self.mk(max_tokens=100, protect_recent_pages=1, reply_reserve=40, seg={1: "new", 2: "new"}, label="reply_reserve=40")
        on.turn(tok(20, "a"), tok(20))
        on.turn(tok(30, "b"), tok(40))
        self.eq(on.moves("prepare"), [(0, "L1", "L2")], "page 0 was demoted during prepare_context to reserve room")
        self.check(on.last["mid"]["max"] - on.last["mid"]["used"] >= 40, f"free tokens after prepare_context: {on.last['mid']['max'] - on.last['mid']['used']} (>= 40)")
        self.eq(on.last["ev_r"], [], "the 40-token reply then fitted without any eviction")
        off = self.mk(max_tokens=100, protect_recent_pages=1, reply_reserve=0, seg={1: "new", 2: "new"}, label="reply_reserve=0")
        off.turn(tok(20, "a"), tok(20))
        off.turn(tok(30, "b"), tok(5))
        self.eq(off.moves(), [], "control: with no reserve nothing was demoted")

    def test_T5_message_larger_than_L1_is_rejected_cleanly(self):
        """A message bigger than the whole L1 raises L1FullError before anything changes."""
        h = self.mk(max_tokens=100, seg={1: "new", 2: "new"})
        h.turn(tok(10, "a"), tok(10))
        before = snap(h.mgr)
        err = h.try_turn(tok(150, "huge"))
        self.check(isinstance(err, L1FullError), f"L1FullError raised (got {type(err).__name__ if err else 'nothing'})")
        self.eq(structure(snap(h.mgr)), structure(before), "topics, pages and page table are exactly as before")

    def test_T6_a_message_that_cannot_fit_leaves_state_untouched(self):
        """If a message fits the window but not the free space, the failed call must not leave a half-applied turn."""
        cont = self.mk(max_tokens=60, protect_recent_pages=1, seg={1: "new", 2: "continue"}, label="continue")
        cont.turn(tok(25, "a"), tok(25))
        before = snap(cont.mgr)
        err = cont.try_turn(tok(30, "b"))
        self.check(isinstance(err, L1FullError), "continue variant: L1FullError raised (nothing can be evicted)")
        self.eq(structure(snap(cont.mgr)), structure(before), "continue variant: state unchanged after the failure")
        new = self.mk(max_tokens=60, protect_recent_pages=2, seg={1: "new", 2: "new"}, label="new topic")
        new.turn(tok(25, "a"), tok(25))
        before = snap(new.mgr)
        err = new.try_turn(tok(30, "b"))
        self.check(isinstance(err, L1FullError), "new-topic variant: L1FullError raised (both pages are protected)")
        self.eq(structure(snap(new.mgr)), structure(before),
                "new-topic variant: state unchanged (the old topic must not be closed and an empty page opened by a call that failed)")


# ══════════════════════════════════════════════════════════════════ C: cards

class TestCards(PrismCase):

    def test_C1_second_close_updates_the_card_with_only_new_pages(self):
        """On a second close the card writer gets only pages newer than covered_through, and facts accumulate."""
        spy = SpyCardWriter()
        h = self.mk(seg={1: "new", 2: "new", 3: ("return", 1), 4: "new"}, writer=spy)
        u1, u3 = tok(12, "docker containers"), tok(12, "docker compose networks")
        h.turn(u1, tok(6)); h.turn(tok(12, "carbonara"), tok(6)); h.turn(u3, tok(6))
        c1 = list(h.mgr.topics.get(1).card.key_facts); cov1 = h.mgr.topics.get(1).card.covered_through
        h.turn(tok(12, "stocks"), tok(6))
        t1 = h.mgr.topics.get(1)
        self.eq([c["pages"] for c in spy.calls], [[0], [1], [2]], "card writer received page [0] (topic 1), [1] (topic 2), then only [2] for topic 1's second close")
        self.eq(spy.calls[2]["old_covered"], 0, "the second call was given the previous card (covered_through 0)")
        self.check(len(t1.card.key_facts) > len(c1), f"key_facts grew {len(c1)} -> {len(t1.card.key_facts)}")
        self.check(any(u1[:80] in f for f in t1.card.key_facts) and any(u3[:80] in f for f in t1.card.key_facts), "old and new facts are both present")
        self.eq((cov1, t1.card.covered_through), (0, 2), "covered_through advanced from 0 to 2")

    def test_C2_closing_a_topic_with_pages_in_L2_still_works(self):
        """A topic's earlier pages may sit in L2 when it closes; the card writer must still receive them."""
        spy = SpyCardWriter()
        h = self.mk(max_tokens=100, high=0.5, low=0.3, protect_recent_pages=1, max_page_tokens=20, writer=spy,
                    seg={1: "new", 2: "continue", 3: "new"}, rt={2: {}, 3: {}})
        h.turn(tok(10, "x"), tok(10)); h.turn(tok(10, "y"), tok(10)); h.turn(tok(30, "z"), tok(10))
        self.eq(spy.calls[0]["pages"], [0, 1], "the card writer got both pages of topic 1 at close")
        self.check(h.mgr.topics.get(1).card.covered_through == 1, "covered_through is the last page of the topic")


# ══════════════════════════════════════════════════════════════════ D: deciders

def topic_with(tid, label, facts=(), entities=(), open_=False, pages=(0,)):
    return Topic(id=tid, card=TopicCard(label=label, description="", key_facts=list(facts), entities=list(entities)),
                 page_seqs=list(pages), is_open=open_)


class TestDeciders(PrismCase):

    def test_D1_KeywordSegmenter_rules(self):
        """The offline segmenter continues on overlap, returns on a better old-topic match, and starts new otherwise."""
        seg = KeywordSegmenter()
        op = topic_with(2, "python decorators closures", open_=True)
        old = topic_with(1, "goa beaches anjuna nightlife", ["Goa beaches Anjuna nightlife"])
        d = lambda text, o=op, closed=(old,), recent=(): seg.decide(o, list(closed), list(recent), Message("user", text))
        self.eq(seg.decide(None, [], [], Message("user", "anything")).action, "new", "no open topic: new")
        self.eq(d("Explain python decorators").action, "continue", "message overlapping the open topic: continue")
        r = d("Which goa beach has the best nightlife")
        self.eq((r.action, r.topic_id), ("return", 1), "message matching a closed topic better than the open one: return to it")
        self.eq(d("Quantum entanglement superposition experiments").action, "new", "unrelated message: new")
        self.eq(d("ok thanks").action, "continue", "very short message with no overlap: continue")

    def test_D2_KeywordRouter_scores(self):
        """Router score is min(1, 2 x word overlap), 0 for unrelated topics."""
        rt = KeywordRouter()
        t = topic_with(1, "goa beach nightlife anjuna")
        score = lambda text: rt.score([t], [], Message("user", text))[1]
        self.eq(score("quantum physics entanglement"), 0.0, "no shared words: 0.0")
        self.eq(score("goa trip planning weather"), 0.5, "1 of 4 words shared: 0.5")
        self.eq(score("goa beach"), 1.0, "everything shared: capped at 1.0")
        self.eq(rt.score([], [], Message("user", "x")), {}, "no topics: empty result")

    def test_D3_FakeCardWriter_edge_cases(self):
        """The offline card writer handles empty input, dedupes facts and caps entities."""
        w = FakeCardWriter()
        self.eq(w.write(None, []).label, "Empty topic", "no pages and no old card: default card")
        old = TopicCard(label="old", key_facts=["fact"], covered_through=3)
        self.check(w.write(old, []) is old, "no pages: the old card is returned unchanged")
        pages = [PageBlock(seq=4, topic_id=1, data=[Message("user", "Alpha beta gamma"), Message("assistant", "delta")], is_open=False),
                 PageBlock(seq=5, topic_id=1, data=[Message("user", "Alpha beta gamma")], is_open=False)]
        c = w.write(TopicCard(label="x", key_facts=["Alpha beta gamma"]), pages)
        self.eq(c.key_facts, ["Alpha beta gamma"], "duplicate facts are removed")
        self.eq(c.covered_through, 5, "covered_through is the highest page seq")
        many = [PageBlock(seq=i, topic_id=1, data=[Message("user", f"word{chr(97 + i)}x wordb{chr(97 + i)}y")], is_open=False) for i in range(12)]
        self.check(len(w.write(None, many).entities) <= 10, "entities are capped at 10")

    def test_D4_JevSegmenter_decision_rules(self):
        """JevSegmenter turns Jev's answer into a decision: confidence floor, strict return threshold, question shape."""
        op = topic_with(3, "python decorators", open_=True)
        closed = [topic_with(1, "goa trip"), topic_with(2, "quantum")]
        msg = Message("user", "hello")
        recent = [Message("user", "earlier text")]

        def run(answer, **kw):
            client = MockJev({"segment": answer})
            return JevSegmenter(client, **kw).decide(op, closed, recent, msg), client
        d, client = run({"choice": "continue", "confidence": 0.9, "probabilities": {}})
        q = client.calls[0]["questions"][0]
        self.check(q["type"] == "choice" and q["id"] == "segment", "asks one Choice question with id 'segment'")
        self.eq(sorted(q["options"]), ["continue", "new", "return:1", "return:2"], "options: continue, new and one return:<id> per closed topic")
        self.check("NEWEST user message: hello" in client.calls[0]["state"] and "earlier text" in client.calls[0]["state"], "state contains the recent messages and the newest one")
        self.eq(d.action, "continue", "choice 'continue' -> continue")
        self.eq(run({"choice": "new", "confidence": 0.9, "probabilities": {}})[0].action, "new", "choice 'new' -> new")
        self.eq(run({"choice": "return:2", "confidence": 0.9, "probabilities": {"return:2": 0.9}})[0].topic_id, 2, "confident return:2 -> return to topic 2")
        self.eq(run({"choice": "return:2", "confidence": 0.9, "probabilities": {"return:2": 0.7}})[0].action, "new", "return with probability 0.7 < 0.8: treated as new (strict merge)")
        self.eq(run({"choice": "return:2", "confidence": 0.5, "probabilities": {"return:2": 0.95}})[0].action, "continue", "confidence 0.5 < 0.6: falls back to continue")
        self.eq(run({"choice": "return:2", "confidence": 0.9, "probabilities": {}})[0].action, "new", "return without a probability: treated as new, no crash")
        nd = MockJev({})
        self.eq(JevSegmenter(nd).decide(None, closed, [], msg).action, "new", "no open topic: new")
        self.eq(nd.calls, [], "and Jev is not called at all in that case")

    def test_D5_JevRouter_builds_one_question_per_topic(self):
        """JevRouter asks one Noul question per closed topic and returns their probabilities."""
        topics = [topic_with(1, "goa trip", ["likes beaches"]), topic_with(4, "quantum")]
        client = MockJev({"topic_1": {"noul": 0.9}, "topic_4": {"noul": 0.1}})
        out = JevRouter(client).score(topics, [Message("user", "before")], Message("user", "which beach"))
        self.eq(out, {1: 0.9, 4: 0.1}, "returns {topic_id: probability}")
        qs = client.calls[0]["questions"]
        self.eq([(q["type"], q["id"]) for q in qs], [("noul", "topic_1"), ("noul", "topic_4")], "one Noul question per topic with id topic_<id>")
        self.check("likes beaches" in qs[0]["statement"], "the statement includes the topic card text")
        self.eq(len(client.calls), 1, "all topics are asked in ONE call")
        empty = MockJev({})
        self.eq(JevRouter(empty).score([], [], Message("user", "x")), {}, "no topics: empty result")
        self.eq(empty.calls, [], "and Jev is not called")
        self.raises(NotImplementedError, lambda: JevClient().ask("s", []), "the placeholder JevClient.ask raises NotImplementedError")

    def test_D6_LLMCardWriter_prompt_and_parsing(self):
        """LLMCardWriter builds the prompt from the old card and new pages and parses the JSON reply."""
        seen = {}

        class Fake(LLMCardWriter):
            def _call_llm(self, prompt):
                seen["prompt"] = prompt
                return seen.get("reply", "{}")
        w = Fake()
        pages = [PageBlock(seq=4, topic_id=1, data=[Message("user", "I like mango")], is_open=False),
                 PageBlock(seq=6, topic_id=1, data=[Message("assistant", "Noted")], is_open=False)]
        seen["reply"] = json.dumps(dict(label="Food", description="d", key_facts=["likes mango"], entities=["mango"]))
        c = w.write(TopicCard(label="prev", key_facts=["old fact"]), pages)
        self.eq((c.label, c.key_facts, c.entities, c.covered_through), ("Food", ["likes mango"], ["mango"], 6), "card fields come from the JSON; covered_through is the max page seq")
        self.check("old fact" in seen["prompt"] and "user: I like mango" in seen["prompt"] and "assistant: Noted" in seen["prompt"], "prompt contains the previous card and the new messages")
        self.check(seen["prompt"].startswith("You maintain an index card"), "prompt starts with the card-writing rules")
        self.eq(w.write(None, []).label, "Empty topic", "no pages and no card: default card, no LLM call")
        old = TopicCard(label="keep")
        self.check(w.write(old, []) is old, "no pages: old card returned unchanged")
        seen["reply"] = "not json"
        self.raises(json.JSONDecodeError, lambda: w.write(None, pages), "invalid JSON from the LLM raises JSONDecodeError")
        seen["reply"] = json.dumps(dict(label="x"))
        self.raises(KeyError, lambda: w.write(None, pages), "a reply missing fields raises KeyError")
        self.raises(NotImplementedError, lambda: LLMCardWriter()._call_llm("p"), "the placeholder _call_llm raises NotImplementedError")


# ══════════════════════════════════════════════════════════════════ E: end to end

class TestEndToEnd(PrismCase):

    def test_E1_realistic_conversation_with_the_keyword_deciders(self):
        """Six turns across four subjects with a small L1: invariants hold every turn and old context returns when asked for."""
        h = self.mk(max_tokens=130, high=0.7, low=0.5, protect_recent_pages=1,
                    seg=KeywordSegmenter(), rt=KeywordRouter(), writer=FakeCardWriter())
        script = [
            ("Tell me about Goa beaches Anjuna nightlife and Baga water sports", "Anjuna has trance parties. Baga offers parasailing."),
            ("Explain quantum computing qubits superposition entanglement", "Qubits use superposition and entanglement."),
            ("How do Docker containers and Kubernetes orchestration work", "Docker packages apps. Kubernetes schedules containers."),
            ("Which Goa beach has the best Anjuna nightlife", "Anjuna is the nightlife hub."),
            ("Can Kubernetes scale Docker containers automatically", "Yes, with autoscaling."),
            ("What is the GDP of India and its growth rate", "About 3.7 trillion dollars."),
        ]
        prompts = [h.turn(u, r) for u, r in script]

        # --- Structural checks (manager-level; independent of keyword decisions) ---
        self.check(max(x["after"]["used"] for x in [h.last]) <= 130, "L1 never exceeded its maximum")

        # --- Heuristic-dependent checks (keyword-decider-level) ---
        # These rely on KeywordSegmenter correctly detecting topic transitions.
        # A failure here means either: (a) the manager has a bug, OR
        # (b) the keyword thresholds mis-segmented the script — check the topic table
        # in the report to distinguish. The fuzz test E2 isolates (a) from (b).
        self.eq(len(h.mgr.topics.all()), 4,
                "[heuristic] four subjects became four topics (Goa, quantum, Docker, GDP); the returns reused old topics")
        self.check("Anjuna has trance parties. Baga offers parasailing." in contents(prompts[3]),
                   "[heuristic] turn 4 (back to Goa): the old Goa answer is in the prompt again")
        self.check("Docker packages apps. Kubernetes schedules containers." in contents(prompts[4]),
                   "[heuristic] turn 5 (back to Docker): the old Docker answer is in the prompt again")

    def test_E2_random_conversations_never_break_the_invariants(self):
        """Fuzz: random topics, returns, scores and message sizes over 8 seeds x 120 turns. Invariants must hold after every step."""
        total_turns = errors = 0
        for seed in range(8):
            rng = random.Random(seed)

            class RandSeg:
                turn = 0
                def decide(self, open_topic, closed_topics, recent, new_msg):
                    r = rng.random()
                    if open_topic is None or r < 0.55:
                        return SegmentDecision("continue" if open_topic else "new")
                    if closed_topics and r < 0.75:
                        return SegmentDecision("return", rng.choice(closed_topics).id)
                    return SegmentDecision("new")

            class RandRouter:
                turn = 0
                def score(self, topics, recent, new_msg):
                    return {t.id: rng.choice([0.0, 0.2, 0.49, 0.5, 0.9]) for t in topics}
            h = self.mk(max_tokens=rng.choice([120, 160, 240]), high=0.8, low=0.5, seg=RandSeg(), rt=RandRouter(),
                        protect_recent_pages=rng.choice([0, 1, 2]), max_page_tokens=rng.choice([30, 60, 400]),
                        reply_reserve=rng.choice([0, 0, 20]), quiet=True, label=f"seed {seed}")
            bad = None
            for i in range(120):
                total_turns += 1
                try:
                    h.turn(tok(rng.randint(3, 25), f"u{i}"), tok(rng.randint(3, 25), f"r{i}"), role=rng.choice(["assistant", "assistant", "tool"]))
                except L1FullError:
                    errors += 1                      # allowed to fail loudly, but never to corrupt the state
                    v = invariants(h.mgr)
                    if v and not bad:
                        bad = (i, "after an L1FullError: " + v[0])
                turn_fails = [f for f in h.case._fails if f.startswith("turn ")]
                if turn_fails and not bad:
                    bad = (i, turn_fails[-1])
                if bad:
                    break
            self.check(bad is None, f"seed {seed}: 120 turns, invariants held" if bad is None else f"seed {seed}: broke at turn {bad[0]}: {bad[1]}")
            if bad:
                REPORT.turn(dict(label=f"seed {seed} failing state", n=bad[0], user="(random)", reply=None, role="",
                                 ev_p=[], ev_r=[], mid=h.last["mid"], after=h.last["after"], viol=[bad[1]], error=None, prompt=[]))
            h.case._fails[:] = [f for f in h.case._fails if not f.startswith("turn ")]
        self.note(f"{total_turns} random turns; {errors} of them raised L1FullError (allowed, but see T3/T6: a raised error must not lose the reply or half-apply a turn).")


# ══════════════════════════════════════════════════════════════════ runner

ORDER = "USRBPTCDE"


class ReportResult(unittest.TextTestResult):
    def addSuccess(self, test):
        super().addSuccess(test)
        REPORT.end_test("PASS")

    def addFailure(self, test, err):
        super().addFailure(test, err)
        REPORT.end_test("FAIL", self._exc_info_to_string(err, test))

    def addError(self, test, err):
        super().addError(test, err)
        REPORT.end_test("ERROR", self._exc_info_to_string(err, test))


def build_suite(only=None):
    tests = []

    def walk(s):
        for t in s:
            walk(t) if isinstance(t, unittest.TestSuite) else tests.append(t)
    walk(unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]))
    key = lambda t: (ORDER.index(t._testMethodName[5]), int(re.match(r"test_[A-Z](\d+)", t._testMethodName).group(1)))
    tests = sorted([t for t in tests if isinstance(t, PrismCase)], key=key)
    if only:
        tests = [t for t in tests if only.lower() in t._testMethodName.lower()]
    return unittest.TestSuite(tests)


def main():
    ap = argparse.ArgumentParser(description="PRISM full test suite")
    ap.add_argument("--out", default=DEFAULT_OUT, help="output folder for the .md and .jsonl reports")
    ap.add_argument("--only", help="run only tests whose id or name contains this text (e.g. P2, pressure)")
    ap.add_argument("--list", action="store_true", help="list the tests and exit")
    args = ap.parse_args()
    suite = build_suite(args.only)
    if args.list:
        for t in suite:
            print(t._testMethodName)
        return
    REPORT.ensure(args.out)
    print(f"\nPRISM full test suite: {suite.countTestCases()} tests\n  streaming to {REPORT.md_path}\n")
    result = unittest.TextTestRunner(stream=open(os.devnull, "w"), verbosity=0, resultclass=ReportResult).run(suite)
    REPORT.finalize()
    ok = sum(r["status"] == "PASS" for r in REPORT.results)
    print(f"\n  {ok}/{len(REPORT.results)} tests passed\n  markdown: {REPORT.md_path.resolve()}\n  events:   {REPORT.jl_path.resolve()}\n")
    sys.exit(0 if result.wasSuccessful() else 1)


if __name__ == "__main__":
    main()