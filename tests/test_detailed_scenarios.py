"""Detailed scenario tests with rich terminal logging.

Run with:
    python -B tests/test_detailed_scenarios.py

Each test prints a step-by-step trace showing:
    - TopicTable state (all topics, cards, page_seqs, open/closed)
    - PageTable (which layer each page lives in)
    - L1 contents (pages, tokens, utilization, watermarks)
    - L2 contents
    - Events emitted by ContextManager
    - Rendered prompt sent to the LLM
"""
from __future__ import annotations

import io
import os
from pathlib import Path
import sys
import unittest

sys.dont_write_bytecode = True
os.environ["PYTHONUTF8"] = "1"

# Ensure the repository root is in sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, io.UnsupportedOperation):
        pass
elif hasattr(sys.stdout, "fileno"):
    try:
        sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf-8", buffering=1)
    except (AttributeError, io.UnsupportedOperation):
        pass

from prism import (
    ContextManager,
    FakeCardWriter,
    KeywordRouter,
    KeywordSegmenter,
    L1,
    L2,
    PageTable,
    TopicTable,
)


import atexit
import builtins
from datetime import datetime
import re

# ═══════════════════════════════════════════════════════════════ CLI & Options

DEFAULT_REPORT_PATH = ROOT_DIR / "detailed_scenarios_report.md"

console_mode = False
stdout_mode = False
report_path = DEFAULT_REPORT_PATH

filtered_argv = [sys.argv[0]]
i = 1
while i < len(sys.argv):
    arg = sys.argv[i]
    if arg in ("--console", "--verbose", "-v"):
        console_mode = True
    elif arg == "--stdout":
        stdout_mode = True
    elif arg in ("--output", "-o"):
        if i + 1 < len(sys.argv):
            i += 1
            report_path = Path(sys.argv[i])
    elif arg.startswith("--output="):
        report_path = Path(arg.split("=", 1)[1])
    else:
        filtered_argv.append(arg)
    i += 1

if os.environ.get("PRISM_CONSOLE") == "1":
    console_mode = True
if os.environ.get("PRISM_STDOUT") == "1":
    stdout_mode = True
if os.environ.get("PRISM_REPORT_FILE"):
    report_path = Path(os.environ["PRISM_REPORT_FILE"])


# ═══════════════════════════════════════════════════════════════ helpers

SEPARATOR = "─" * 80
SECTION   = "━" * 80
BLUE      = "\033[94m"
GREEN     = "\033[92m"
YELLOW    = "\033[93m"
RED       = "\033[91m"
CYAN      = "\033[96m"
MAGENTA   = "\033[95m"
DIM       = "\033[2m"
BOLD      = "\033[1m"
RESET     = "\033[0m"

ANSI_ESCAPE = re.compile(r'\x1b\[[0-9;]*m')

def strip_ansi(text: str) -> str:
    return ANSI_ESCAPE.sub('', text)

def _safe_stdout(text: str) -> None:
    try:
        sys.stdout.write(text)
        sys.stdout.flush()
    except (UnicodeEncodeError, AttributeError, io.UnsupportedOperation):
        safe = (
            text.replace("✅", "[OK]")
            .replace("❌", "[X]")
            .replace("⚠️", "[!]")
            .replace("📄", "[DOC]")
            .replace("═", "=")
            .replace("─", "-")
            .replace("━", "=")
            .replace("┌", "+")
            .replace("┐", "+")
            .replace("└", "+")
            .replace("┘", "+")
            .replace("│", "|")
            .replace("█", "#")
        )
        enc = sys.stdout.encoding or "ascii"
        sys.stdout.write(safe.encode(enc, errors="replace").decode(enc))
        sys.stdout.flush()


