---
name: prism-codebase
description: >
  Complete reference for the PRISM context-manager codebase.
  Covers architecture, invariants, the 6-step pipeline, decider protocols,
  and known test-suite warnings (identified 2026-09-20). Activate for any
  task that touches prism/ or tests/fulltest.py.
---

# PRISM Codebase Reference

## What PRISM Does

PRISM is a **hierarchical context-manager for LLMs**, modelled on OS virtual memory.
The problem: LLM context windows are bounded. PRISM solves this by:

- Partitioning conversation history into **PageBlocks** (groups of messages ≤ `max_page_tokens` tokens).
- Grouping pages under **Topics** (semantic threads of conversation).
- Keeping only the "hot" working set in **L1** (what gets sent to the LLM).
- Holding evicted pages verbatim in **L2** (no information loss).
- Using fast **Deciders** to swap pages in/out on every turn.

---

## File Map

```
prism/
  models.py          — Message, PageBlock, TopicCard, Topic, estimate_tokens
  context_manager.py — ContextManager: the 6-step orchestration loop (public: prepare_context, record_reply, open_topic_id, last_scores, move, snapshot, drain_events)
  storage/
    base.py          — StorageProtocol (Protocol)
    l1.py            — L1 (bounded, with high/low-water hysteresis + gap-marked render)
    l2.py            — L2 (unbounded verbatim store)
    page_table.py    — PageTable: seq -> "L1" | "L2" mapping
    topic_table.py   — TopicTable: single-open-topic lifecycle manager
  deciders/
    interfaces.py    — Segmenter, Router, CardWriter (Protocols) + SegmentDecision
    fakes.py         — KeywordSegmenter, KeywordRouter, FakeCardWriter (offline heuristics)
    jev.py           — JevSegmenter, JevRouter (TypeSafe AI API, placeholder JevClient)
    llm.py           — LLMCardWriter (small LLM summarizer, placeholder _call_llm)
tests/
  fulltest.py        — 42 tests, 229 assertions, streaming markdown report
```

---

## 6-Step Pipeline (`prepare_context`)

Every user turn runs these steps in order:

```
1. _apply_segmentation()   — Segmenter: continue / return / new topic
                             If continue AND open page >= max_page_tokens → split page
                             If return or new → _close_current_topic() + write TopicCard
2. _route()                — Router: score closed topics; open topic forced = 1.0
3. _add_to_open_page()     — Append user message to L1 open page (evict if needed)
4. _bring_in_needed()      — For score >= needed_threshold (0.5): L2 → L1, newest page first
5. _relieve_pressure()     — If L1 > high_water (85%): demote until ≤ low_water (70%)
6. l1.render()             — Flatten L1 pages by seq; insert "[earlier messages omitted]" at gaps
```

After the LLM responds: `record_reply()` appends assistant message to the open page.

---

## Critical Invariants (checked after every turn in tests)

1. No page exists in both L1 and L2 simultaneously.
2. L1 ∪ L2 pages == all pages listed by all topics (no orphans, no missing).
3. PageTable.where(seq) == actual layer for every page.
4. L1.used_tokens is accurate and never exceeds L1.max_tokens.
5. Exactly one open page exists; it is the page at `_open_seq`; it is in L1.
6. Exactly one open topic at any time (TopicTable enforces this via RuntimeError).
7. The open page is the newest page of the open topic.
8. Topic.page_seqs is strictly increasing with no duplicates.
9. render() produces len(all page messages) + len(gap markers) messages.
10. No page is moved more than once in one turn (anti-thrash), unless forced.
11. Every page layer-change has a matching move event in drain_events().

### Key Code Rules

- **`ContextManager.move(seq, src, dst)` is the ONLY way pages change layers.** Never
  call `l1.take() / l2.put()` directly — the PageTable will desync.
- Open pages cannot be taken from L1 (`l1.take()` raises ValueError if `page.is_open`).
- `TopicTable.new_topic()` raises RuntimeError if another topic is already open.

---

## Decider Protocols