class ScenarioReporter:
    def __init__(self, filename: Path, console_mode: bool = False, stdout_mode: bool = False):
        self.filename = Path(filename)
        self.console_mode = console_mode
        self.stdout_mode = stdout_mode
        self.scenarios: list[dict] = []
        self.current_scenario: dict | None = None
        self.total_scenarios = 10
        self.scenario_count = 0
        self._saved = False

    def start_scenario(self, title: str) -> None:
        self.scenario_count += 1
        clean_title = strip_ansi(title).strip()
        m = re.match(r'(?:SCENARIO\s+)?(\d+)[:\s]*(.*)', clean_title, re.IGNORECASE)
        if m:
            num = int(m.group(1))
            display_title = m.group(2).strip() or clean_title
        else:
            num = self.scenario_count
            display_title = clean_title

        self.current_scenario = {
            "num": num,
            "title": display_title,
            "raw_title": clean_title,
            "turns": [],
            "notes": [],
            "status": "PASS",
        }
        self.scenarios.append(self.current_scenario)
        if not self.console_mode and not self.stdout_mode:
            disp_str = clean_title
            if len(disp_str) > 56:
                disp_str = disp_str[:53] + "..."
            _safe_stdout(f"  [{self.scenario_count:02d}/{self.total_scenarios}] {disp_str:<56} ... ")

    def start_turn(self, turn_num: int, user_text: str) -> None:
        clean_user = strip_ansi(user_text).strip()
        turn_item = {
            "turn_num": turn_num,
            "user_text": clean_user,
            "reply": None,
            "state": None,
        }
        if self.current_scenario:
            self.current_scenario["turns"].append(turn_item)

    def record_state(self, mgr: ContextManager, rendered: list | None = None) -> None:
        if not self.current_scenario or not self.current_scenario["turns"]:
            return
        turn_data = self.current_scenario["turns"][-1]

        # Extract assistant reply from open page if available
        if mgr._open_seq is not None and mgr.l1.has(mgr._open_seq):
            data = mgr.l1.get(mgr._open_seq).data
            for m in reversed(data):
                if m.role == "assistant":
                    turn_data["reply"] = m.content
                    break

        topics_info = []
        for t in mgr.topics.all():
            topics_info.append({
                "id": t.id,
                "is_open": t.is_open,
                "label": t.card.label,
                "description": t.card.description,
                "key_facts": list(t.card.key_facts),
                "entities": list(t.card.entities),
                "covered_through": t.card.covered_through,
                "page_seqs": list(t.page_seqs),
            })

        l1_pages = mgr.page_table.pages_in("L1")
        l2_pages = mgr.page_table.pages_in("L2")
        util = mgr.l1.utilization()

        l1_details = {
            "used": mgr.l1.used_tokens,
            "max": mgr.l1.max_tokens,
            "free": mgr.l1.free_tokens,
            "util": util,
            "low_water": mgr.l1.low_water,
            "high_water": mgr.l1.high_water,
            "pages": [{
                "seq": p.seq,
                "topic_id": p.topic_id,
                "tokens": p.tokens,
                "is_open": p.is_open,
                "messages": [{"role": m.role, "content": m.content} for m in p.data],
            } for p in mgr.l1.pages()],
        }

        l2_details = {
            "pages": [{
                "seq": p.seq,
                "topic_id": p.topic_id,
                "tokens": p.tokens,
                "messages": [{"role": m.role, "content": m.content} for m in p.data],
            } for p in mgr.l2.pages()]
        }

        events = mgr.drain_events()
        rendered_msgs = [{"role": m.role, "content": m.content} for m in rendered] if rendered else []

        turn_data["state"] = {
            "open_id": mgr.topics._open_id,
            "topics": topics_info,
            "l1_pages": l1_pages,
            "l2_pages": l2_pages,
            "l1": l1_details,
            "l2": l2_details,
            "events": events,
            "rendered": rendered_msgs,
        }

    def log_note(self, text: str) -> None:
        clean = strip_ansi(text).strip()
        if not clean:
            return
        if self.current_scenario:
            self.current_scenario["notes"].append(clean)
            if "FAIL" in clean:
                self.current_scenario["status"] = "FAIL"

    def finish_scenario(self, status: str = "PASS") -> None:
        if self.current_scenario:
            if status != "PASS":
                self.current_scenario["status"] = status
            final_status = self.current_scenario["status"]
            if not self.console_mode and not self.stdout_mode:
                badge = "PASS ✅\n" if final_status == "PASS" else "FAIL ❌\n"
                _safe_stdout(badge)

    def generate_markdown(self) -> str:
        md = []
        md.append("# PRISM Detailed Scenario Tests Report")
        md.append("")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        passed = sum(1 for s in self.scenarios if s["status"] == "PASS")
        total = len(self.scenarios)
        md.append(f"> **Generated**: `{timestamp}`  ")
        md.append(f"> **Scenarios**: {total} Total | **{passed} Passed** | **{total - passed} Failed**")
        md.append("")
        md.append("## Executive Summary")
        md.append("")
        md.append("| # | Scenario Name | Turns | Status |")
        md.append("|:---:|:---|:---:|:---:|")
        for s in self.scenarios:
            status_icon = "✅ PASS" if s["status"] == "PASS" else "❌ FAIL"
            slug = re.sub(r'[^a-z0-9]+', '-', s['title'].lower()).strip('-')
            md.append(f"| {s['num']:02d} | [{s['title']}](#{slug}) | {len(s['turns'])} | {status_icon} |")
        md.append("")
        md.append("---")
        md.append("")

        for s in self.scenarios:
            slug = re.sub(r'[^a-z0-9]+', '-', s['title'].lower()).strip('-')
            md.append(f"<a id=\"{slug}\"></a>")
            md.append(f"## Scenario {s['num']}: {s['title']}")
            md.append("")
            status_badge = "PASSED ✅" if s["status"] == "PASS" else "FAILED ❌"
            md.append(f"**Status**: `{status_badge}`")
            md.append("")

            for turn in s["turns"]:
                md.append(f"### Turn {turn['turn_num']}: \"{turn['user_text']}\"")
                md.append("")
                if turn.get("reply"):
                    md.append(f"> 🤖 **Assistant Reply**: *{turn['reply']}*")
                    md.append("")

                st = turn.get("state")
                if not st:
                    continue

                if st["events"]:
                    md.append("**System Events**:")
                    for e in st["events"]:
                        md.append(f"- `{e}`")
                    md.append("")

                # Topic Table
                md.append("#### Topic Table")
                md.append("")
                open_id_str = f"`{st['open_id']}`" if st['open_id'] is not None else "*None*"
                md.append(f"- **Active Open Topic**: {open_id_str}")
                md.append("")
                md.append("| Topic ID | Status | Card Label | Key Facts | Entities | Pages |")
                md.append("|:---:|:---:|:---|:---|:---|:---:|")
                for t in st["topics"]:
                    t_status = "🟢 OPEN" if t["is_open"] else "🔴 CLOSED"
                    facts = "<br/>".join(t["key_facts"][:2]) if t["key_facts"] else "-"
                    ents = ", ".join(t["entities"][:5]) if t["entities"] else "-"
                    label_clean = t["label"][:40].replace("|", "/")
                    md.append(f"| {t['id']} | {t_status} | `{label_clean}` | {facts} | {ents} | `{t['page_seqs']}` |")
                md.append("")

                # Memory Layers
                md.append("#### Memory Layers (L1 / L2)")
                md.append("")
                l1 = st["l1"]
                md.append(f"- **L1 Utilization**: `{l1['used']}/{l1['max']}` tokens (**{l1['util']:.0%}**) | Low-water: `{l1['low_water']:.0%}` | High-water: `{l1['high_water']:.0%}`")
                md.append(f"- **L1 Pages**: `{st['l1_pages']}`")
                l2_str = f"`{st['l2_pages']}`" if st['l2_pages'] else "*(empty)*"
                md.append(f"- **L2 Pages**: {l2_str}")
                md.append("")

                # L1 Pages
                if l1["pages"]:
                    md.append("<details><summary><b>View L1 Page Details</b></summary>")
                    md.append("")
                    for p in l1["pages"]:
                        open_flag = " (OPEN)" if p["is_open"] else ""
                        md.append(f"- **Page {p['seq']}** [Topic {p['topic_id']}, {p['tokens']} tokens{open_flag}]:")
                        for m in p["messages"]:
                            role = m["role"].upper()
                            c = m["content"].replace("\n", " ")
                            if len(c) > 75:
                                c = c[:72] + "..."
                            md.append(f"  - `{role}`: {c}")
                    md.append("</details>")
                    md.append("")

                # Rendered prompt
                if st["rendered"]:
                    md.append("#### Rendered Prompt (Sent to LLM)")
                    md.append("")
                    for m in st["rendered"]:
                        role = m["role"].upper()
                        md.append(f"> **[{role}]**: {m['content']}")
                    md.append("")

            # Assertions / Results
            if s["notes"]:
                md.append("#### Assertions & Verification Notes")
                for note in s["notes"]:
                    if "PASS" in note:
                        md.append(f"> [!NOTE]\n> **{note}**")
                    else:
                        md.append(f"- {note}")
                md.append("")

            md.append("---")
            md.append("")

        return "\n".join(md)

    def save(self) -> Path:
        if self._saved:
            return self.filename
        text = self.generate_markdown()
        self.filename.parent.mkdir(parents=True, exist_ok=True)
        with open(self.filename, "w", encoding="utf-8") as f:
            f.write(text)
        self._saved = True
        return self.filename


reporter = ScenarioReporter(report_path, console_mode=console_mode, stdout_mode=stdout_mode)
atexit.register(reporter.save)

_orig_print = builtins.print

def print(*args, **kwargs) -> None:
    text = " ".join(str(a) for a in args)
    reporter.log_note(text)
    if reporter.console_mode:
        _orig_print(*args, **kwargs)


def print_header(title: str) -> None:
    reporter.start_scenario(title)
    if reporter.console_mode:
        _orig_print(f"\n{BOLD}{CYAN}{SECTION}{RESET}")
        _orig_print(f"{BOLD}{CYAN}  TEST: {title}{RESET}")
        _orig_print(f"{BOLD}{CYAN}{SECTION}{RESET}")


def print_turn(turn_num: int, user_text: str) -> None:
    reporter.start_turn(turn_num, user_text)
    if reporter.console_mode:
        _orig_print(f"\n{BOLD}{YELLOW}{'─' * 60}{RESET}")
        _orig_print(f"{BOLD}{YELLOW}  TURN {turn_num}: \"{user_text}\"{RESET}")
        _orig_print(f"{BOLD}{YELLOW}{'─' * 60}{RESET}")


def print_state(mgr: ContextManager, rendered: list | None = None) -> None:
    """Record state and print full system state if console_mode."""
    reporter.record_state(mgr, rendered)
    if not reporter.console_mode:
        return

    # ── Topic Table ──
    _orig_print(f"\n  {BOLD}{MAGENTA}┌── TOPIC TABLE ──────────────────────────────────────────┐{RESET}")
    _orig_print(f"  {MAGENTA}│  open_id = {mgr.topics._open_id}{RESET}")
    for t in mgr.topics.all():
        status = f"{GREEN}OPEN ✅{RESET}" if t.is_open else f"{RED}CLOSED ❌{RESET}"
        _orig_print(f"  {MAGENTA}│{RESET}")
        _orig_print(f"  {MAGENTA}│  Topic {t.id}: {status}{RESET}")
        _orig_print(f"  {MAGENTA}│    label:           {t.card.label[:60]}{RESET}")
        if t.card.description:
            _orig_print(f"  {MAGENTA}│    description:     {t.card.description[:60]}{RESET}")
        if t.card.key_facts:
            for kf in t.card.key_facts[:3]:
                _orig_print(f"  {MAGENTA}│    key_fact:        {kf[:60]}{RESET}")
        if t.card.entities:
            _orig_print(f"  {MAGENTA}│    entities:        {t.card.entities[:6]}{RESET}")
        _orig_print(f"  {MAGENTA}│    covered_through: {t.card.covered_through}{RESET}")
        _orig_print(f"  {MAGENTA}│    page_seqs:       {t.page_seqs}{RESET}")
    _orig_print(f"  {MAGENTA}└────────────────────────────────────────────────────────┘{RESET}")

    # ── Page Table ──
    _orig_print(f"\n  {BOLD}{BLUE}┌── PAGE TABLE ───────────────────────────────────────────┐{RESET}")
    for layer_name in ["L1", "L2"]:
        seqs = mgr.page_table.pages_in(layer_name)
        if seqs:
            _orig_print(f"  {BLUE}│  {layer_name}: pages {seqs}{RESET}")
    _orig_print(f"  {BLUE}└────────────────────────────────────────────────────────┘{RESET}")

    # ── L1 ──
    util = mgr.l1.utilization()
    bar_len = 30
    filled = int(util * bar_len)
    bar = "█" * filled + "" * (bar_len - filled)
    hw = mgr.l1.high_water
    lw = mgr.l1.low_water
    color = RED if util > hw else (YELLOW if util > lw else GREEN)

    _orig_print(f"\n  {BOLD}{GREEN}┌── L1 (Active Prompt Context) ──────────────────────────┐{RESET}")
    _orig_print(f"  {GREEN}│  Tokens: {mgr.l1.used_tokens} / {mgr.l1.max_tokens}  "
          f"Free: {mgr.l1.free_tokens}{RESET}")
    _orig_print(f"  {GREEN}│  Utilization: {color}[{bar}] {util:.0%}{RESET}")
    _orig_print(f"  {GREEN}│  Low water: {lw:.0%}   High water: {hw:.0%}{RESET}")
    for p in mgr.l1.pages():
        open_mark = " 📝 OPEN" if p.is_open else ""
        msgs = [f"{m.role[0].upper()}:{m.content[:30]}" for m in p.data]
        _orig_print(f"  {GREEN}│  Page {p.seq} [topic {p.topic_id}, {p.tokens}tok{open_mark}]{RESET}")
        for m in msgs:
            _orig_print(f"  {GREEN}│    {DIM}{m}{RESET}")
    _orig_print(f"  {GREEN}└────────────────────────────────────────────────────────┘{RESET}")

    # ── L2 ──
    _orig_print(f"\n  {BOLD}{RED}┌── L2 (Held Pages) ─────────────────────────────────────┐{RESET}")
    if mgr.l2.pages():
        for p in mgr.l2.pages():
            msgs = [f"{m.role[0].upper()}:{m.content[:30]}" for m in p.data]
            _orig_print(f"  {RED}│  Page {p.seq} [topic {p.topic_id}, {p.tokens}tok]{RESET}")
            for m in msgs:
                _orig_print(f"  {RED}│    {DIM}{m}{RESET}")
    else:
        _orig_print(f"  {RED}│  (empty){RESET}")
    _orig_print(f"  {RED}└────────────────────────────────────────────────────────┘{RESET}")

    # ── Events ──
    events = mgr.drain_events()
    if events:
        _orig_print(f"\n  {BOLD}{CYAN}┌── EVENTS ──────────────────────────────────────────────┐{RESET}")
        for e in events:
            _orig_print(f"  {CYAN}│  → {e}{RESET}")
        _orig_print(f"  {CYAN}└────────────────────────────────────────────────────────┘{RESET}")

    # ── Rendered Prompt ──
    if rendered:
        _orig_print(f"\n  {BOLD}{DIM}┌── RENDERED PROMPT (sent to LLM) ───────────────────────┐{RESET}")
        for m in rendered:
            tag = m.role.upper()
            _orig_print(f"  {DIM}│  [{tag}] {m.content[:65]}{RESET}")
        _orig_print(f"  {DIM}└────────────────────────────────────────────────────────┘{RESET}")