```python
class Segmenter(Protocol):
    def decide(self, open_topic, closed_topics, recent, new_msg) -> SegmentDecision:
        # action: "continue" | "return" | "new"
        # topic_id: only set for "return"

class Router(Protocol):
    def score(self, topics, recent, new_msg) -> dict[int, float]:
        # topic_id -> probability; >= needed_threshold (0.5) means "bring to L1"

class CardWriter(Protocol):
    def write(self, old_card, pages) -> TopicCard:
        # called synchronously when a topic closes
        # receives only pages newer than old_card.covered_through
```

### Offline fakes (no API needed, used in D1–D3 and E tests)

- `KeywordSegmenter`: word-overlap with stopword removal + rudimentary s-stemming.
  `continue` if overlap ≥ 0.2, `return` if closed topic scores ≥ 0.34 and beats open score, else `new`.
- `KeywordRouter`: `min(1.0, 2 × word_overlap)` per topic card.
- `FakeCardWriter`: top-6 frequent words as entities, user messages as key_facts.

Most tests (U, S, R, B, P, T, C) use `ScriptedSegmenter` / `ScriptedRouter` instead —
deterministic per-turn overrides that keep tests decider-agnostic.

### Jev / LLM (production, API placeholders)

- `JevSegmenter`: one Choice question to TypeSafe AI Jev API.
- `JevRouter`: one Noul question per topic to Jev API.
- `LLMCardWriter`: prompt → Claude Haiku or similar small model → JSON TopicCard.
  **Both `JevClient.ask` and `LLMCardWriter._call_llm` raise `NotImplementedError`** —
  they are stubs that must be wired to real APIs.

---

## Token Estimation

```python
def estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)
```

**This is a placeholder.** The code comment says "Swap in a real tokenizer later."
All tests, all watermark arithmetic, and all page-size decisions are calibrated to this
`len//4` formula. Replacing it will require recalibrating token budgets everywhere.

---

## Test Suite Architecture & Validation Report

The test suite in `tests/fulltest.py` is a 1161-line comprehensive verification system consisting of **42 tests, 229 assertions/checks, and 110 logged conversation turns** (plus 960 fuzz turns in E2 across 8 random seeds). All 42 tests pass with 0 invariant violations.

Running the test suite generates two report artifacts:
- `test_reports/prism_test_report.md`: Human-readable markdown report with topic/page tables, visual token gauges (`[####.....|.....|.....]`), prompts sent to model, and collapsible page contents.
- `test_reports/prism_test_events.jsonl`: Machine-readable streaming event stream recording every turn, action, and invariant check.

### Test Categories Breakdown

| Category | Tests | Checks | Focus & Invariants Tested |
|:---|:---:|:---:|:---|
| **U: Storage & Tables** | U1–U6 | 51 | L1/L2 primitives, token counting, capacity rejection, render order, gap markers, watermark math, PageTable mapping, TopicTable lifecycle. |
| **S: Segmentation** | S1–S6 | 36 | Pipeline step 1: `continue`, `new`, `return`, deferred page splitting at `max_page_tokens`, odd decider handling (missing topic ID, invalid ID). |
| **R: Routing** | R1–R4 | 11 | Pipeline step 2: router sees only closed topics, receives recent window, 0.5 threshold boundary, open topic score forced to 1.0. |
| **B: Bringing Pages** | B1–B4 | 18 | Pipeline step 4: bringing needed pages from L2 to L1, newest pages prioritized, safe skipping when page exceeds free space, deduplication. |
| **P: Demotion Pressure**| P1–P6 | 35 | Pipeline step 5: high-water (85%) triggers demotion down to low-water (70%), recent page protection, victim selection (score ascending, age descending). |
| **T: Turn Handling** | T1–T6 | 19 | Assistant replies & tool results append to open page, survivor pages, reply reserve pre-allocation, oversized message rejection. |
| **C: Card Lifecycle** | C1–C2 | 7 | Incremental card updates (pages newer than `covered_through`), closing topics whose pages reside in L2. |
| **D: Decider Protocols**| D1–D6 | 40 | Unit tests for keyword heuristics (D1–D3), Jev API prompt construction & rules (D4–D5), LLM card writer prompt & JSON parsing (D6). |
| **E: End-to-End & Fuzz**| E1–E2 | 12 | Realistic 6-turn multi-topic dialog with keyword deciders (E1); 8-seed × 120-turn (960 turns total) fuzz testing ensuring all 11 invariants hold (E2). |