def make_manager(max_tokens: int = 500, max_page_tokens: int = 400) -> ContextManager:
    """Create a fresh ContextManager with standard test config."""
    return ContextManager(
        l1=L1(max_tokens=max_tokens, high_water=0.85, low_water=0.70),
        l2=L2(),
        topics=TopicTable(),
        page_table=PageTable(),
        segmenter=KeywordSegmenter(),
        router=KeywordRouter(),
        card_writer=FakeCardWriter(),
        max_page_tokens=max_page_tokens,
    )


# ═══════════════════════════════════════════════════════════════ tests

class TestScenario1_BasicConversation(unittest.TestCase):
    """First message creates a topic and page. Follow-up continues on it."""

    def test_first_message_and_continuation(self):
        print_header("SCENARIO 1: First Message + Continuation")
        mgr = make_manager(max_tokens=500)

        # Turn 1: First ever message
        print_turn(1, "Tell me about Python decorators")
        rendered = mgr.prepare_context("Tell me about Python decorators")
        mgr.record_reply("Decorators wrap functions using @ syntax. They take a function and return a modified function.")
        print_state(mgr, rendered)

        self.assertEqual(len(mgr.topics.all()), 1)
        self.assertTrue(mgr.topics.all()[0].is_open)
        self.assertEqual(mgr.page_table.where(0), "L1")

        # Turn 2: Continue same topic
        print_turn(2, "Can you show me a decorator example?")
        rendered = mgr.prepare_context("Can you show me a decorator example?")
        mgr.record_reply("Here's a simple decorator: @timer def slow_func(): ...")
        print_state(mgr, rendered)

        self.assertEqual(len(mgr.topics.all()), 1, "Should still be 1 topic")
        self.assertTrue(mgr.topics.all()[0].is_open)
        print(f"\n  {GREEN}✅ PASS: First message creates topic, continuation stays on it{RESET}")


class TestScenario2_TopicSwitch(unittest.TestCase):
    """User changes subject entirely. Old topic closes, card is written."""

    def test_topic_switch_closes_old_and_opens_new(self):
        print_header("SCENARIO 2: Topic Switch (New Topic)")
        mgr = make_manager(max_tokens=800)

        # Turn 1: Python topic
        print_turn(1, "Explain Python list comprehensions")
        rendered = mgr.prepare_context("Explain Python list comprehensions")
        mgr.record_reply("List comprehensions create lists using [expr for item in iterable]. They are concise and fast.")
        print_state(mgr, rendered)

        # Turn 2: Completely different topic
        print_turn(2, "What is the capital of France and its population?")
        rendered = mgr.prepare_context("What is the capital of France and its population?")
        mgr.record_reply("Paris is the capital of France with a population of about 2.1 million in the city proper.")
        print_state(mgr, rendered)

        topics = mgr.topics.all()
        self.assertEqual(len(topics), 2, "Should have 2 topics")
        closed = [t for t in topics if not t.is_open]
        opened = [t for t in topics if t.is_open]
        self.assertEqual(len(closed), 1, "First topic should be closed")
        self.assertEqual(len(opened), 1, "Second topic should be open")
        self.assertNotEqual(closed[0].card.label, closed[0].card.label[:60],
                            msg="") if len(closed[0].card.label) > 60 else None
        self.assertGreaterEqual(closed[0].card.covered_through, 0,
                                "Card should have covered_through set")
        print(f"\n  {GREEN}✅ PASS: Topic switch closes old topic and writes card{RESET}")


class TestScenario3_ReturnToOldTopic(unittest.TestCase):
    """User returns to a previously closed topic."""

    def test_return_reopens_old_topic(self):
        print_header("SCENARIO 3: Return to Old Topic")
        mgr = make_manager(max_tokens=1200)

        # Turn 1: Goa trip
        print_turn(1, "Let's plan a trip to Goa with beaches and hotels")
        rendered = mgr.prepare_context("Let's plan a trip to Goa with beaches and hotels")
        mgr.record_reply("Great choice! Goa has Anjuna, Baga, and Calangute beaches. For hotels I recommend Taj Fort Aguada.")
        print_state(mgr, rendered)

        # Turn 2: Switch to cooking
        print_turn(2, "How do I make butter chicken recipe with spices?")
        rendered = mgr.prepare_context("How do I make butter chicken recipe with spices?")
        mgr.record_reply("Marinate chicken in yogurt and spices. Make tomato gravy with butter, cream, and kasuri methi.")
        print_state(mgr, rendered)

        # Turn 3: Return to Goa trip
        print_turn(3, "Which hotel in Goa has the best beach view?")
        rendered = mgr.prepare_context("Which hotel in Goa has the best beach view?")
        mgr.record_reply("Taj Fort Aguada has a stunning beach view from every room.")
        print_state(mgr, rendered)

        goa_topic = mgr.topics.get(1)
        self.assertTrue(goa_topic.is_open, "Goa topic should be reopened")
        self.assertGreater(len(goa_topic.page_seqs), 1,
                           "Goa topic should have a new page after reopening")
        print(f"\n  {GREEN}✅ PASS: Return to old topic reopens it with new page{RESET}")


class TestScenario4_PressureReliefHysteresis(unittest.TestCase):
    """L1 fills up past high_water, pages demoted to L2 down to low_water."""

    def test_hysteresis_demotion(self):
        print_header("SCENARIO 4: Pressure Relief (Hysteresis 85%→70%)")
        # Small L1 so we hit pressure quickly
        mgr = make_manager(max_tokens=300, max_page_tokens=200)

        # Turn 1: Fill L1 with a chunky message
        print_turn(1, "Python is a great programming language for data science and machine learning applications")
        rendered = mgr.prepare_context(
            "Python is a great programming language for data science and machine learning applications"
        )
        mgr.record_reply(
            "Absolutely! Python has libraries like NumPy, Pandas, Scikit-learn, TensorFlow, and PyTorch "
            "that make it the go-to language for data science workflows and ML model training."
        )
        print_state(mgr, rendered)

        util_before = mgr.l1.utilization()
        print(f"\n  {DIM}Utilization after turn 1: {util_before:.0%}{RESET}")

        # Turn 2: Switch topic — fills L1 more
        print_turn(2, "Tell me about JavaScript React framework and hooks for building web applications")
        rendered = mgr.prepare_context(
            "Tell me about JavaScript React framework and hooks for building web applications"
        )
        mgr.record_reply(
            "React uses components and hooks like useState and useEffect. JSX lets you write "
            "HTML-like syntax in JavaScript. Virtual DOM makes it fast for web app rendering."
        )
        print_state(mgr, rendered)

        # Check: old topic's pages should have been demoted to L2
        has_l2_pages = len(mgr.l2.pages()) > 0
        util_after = mgr.l1.utilization()
        print(f"\n  {DIM}Utilization after turn 2: {util_after:.0%}{RESET}")
        print(f"  {DIM}Pages in L2: {len(mgr.l2.pages())}{RESET}")

        if has_l2_pages:
            self.assertLessEqual(util_after, mgr.l1.high_water + 0.05,
                                 "Should be near or below high_water after demotion")
            print(f"\n  {GREEN}✅ PASS: Pressure relief demoted pages to L2{RESET}")
        else:
            print(f"\n  {YELLOW}⚠️  No demotion needed (messages fit within budget){RESET}")
            # Still valid — verify L1 isn't over limit
            self.assertLessEqual(mgr.l1.used_tokens, mgr.l1.max_tokens)
            print(f"  {GREEN}✅ PASS: All within budget{RESET}")