---

## Test Suite Warnings & Architectural Quirks

### 🔴 HIGH — Tokenizer Coupling (Architectural Constraint)
All token-budget tests use `tok(n)` which is tied to `len // 4`. If the tokenizer changes, all U/S/R/B/P/T/C test calibrations break. Token values (400, 120, 100, etc.) are all `len // 4` units.
```python
def tok(n, tag=""):
    base = ((tag + " ") if tag else "") + "lorem ipsum dolor sit amet " * (n + 3)
    for length in range(1, len(base) + 1):
        if Message("user", base[:length]).tokens == n:
            return base[:length]
```

### 🔴 HIGH — E1 Heuristic Fragility (Resolved)
`test_E1` asserts specific reply strings appear in prompts, dependent on `KeywordSegmenter` making correct topic-transition decisions.
- **Resolution**: Separated into structural checks (manager-level invariants, e.g. L1 token ceiling) vs heuristic-dependent checks (keyword-decider level). Heuristic checks are explicitly labeled `[heuristic]` in the report, with test comments providing triage instructions to isolate manager defects from keyword-fake threshold variance.

### 🟡 MEDIUM — S6(c) Vague Assertion (Resolved)
Return to nonexistent `topic_id`: previously accepted either `err is not None` OR `open_topic_id is not None`.
- **Resolution**: Tightened to assert `isinstance(err, KeyError)` specifically and verify state is fully untouched (`structure(snap(c.mgr)) == before`), confirming the pre-flight check in `prepare_context` fires before any partial state changes.

### 🟡 MEDIUM — S6(b) Self-Return Semantics Undocumented (Resolved)
Returning to the currently-open topic causes: `_close_current_topic()` (card written) + `reopen()` + new page.
- **Resolution**: Documented architectural design rationale in test comments. When the segmenter returns `("return", open_topic_id)`, it signals a semantic topic transition; opening a fresh page boundary is intentional, even when returning to the same topic.

### 🟡 MEDIUM — R4 Reads Private `_last_scores` (Resolved)
Previously accessed internal attribute: `scores = h.mgr._last_scores`.
- **Resolution**: Added public `@property def last_scores(self) -> dict[int, float]:` on `ContextManager` (returning a defensive copy `dict(self._last_scores)`), and updated `R4` in `fulltest.py` to use `h.mgr.last_scores`.

### 🟡 MEDIUM — Page Split Is Deferred (Architectural Constraint)
A split only triggers at the START of the NEXT turn (when `open_page.tokens >= max_page_tokens` is checked during `_apply_segmentation`). A reply that pushes a page over `max_page_tokens` does NOT immediately split it mid-turn. The page can exceed its nominal size by up to one reply's worth of tokens within a turn.

### 🟢 LOW — FakeCardWriter Exact-String Dedup (Documented Limitation)
`key_facts` deduplication uses `dict.fromkeys()` (exact string equality). Semantically similar facts with varying casing or punctuation are not deduplicated by the fake.

---

## Running the Tests

```powershell
# From project root (PRISM- directory)
python -B tests/fulltest.py                     # run all 42 tests, writes test_reports/
python -B tests/fulltest.py --only P2           # run only tests matching "P2"
python -B tests/fulltest.py --list              # list all test ids and descriptions
python -B tests/fulltest.py --out my_dir        # custom output folder for reports
```

Outputs generated:
- `test_reports/prism_test_report.md` (human-readable markdown)
- `test_reports/prism_test_events.jsonl` (machine-readable event log)