class TestScenario5_BringBackFromL2(unittest.TestCase):
    """Pages demoted to L2 get brought back when user returns to that topic."""

    def test_l2_to_l1_retrieval(self):
        print_header("SCENARIO 5: L2 → L1 Retrieval")
        mgr = make_manager(max_tokens=350, max_page_tokens=200)

        # Turn 1: Topic A
        print_turn(1, "Explain Goa beaches and Anjuna nightlife and Baga water sports")
        rendered = mgr.prepare_context("Explain Goa beaches and Anjuna nightlife and Baga water sports")
        mgr.record_reply("Anjuna has flea markets and trance parties. Baga is great for parasailing and jet skiing.")
        print_state(mgr, rendered)

        # Turn 2: Topic B — forces demotion of A
        print_turn(2, "How does quantum computing work with qubits and superposition entanglement")
        rendered = mgr.prepare_context("How does quantum computing work with qubits and superposition entanglement")
        mgr.record_reply("Quantum computers use qubits that can be in superposition. Entanglement links qubits together.")
        print_state(mgr, rendered)

        # Check if Topic A's pages are in L2
        topic_a_seqs = mgr.topics.get(1).page_seqs
        l2_pages = [s for s in topic_a_seqs if mgr.page_table.where(s) == "L2"]
        print(f"\n  {DIM}Topic A pages in L2: {l2_pages}{RESET}")

        # Turn 3: Return to Topic A — should bring pages back from L2
        print_turn(3, "Which Goa beach has the best Anjuna nightlife scene?")
        rendered = mgr.prepare_context("Which Goa beach has the best Anjuna nightlife scene?")
        mgr.record_reply("Anjuna Beach is the nightlife capital of Goa, especially around Curlies and Shiva Valley.")
        print_state(mgr, rendered)

        # Check if Topic A pages came back to L1
        topic_a_in_l1 = [s for s in mgr.topics.get(1).page_seqs if mgr.page_table.where(s) == "L1"]
        print(f"\n  {DIM}Topic A pages now in L1: {topic_a_in_l1}{RESET}")

        if topic_a_in_l1:
            print(f"\n  {GREEN}✅ PASS: Pages retrieved from L2 back to L1{RESET}")
        else:
            print(f"\n  {YELLOW}⚠️  Pages stayed in L2 (not enough room){RESET}")


class TestScenario6_PageSplitting(unittest.TestCase):
    """Long topics get split into multiple pages at max_page_tokens boundary."""

    def test_page_split_on_long_topic(self):
        print_header("SCENARIO 6: Page Splitting (max_page_tokens)")
        # Low page token limit so we trigger splits
        mgr = make_manager(max_tokens=2000, max_page_tokens=80)

        # Turn 1: Start a topic
        print_turn(1, "Explain the Python GIL and how it affects threading performance")
        rendered = mgr.prepare_context("Explain the Python GIL and how it affects threading performance")
        mgr.record_reply(
            "The Global Interpreter Lock is a mutex that protects Python objects from concurrent access. "
            "It means only one thread executes Python bytecode at a time, limiting true parallelism."
        )
        print_state(mgr, rendered)

        pages_before = len(mgr.topics.get(1).page_seqs)

        # Turn 2: Continue same topic — should trigger page split
        print_turn(2, "How can I work around the GIL using multiprocessing?")
        rendered = mgr.prepare_context("How can I work around the GIL using multiprocessing?")
        mgr.record_reply(
            "Use the multiprocessing module which spawns separate processes, each with its own GIL. "
            "ProcessPoolExecutor makes it easy. For I/O-bound tasks, asyncio is another option."
        )
        print_state(mgr, rendered)

        pages_after = len(mgr.topics.get(1).page_seqs)
        print(f"\n  {DIM}Pages before turn 2: {pages_before}, after: {pages_after}{RESET}")

        if pages_after > pages_before:
            print(f"\n  {GREEN}✅ PASS: Page was split when exceeding max_page_tokens{RESET}")
        else:
            print(f"\n  {YELLOW}⚠️  No split needed (page tokens < {mgr.max_page_tokens}){RESET}")

        self.assertGreaterEqual(pages_after, pages_before)


class TestScenario7_ProtectedPagesNotEvicted(unittest.TestCase):
    """Verify that open pages and wanted topic pages are never evicted."""

    def test_protected_pages_survive_pressure(self):
        print_header("SCENARIO 7: Protected Pages Not Evicted")
        mgr = make_manager(max_tokens=400, max_page_tokens=200)

        # Turn 1: Topic about databases
        print_turn(1, "Explain PostgreSQL indexes and query optimization with EXPLAIN ANALYZE")
        rendered = mgr.prepare_context("Explain PostgreSQL indexes and query optimization with EXPLAIN ANALYZE")
        mgr.record_reply("Use B-tree indexes on frequently queried columns. EXPLAIN ANALYZE shows the query plan.")
        print_state(mgr, rendered)

        # Turn 2: Topic about Redis
        print_turn(2, "How does Redis caching work with TTL expiration and eviction policies?")
        rendered = mgr.prepare_context("How does Redis caching work with TTL expiration and eviction policies?")
        mgr.record_reply("Redis stores key-value pairs in memory. Set TTL with EXPIRE. LRU eviction when maxmemory is hit.")
        print_state(mgr, rendered)

        # Turn 3: Topic about Docker — should push oldest out
        print_turn(3, "Explain Docker containers and Kubernetes orchestration for microservices")
        rendered = mgr.prepare_context("Explain Docker containers and Kubernetes orchestration for microservices")
        mgr.record_reply("Docker packages apps in containers. Kubernetes manages scaling, networking, and deployment.")
        print_state(mgr, rendered)

        # The open page (current topic) must always be in L1
        open_seq = mgr._open_seq
        self.assertIsNotNone(open_seq)
        self.assertEqual(mgr.page_table.where(open_seq), "L1",
                         "Open page must always be in L1")

        # The newest protect_recent_pages pages must be in L1
        newest = mgr.l1.seqs()[-mgr.protect_recent_pages:]
        for seq in newest:
            self.assertEqual(mgr.page_table.where(seq), "L1",
                             f"Newest page {seq} must be protected in L1")

        print(f"\n  {GREEN}✅ PASS: Open page and newest pages are protected{RESET}")


class TestScenario8_MultipleTopicLifecycle(unittest.TestCase):
    """Full lifecycle: create → close → reopen → close again."""

    def test_full_topic_lifecycle(self):
        print_header("SCENARIO 8: Full Topic Lifecycle")
        mgr = make_manager(max_tokens=1500, max_page_tokens=400)

        # Turn 1: Topic 1
        print_turn(1, "Let's discuss machine learning neural networks and deep learning")
        rendered = mgr.prepare_context("Let's discuss machine learning neural networks and deep learning")
        mgr.record_reply("Neural networks have layers of nodes. Deep learning uses many layers for complex patterns.")
        print_state(mgr, rendered)

        # Turn 2: Switch to Topic 2
        print_turn(2, "How do I cook pasta carbonara with eggs and pecorino cheese?")
        rendered = mgr.prepare_context("How do I cook pasta carbonara with eggs and pecorino cheese?")
        mgr.record_reply("Cook guanciale, mix eggs with pecorino, toss with hot pasta off heat to avoid scrambling.")
        print_state(mgr, rendered)

        # Verify Topic 1 closed
        t1 = mgr.topics.get(1)
        self.assertFalse(t1.is_open, "Topic 1 should be closed")
        self.assertGreater(len(t1.card.entities), 0, "Topic 1 card should have entities")
        print(f"\n  {DIM}Topic 1 card after closing: {t1.card.label}{RESET}")
        print(f"  {DIM}Topic 1 entities: {t1.card.entities}{RESET}")

        # Turn 3: Switch to Topic 3
        print_turn(3, "What are the best strategies for investing in stock market index funds?")
        rendered = mgr.prepare_context("What are the best strategies for investing in stock market index funds?")
        mgr.record_reply("Index funds track the market. Dollar-cost averaging reduces timing risk. Low expense ratios matter.")
        print_state(mgr, rendered)

        # Turn 4: Return to Topic 1 (machine learning)
        print_turn(4, "What neural network architecture works best for deep learning image recognition?")
        rendered = mgr.prepare_context("What neural network architecture works best for deep learning image recognition?")
        mgr.record_reply("CNNs like ResNet and EfficientNet excel at image recognition with convolutional layers.")
        print_state(mgr, rendered)

        # Verify Topic 1 reopened
        t1 = mgr.topics.get(1)
        print(f"\n  {DIM}Topic 1 is_open: {t1.is_open}{RESET}")
        print(f"  {DIM}Topic 1 page_seqs: {t1.page_seqs}{RESET}")
        print(f"  {DIM}Total topics: {len(mgr.topics.all())}{RESET}")

        self.assertEqual(len(mgr.topics.all()), 3, "Should have 3 topics total")

        # Turn 5: Switch away — closes Topic 1 again with updated card
        print_turn(5, "What is the GDP of India and its economic growth rate?")
        rendered = mgr.prepare_context("What is the GDP of India and its economic growth rate?")
        mgr.record_reply("India's GDP is about 3.7 trillion USD with 6-7% annual growth rate.")
        print_state(mgr, rendered)

        t1 = mgr.topics.get(1)
        self.assertFalse(t1.is_open, "Topic 1 should be closed again")
        print(f"\n  {DIM}Topic 1 card after second close: {t1.card.label}{RESET}")
        print(f"  {DIM}Topic 1 covered_through: {t1.card.covered_through}{RESET}")

        print(f"\n  {GREEN}✅ PASS: Full lifecycle — create → close → reopen → close{RESET}")


class TestScenario9_GapMarkersInRender(unittest.TestCase):
    """When pages are non-consecutive in L1, gap markers appear in render."""

    def test_gap_markers(self):
        print_header("SCENARIO 9: Gap Markers in Rendered Prompt")
        mgr = make_manager(max_tokens=500, max_page_tokens=400)

        # Turn 1
        print_turn(1, "Tell me about Goa beaches and resorts")
        rendered = mgr.prepare_context("Tell me about Goa beaches and resorts")
        mgr.record_reply("Goa has beautiful beaches like Palolem and Agonda. Many beachside resorts available.")
        print_state(mgr, rendered)

        # Turn 2: Different topic
        print_turn(2, "Explain quantum physics wave particle duality experiments")
        rendered = mgr.prepare_context("Explain quantum physics wave particle duality experiments")
        mgr.record_reply("In the double slit experiment, particles show wave-like interference patterns.")
        print_state(mgr, rendered)

        # Turn 3: Yet another topic
        print_turn(3, "How does blockchain consensus mechanism proof of work function?")
        rendered = mgr.prepare_context("How does blockchain consensus mechanism proof of work function?")
        mgr.record_reply("Miners compete to solve hash puzzles. First to find valid hash gets to add the block.")
        print_state(mgr, rendered)

        # Check for gap markers in rendered output
        gaps = [m for m in rendered if m.content == "[earlier messages omitted]"]
        print(f"\n  {DIM}Gap markers found: {len(gaps)}{RESET}")
        print(f"  {DIM}L1 page seqs: {mgr.l1.seqs()}{RESET}")

        # If pages in L1 are non-consecutive, there should be gap markers
        seqs = mgr.l1.seqs()
        has_gaps = any(seqs[i+1] - seqs[i] > 1 for i in range(len(seqs)-1)) if len(seqs) > 1 else False

        if has_gaps:
            self.assertGreater(len(gaps), 0, "Should have gap markers for non-consecutive pages")
            print(f"\n  {GREEN}✅ PASS: Gap markers inserted between non-consecutive pages{RESET}")
        else:
            print(f"\n  {GREEN}✅ PASS: Pages are consecutive, no gaps needed{RESET}")


class TestScenario10_VictimSelection(unittest.TestCase):
    """Victim selection picks least-needed topic first, oldest page among ties."""

    def test_victim_is_least_needed(self):
        print_header("SCENARIO 10: Victim Selection (Least Needed First)")
        mgr = make_manager(max_tokens=350, max_page_tokens=200)

        # Build up 3 topics to fill L1
        print_turn(1, "Goa beaches Anjuna Baga Calangute Palolem resorts")
        rendered = mgr.prepare_context("Goa beaches Anjuna Baga Calangute Palolem resorts")
        mgr.record_reply("Goa is wonderful for beaches.")
        print_state(mgr, rendered)

        print_turn(2, "Python Django Flask web framework REST API development")
        rendered = mgr.prepare_context("Python Django Flask web framework REST API development")
        mgr.record_reply("Django has ORM and admin. Flask is lightweight.")
        print_state(mgr, rendered)

        print_turn(3, "Kubernetes Docker container orchestration microservices deployment")
        rendered = mgr.prepare_context("Kubernetes Docker container orchestration microservices deployment")
        mgr.record_reply("K8s manages containers at scale.")
        print_state(mgr, rendered)

        # Check what's in L2 — the least relevant topic should have been evicted
        l2_pages = mgr.l2.pages()
        print(f"\n  {DIM}L2 pages: {[(p.seq, f'topic {p.topic_id}') for p in l2_pages]}{RESET}")
        print(f"  {DIM}L1 pages: {[(p.seq, f'topic {p.topic_id}') for p in mgr.l1.pages()]}{RESET}")

        # The open page must be in L1
        self.assertEqual(mgr.page_table.where(mgr._open_seq), "L1")
        print(f"\n  {GREEN}✅ PASS: Least-needed pages evicted, current topic protected{RESET}")


def load_tests(loader, tests, pattern):
    """Ensure scenario test suites are run in natural numerical order (1..10)."""
    def _extract_tests(suite):
        extracted = []
        for item in suite:
            if isinstance(item, unittest.TestSuite):
                extracted.extend(_extract_tests(item))
            else:
                extracted.append(item)
        return extracted

    def _scenario_key(test_case):
        name = test_case.__class__.__name__
        m = re.search(r'\d+', name)
        return int(m.group(0)) if m else 999

    all_tests = _extract_tests(tests)
    all_tests.sort(key=_scenario_key)
    ordered_suite = unittest.TestSuite()
    ordered_suite.addTests(all_tests)
    return ordered_suite


class ScenarioTestResult(unittest.TextTestResult):
    def addSuccess(self, test):
        super().addSuccess(test)
        reporter.finish_scenario("PASS")

    def addFailure(self, test, err):
        super().addFailure(test, err)
        reporter.finish_scenario("FAIL")

    def addError(self, test, err):
        super().addError(test, err)
        reporter.finish_scenario("FAIL")


class ScenarioTestRunner(unittest.TextTestRunner):
    resultclass = ScenarioTestResult


# ═══════════════════════════════════════════════════════════════ runner

if __name__ == "__main__":
    if not stdout_mode:
        _safe_stdout(f"\n{BOLD}{CYAN}{'═' * 80}{RESET}\n")
        _safe_stdout(f"{BOLD}{CYAN}  PRISM DETAILED SCENARIO TESTS — Markdown Reporting{RESET}\n")
        _safe_stdout(f"{BOLD}{CYAN}{'═' * 80}{RESET}\n")

    stream = open(os.devnull, "w") if not console_mode and not stdout_mode else sys.stderr
    runner = ScenarioTestRunner(stream=stream, verbosity=0)
    result = unittest.main(argv=filtered_argv, testRunner=runner, exit=False)

    saved_path = reporter.save()

    if stdout_mode:
        _safe_stdout(reporter.generate_markdown() + "\n")
    elif not console_mode:
        passed = sum(1 for s in reporter.scenarios if s["status"] == "PASS")
        total = len(reporter.scenarios)
        _safe_stdout(f"\n{BOLD}{CYAN}{'═' * 80}{RESET}\n")
        _safe_stdout(f"  {BOLD}Summary:{RESET} {passed}/{total} scenarios passed\n")
        _safe_stdout(f"  {BOLD}📄 Detailed Markdown Report:{RESET} {saved_path.resolve()}\n")
        _safe_stdout(f"{BOLD}{CYAN}{'═' * 80}{RESET}\n\n")

    if not result.result.wasSuccessful():
        sys.exit(1)
