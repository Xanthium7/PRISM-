# PRISM test report

> Generated `2026-09-20 12:26:24`


---## Summary

**42/42 tests passed** · 229 checks · 110 conversation turns logged

| ID | Test | Turns | Checks | Result |
|:-:|:--|:-:|:-:|:-:|
| U1 | L1 put take append and capacity | 0 | 12 | ✅ PASS |
| U2 | L1 render order and gap markers | 0 | 9 | ✅ PASS |
| U3 | L1 watermarks and validation | 0 | 6 | ✅ PASS |
| U4 | L2 holds pages without a limit | 0 | 8 | ✅ PASS |
| U5 | PageTable maps pages to layers | 0 | 5 | ✅ PASS |
| U6 | TopicTable lifecycle | 0 | 11 | ✅ PASS |
| S1 | first message creates topic and page | 1 | 8 | ✅ PASS |
| S2 | continue keeps the same page | 2 | 3 | ✅ PASS |
| S3 | new topic closes old and writes card | 2 | 8 | ✅ PASS |
| S4 | return reopens old topic with a new page | 3 | 6 | ✅ PASS |
| S5 | page splits at max page tokens between turns | 4 | 6 | ✅ PASS |
| S6 | odd decider output is handled | 6 | 5 | ✅ PASS |
| R1 | router sees only closed topics | 4 | 3 | ✅ PASS |
| R2 | router gets the recent window | 4 | 2 | ✅ PASS |
| R3 | needed threshold boundary | 6 | 4 | ✅ PASS |
| R4 | open topic always scores 1 | 2 | 2 | ✅ PASS |
| B1 | needed page returns from L2 intact | 3 | 7 | ✅ PASS |
| B2 | newest pages first and skip when no room | 4 | 5 | ✅ PASS |
| B3 | page too big to fit is skipped safely | 3 | 4 | ✅ PASS |
| B4 | needed page already in L1 is not moved | 3 | 2 | ✅ PASS |
| P1 | no demotion at or below high water | 5 | 6 | ✅ PASS |
| P2 | demotion continues down to low water and stops | 7 | 9 | ✅ PASS |
| P3 | newest pages are protected | 6 | 8 | ✅ PASS |
| P4 | protect recent pages zero protects only the open page | 6 | 7 | ✅ PASS |
| P5 | victims are chosen by router score then age | 5 | 2 | ✅ PASS |
| P6 | everything protected leaves L1 over high water | 3 | 3 | ✅ PASS |
| T1 | replies and tool results go into the open page | 2 | 3 | ✅ PASS |
| T2 | a needed page survives the reply | 3 | 3 | ✅ PASS |
| T3 | a reply that does not fit is not lost | 3 | 3 | ✅ PASS |
| T4 | reply reserve makes room before the model call | 4 | 4 | ✅ PASS |
| T5 | message larger than L1 is rejected cleanly | 2 | 2 | ✅ PASS |
| T6 | a message that cannot fit leaves state untouched | 4 | 4 | ✅ PASS |
| C1 | second close updates the card with only new pages | 4 | 5 | ✅ PASS |
| C2 | closing a topic with pages in L2 still works | 3 | 2 | ✅ PASS |
| D1 | KeywordSegmenter rules | 0 | 5 | ✅ PASS |
| D2 | KeywordRouter scores | 0 | 4 | ✅ PASS |
| D3 | FakeCardWriter edge cases | 0 | 5 | ✅ PASS |
| D4 | JevSegmenter decision rules | 0 | 11 | ✅ PASS |
| D5 | JevRouter builds one question per topic | 0 | 7 | ✅ PASS |
| D6 | LLMCardWriter prompt and parsing | 0 | 8 | ✅ PASS |
| E1 | realistic conversation with the keyword deciders | 6 | 4 | ✅ PASS |
| E2 | random conversations never break the invariants | 0 | 8 | ✅ PASS |



## U1 — L1 put take append and capacity

> L1 stores pages, counts tokens, and refuses overflow, duplicates and removal of the open page.

- ✅ an empty open page can be put
- ✅ used / free / utilization after a 10-token message — got `(10, 90, 0.1)`, expected `(10, 90, 0.1)`
- ✅ putting a duplicate seq is refused (raised ValueError)
- ✅ a page bigger than free space is refused (raised L1FullError)
- ✅ a refused put leaves L1 unchanged — got `[0]`, expected `[0]`
- ✅ a message bigger than free space is refused (raised L1FullError)
- ✅ a refused append leaves the page unchanged — got `10`, expected `10`
- ✅ the open page cannot be taken out (raised ValueError)
- ✅ the open page is still in L1 after the refused take
- ✅ a closed page can be taken and tokens are released
- ✅ get on a missing page raises KeyError (raised KeyError)
- ✅ seqs() and pages() are always sorted by seq — got `([2, 5, 9], [2, 5, 9])`, expected `([2, 5, 9], [2, 5, 9])`

**Result: ✅ PASS**  (12 checks, 0 failed, 0 turns, 0.00s)

---

## U2 — L1 render order and gap markers

> render() flattens pages in seq order and inserts exactly one gap marker per discontinuity.

- ✅ consecutive pages from 0: no marker (pages [0, 1, 2]) — got `['page0', 'page1', 'page2']`, expected `['page0', 'page1', 'page2']`
- ✅ first page is not seq 0: marker at the start (pages [1, 2]) — got `['[earlier messages omitted]', 'page1', 'page2']`, expected `['[earlier messages omitted]', 'page1', 'page2']`
- ✅ one missing page in the middle: one marker between (pages [0, 2]) — got `['page0', '[earlier messages omitted]', 'page2']`, expected `['page0', '[earlier messages omitted]', 'page2']`
- ✅ two gaps: two markers (pages [0, 2, 4]) — got `['page0', '[earlier messages omitted]', 'page2', '[earlier messages omitted]', 'page4']`, expected `['page0', '[earlier messages omitted]', 'page2', '[earlier messages omitted]', 'page4']`
- ✅ a single page that is not seq 0: marker first (pages [3]) — got `['[earlier messages omitted]', 'page3']`, expected `['[earlier messages omitted]', 'page3']`
- ✅ gap followed by consecutive pages: one marker only (pages [0, 3, 4]) — got `['page0', '[earlier messages omitted]', 'page3', 'page4']`, expected `['page0', '[earlier messages omitted]', 'page3', 'page4']`
- ✅ mark_gaps=False inserts nothing — got `['page0', 'page2']`, expected `['page0', 'page2']`
- ✅ the marker has role 'system' — got `'system'`, expected `'system'`
- ✅ an empty L1 renders an empty prompt — got `[]`, expected `[]`

**Result: ✅ PASS**  (9 checks, 0 failed, 0 turns, 0.00s)

---

## U3 — L1 watermarks and validation

> over_high_water / above_low_water are strict '>' comparisons and bad settings are rejected.

- ✅ over_high_water: 85% is not over, 86% is — got `(False, True)`, expected `(False, True)`
- ✅ above_low_water: 70% is not above, 71% is — got `(False, True)`, expected `(False, True)`
- ✅ low_water == high_water is rejected (raised ValueError)
- ✅ high_water above 1 is rejected (raised ValueError)
- ✅ low_water of 0 is rejected (raised ValueError)
- ✅ max_tokens=0 gives utilization 0.0 instead of dividing by zero — got `0.0`, expected `0.0`

**Result: ✅ PASS**  (6 checks, 0 failed, 0 turns, 0.00s)

---

## U4 — L2 holds pages without a limit

> L2 is a plain seq-keyed store with the same put/take/get/has/pages interface as L1.

- ✅ pages() is sorted and len() counts pages — got `([3, 5, 7], 3)`, expected `([3, 5, 7], 3)`
- ✅ has() reports membership
- ✅ get() returns the page — got `5`, expected `5`
- ✅ get() does not remove the page
- ✅ take() returns the page — got `5`, expected `5`
- ✅ take() removes the page
- ✅ taking a missing page raises KeyError (raised KeyError)
- ✅ L2 has no capacity limit yet — got `202`, expected `202`

**Result: ✅ PASS**  (8 checks, 0 failed, 0 turns, 0.00s)

---

## U5 — PageTable maps pages to layers

> PageTable stores which layer each page is in.

- ✅ where() returns the stored layer — got `('L2', 'L1')`, expected `('L2', 'L1')`
- ✅ pages_in() is sorted and empty for unknown layers — got `([1, 2], [0], [])`, expected `([1, 2], [0], [])`
- ✅ set() overwrites the previous layer — got `'L1'`, expected `'L1'`
- ✅ where() on an unknown page raises KeyError (raised KeyError)
- ✅ LocationBook is a backward-compatible alias

**Result: ✅ PASS**  (5 checks, 0 failed, 0 turns, 0.00s)

---

## U6 — TopicTable lifecycle

> Topics get increasing ids, only one can be open, and closing/reopening works.

- ✅ starts with no open topic
- ✅ first topic gets id 1, is open, label is the placeholder — got `(1, 1, 'first', True)`, expected `(1, 1, 'first', True)`
- ✅ a second topic cannot be opened while one is open (raised RuntimeError)
- ✅ add_page appends in order — got `[0, 3]`, expected `[0, 3]`
- ✅ close() closes the topic and clears the open topic
- ✅ ids keep increasing — got `2`, expected `2`
- ✅ reopening while another topic is open is refused (raised RuntimeError)
- ✅ a closed topic can be reopened — got `1`, expected `1`
- ✅ closed_topics() excludes the open topic; all() keeps creation order — got `([2], [1, 2])`, expected `([2], [1, 2])`
- ✅ add_page on an unknown topic raises KeyError (raised KeyError)
- ✅ get() on an unknown topic raises KeyError (raised KeyError)

**Result: ✅ PASS**  (11 checks, 0 failed, 0 turns, 0.00s)

---

## S1 — first message creates topic and page

> The very first message opens topic 1 with page 0 in L1, labelled with its first 60 characters.

### Turn 1: "hello world lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum do"

- **Reply (assistant)**: hi lorem ipsum dolor sit amet lo
- **Events in prepare_context**: `new topic 1`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🟢 open | `hello world lorem ipsum dolor sit ame...` | - | - | `[0]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L1** | 1 | 28 | yes | hello world lorem ipsum dolor sit amet lorem ip... |

**L1 after prepare_context**: `[##..........................|.....|.....]` 20/500 tok (4%); `|` marks low 70% / high 85%; L1 pages `[0]`, L2 pages `[]`

**L1 after record_reply**: `[##..........................|.....|.....]` 28/500 tok (6%); `|` marks low 70% / high 85%; L1 pages `[0]`, L2 pages `[]`

**Prompt sent to the model**

> **[USER]** hello world lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum do

<details><summary>Page contents (final state)</summary>

- **L1 page 0** (topic 1, 28 tok, OPEN)
  - `user`: hello world lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum do
  - `assistant`: hi lorem ipsum dolor sit amet lo

</details>

- ✅ one topic exists — got `1`, expected `1`
- ✅ topic 1 is open
- ✅ page 0 exists, is open, is in L1 — got `([0], 0, 'L1')`, expected `([0], 0, 'L1')`
- ✅ placeholder label is the first 60 characters of the message — got `'hello world lorem ipsum dolor sit amet lorem ipsum dolor sit'`, expected `'hello world lorem ipsum dolor sit amet lorem ipsum dolor sit'`
- ✅ the prompt sent to the model is exactly the user message — got `['hello world lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum do']`, expected `['hello world lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum do']`
- ✅ the reply was appended to the same page — got `['user', 'assistant']`, expected `['user', 'assistant']`
- ✅ snapshot() describes L1 and L2
- ✅ drain_events() returns nothing new once drained

**Result: ✅ PASS**  (8 checks, 0 failed, 1 turns, 0.00s)

---

## S2 — continue keeps the same page

> A 'continue' decision adds messages to the open page and creates nothing new.

### Turn 1: "lorem ipsum dolor sit amet lorem ipsum d"

- **Reply (assistant)**: lorem ipsum dolor sit amet lorem ipsum d
- **Events in prepare_context**: `new topic 1`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🟢 open | `lorem ipsum dolor sit amet lorem ipsum d` | - | - | `[0]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L1** | 1 | 20 | yes | lorem ipsum dolor sit amet lorem ipsum d |

**L1 after prepare_context**: `[#...........................|.....|.....]` 10/500 tok (2%); `|` marks low 70% / high 85%; L1 pages `[0]`, L2 pages `[]`

**L1 after record_reply**: `[##..........................|.....|.....]` 20/500 tok (4%); `|` marks low 70% / high 85%; L1 pages `[0]`, L2 pages `[]`

**Prompt sent to the model**

> **[USER]** lorem ipsum dolor sit amet lorem ipsum d

<details><summary>Page contents (final state)</summary>

- **L1 page 0** (topic 1, 20 tok, OPEN)
  - `user`: lorem ipsum dolor sit amet lorem ipsum d
  - `assistant`: lorem ipsum dolor sit amet lorem ipsum d

</details>

### Turn 2: "more lorem ipsum dolor sit amet lorem ip"

- **Reply (assistant)**: lorem ipsum dolor sit amet lorem ipsum d
- **Events in prepare_context**: none
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🟢 open | `lorem ipsum dolor sit amet lorem ipsum d` | - | - | `[0]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L1** | 1 | 40 | yes | lorem ipsum dolor sit amet lorem ipsum d |

**L1 after prepare_context**: `[##..........................|.....|.....]` 30/500 tok (6%); `|` marks low 70% / high 85%; L1 pages `[0]`, L2 pages `[]`

**L1 after record_reply**: `[###.........................|.....|.....]` 40/500 tok (8%); `|` marks low 70% / high 85%; L1 pages `[0]`, L2 pages `[]`

**Prompt sent to the model**

> **[USER]** lorem ipsum dolor sit amet lorem ipsum d
> **[ASSISTANT]** lorem ipsum dolor sit amet lorem ipsum d
> **[USER]** more lorem ipsum dolor sit amet lorem ip

<details><summary>Page contents (final state)</summary>

- **L1 page 0** (topic 1, 40 tok, OPEN)
  - `user`: lorem ipsum dolor sit amet lorem ipsum d
  - `assistant`: lorem ipsum dolor sit amet lorem ipsum d
  - `user`: more lorem ipsum dolor sit amet lorem ip
  - `assistant`: lorem ipsum dolor sit amet lorem ipsum d

</details>

- ✅ still one topic with one page — got `(1, [0])`, expected `(1, [0])`
- ✅ page holds all four messages in order — got `['user', 'assistant', 'user', 'assistant']`, expected `['user', 'assistant', 'user', 'assistant']`
- ✅ no events were emitted for a plain continue — got `[]`, expected `[]`

**Result: ✅ PASS**  (3 checks, 0 failed, 2 turns, 0.00s)

---

## S3 — new topic closes old and writes card

> A 'new' decision closes the open topic, writes its card, and opens the next page.

### Turn 1: "python decorators wrap functions lorem ipsum dol"

- **Reply (assistant)**: decorators use closures lorem ip
- **Events in prepare_context**: `new topic 1`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🟢 open | `python decorators wrap functions lore...` | - | - | `[0]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L1** | 1 | 20 | yes | python decorators wrap functions lorem ipsum dol |

**L1 after prepare_context**: `[#...........................|.....|.....]` 12/500 tok (2%); `|` marks low 70% / high 85%; L1 pages `[0]`, L2 pages `[]`

**L1 after record_reply**: `[##..........................|.....|.....]` 20/500 tok (4%); `|` marks low 70% / high 85%; L1 pages `[0]`, L2 pages `[]`

**Prompt sent to the model**

> **[USER]** python decorators wrap functions lorem ipsum dol

<details><summary>Page contents (final state)</summary>

- **L1 page 0** (topic 1, 20 tok, OPEN)
  - `user`: python decorators wrap functions lorem ipsum dol
  - `assistant`: decorators use closures lorem ip

</details>

### Turn 2: "capital of france lorem ipsum dolor sit amet lor"

- **Reply (assistant)**: paris lorem ipsum dolor sit amet
- **Events in prepare_context**: `closed topic 1, card: dol / closure / python`, `new topic 2`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🔴 closed | `dol / closure / python` | python decorators wrap functions lorem ipsum dol | dol, closure, python, lorem, decorator | `[0]` | 0 |
| 2 | 🟢 open | `capital of france lorem ipsum dolor s...` | - | - | `[1]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L1** | 1 | 20 |  | python decorators wrap functions lorem ipsum dol |
| 1 | **L1** | 2 | 20 | yes | capital of france lorem ipsum dolor sit amet lor |

**L1 after prepare_context**: `[###.........................|.....|.....]` 32/500 tok (6%); `|` marks low 70% / high 85%; L1 pages `[0, 1]`, L2 pages `[]`

**L1 after record_reply**: `[###.........................|.....|.....]` 40/500 tok (8%); `|` marks low 70% / high 85%; L1 pages `[0, 1]`, L2 pages `[]`

**Prompt sent to the model**

> **[USER]** python decorators wrap functions lorem ipsum dol
> **[ASSISTANT]** decorators use closures lorem ip
> **[USER]** capital of france lorem ipsum dolor sit amet lor

<details><summary>Page contents (final state)</summary>

- **L1 page 0** (topic 1, 20 tok)
  - `user`: python decorators wrap functions lorem ipsum dol
  - `assistant`: decorators use closures lorem ip
- **L1 page 1** (topic 2, 20 tok, OPEN)
  - `user`: capital of france lorem ipsum dolor sit amet lor
  - `assistant`: paris lorem ipsum dolor sit amet

</details>

- ✅ topic 1 closed, topic 2 open
- ✅ page 0 closed, page 1 open
- ✅ topic 2 owns the next page number (1) — got `([1], 1)`, expected `([1], 1)`
- ✅ card label was rewritten by the card writer
- ✅ card key_facts contain the user message
- ✅ card has entities and a description
- ✅ card covered_through equals its last page seq — got `0`, expected `0`
- ✅ events report the close and the new topic

**Result: ✅ PASS**  (8 checks, 0 failed, 2 turns, 0.00s)

---

## S4 — return reopens old topic with a new page

> A 'return' decision reopens the old topic; its new page gets the next seq, never an old one.

### Turn 1: "goa beaches lorem ipsum dolor sit amet lorem ips"

- **Reply (assistant)**: lorem ipsum dolor sit amet lorem
- **Events in prepare_context**: `new topic 1`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🟢 open | `goa beaches lorem ipsum dolor sit ame...` | - | - | `[0]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L1** | 1 | 20 | yes | goa beaches lorem ipsum dolor sit amet lorem ips |

**L1 after prepare_context**: `[#...........................|.....|.....]` 12/500 tok (2%); `|` marks low 70% / high 85%; L1 pages `[0]`, L2 pages `[]`

**L1 after record_reply**: `[##..........................|.....|.....]` 20/500 tok (4%); `|` marks low 70% / high 85%; L1 pages `[0]`, L2 pages `[]`

**Prompt sent to the model**

> **[USER]** goa beaches lorem ipsum dolor sit amet lorem ips

<details><summary>Page contents (final state)</summary>

- **L1 page 0** (topic 1, 20 tok, OPEN)
  - `user`: goa beaches lorem ipsum dolor sit amet lorem ips
  - `assistant`: lorem ipsum dolor sit amet lorem

</details>

### Turn 2: "cooking pasta lorem ipsum dolor sit amet lorem i"

- **Reply (assistant)**: lorem ipsum dolor sit amet lorem
- **Events in prepare_context**: `closed topic 1, card: beach / ips / dolor`, `new topic 2`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🔴 closed | `beach / ips / dolor` | goa beaches lorem ipsum dolor sit amet lorem ips | beach, ips, dolor, sit, lorem | `[0]` | 0 |
| 2 | 🟢 open | `cooking pasta lorem ipsum dolor sit a...` | - | - | `[1]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L1** | 1 | 20 |  | goa beaches lorem ipsum dolor sit amet lorem ips |
| 1 | **L1** | 2 | 20 | yes | cooking pasta lorem ipsum dolor sit amet lorem i |

**L1 after prepare_context**: `[###.........................|.....|.....]` 32/500 tok (6%); `|` marks low 70% / high 85%; L1 pages `[0, 1]`, L2 pages `[]`

**L1 after record_reply**: `[###.........................|.....|.....]` 40/500 tok (8%); `|` marks low 70% / high 85%; L1 pages `[0, 1]`, L2 pages `[]`

**Prompt sent to the model**

> **[USER]** goa beaches lorem ipsum dolor sit amet lorem ips
> **[ASSISTANT]** lorem ipsum dolor sit amet lorem
> **[USER]** cooking pasta lorem ipsum dolor sit amet lorem i

<details><summary>Page contents (final state)</summary>

- **L1 page 0** (topic 1, 20 tok)
  - `user`: goa beaches lorem ipsum dolor sit amet lorem ips
  - `assistant`: lorem ipsum dolor sit amet lorem
- **L1 page 1** (topic 2, 20 tok, OPEN)
  - `user`: cooking pasta lorem ipsum dolor sit amet lorem i
  - `assistant`: lorem ipsum dolor sit amet lorem

</details>

### Turn 3: "best goa beach lorem ipsum dolor sit amet lorem "

- **Reply (assistant)**: lorem ipsum dolor sit amet lorem
- **Events in prepare_context**: `closed topic 2, card: ipsum / dolor / sit`, `return to topic 1 (beach / ips / dolor)`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🟢 open | `beach / ips / dolor` | goa beaches lorem ipsum dolor sit amet lorem ips | beach, ips, dolor, sit, lorem | `[0, 2]` | 0 |
| 2 | 🔴 closed | `ipsum / dolor / sit` | cooking pasta lorem ipsum dolor sit amet lorem i | ipsum, dolor, sit, lorem, amet | `[1]` | 1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L1** | 1 | 20 |  | goa beaches lorem ipsum dolor sit amet lorem ips |
| 1 | **L1** | 2 | 20 |  | cooking pasta lorem ipsum dolor sit amet lorem i |
| 2 | **L1** | 1 | 20 | yes | best goa beach lorem ipsum dolor sit amet lorem  |

**L1 after prepare_context**: `[####........................|.....|.....]` 52/500 tok (10%); `|` marks low 70% / high 85%; L1 pages `[0, 1, 2]`, L2 pages `[]`

**L1 after record_reply**: `[#####.......................|.....|.....]` 60/500 tok (12%); `|` marks low 70% / high 85%; L1 pages `[0, 1, 2]`, L2 pages `[]`

**Prompt sent to the model**

> **[USER]** goa beaches lorem ipsum dolor sit amet lorem ips
> **[ASSISTANT]** lorem ipsum dolor sit amet lorem
> **[USER]** cooking pasta lorem ipsum dolor sit amet lorem i
> **[ASSISTANT]** lorem ipsum dolor sit amet lorem
> **[USER]** best goa beach lorem ipsum dolor sit amet lorem 

<details><summary>Page contents (final state)</summary>

- **L1 page 0** (topic 1, 20 tok)
  - `user`: goa beaches lorem ipsum dolor sit amet lorem ips
  - `assistant`: lorem ipsum dolor sit amet lorem
- **L1 page 1** (topic 2, 20 tok)
  - `user`: cooking pasta lorem ipsum dolor sit amet lorem i
  - `assistant`: lorem ipsum dolor sit amet lorem
- **L1 page 2** (topic 1, 20 tok, OPEN)
  - `user`: best goa beach lorem ipsum dolor sit amet lorem 
  - `assistant`: lorem ipsum dolor sit amet lorem

</details>

- ✅ topic 1 reopened, topic 2 closed
- ✅ topic 1 now owns pages [0, 2] and page 2 is the open page — got `([0, 2], 2)`, expected `([0, 2], 2)`
- ✅ page 2 belongs to topic 1 — got `1`, expected `1`
- ✅ the old page 0 stays closed
- ✅ a 'return to topic 1' event was logged
- ✅ topic 2 (closed by the return) got its card written

**Result: ✅ PASS**  (6 checks, 0 failed, 3 turns, 0.00s)

---

## S5 — page splits at max page tokens between turns

> A page splits only when it has reached max_page_tokens (>=), and only at the start of the next turn.

### Turn 1 [page == limit]: "lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet..."

- **Reply (assistant)**: lorem ipsum dolor sit amet lorem
- **Events in prepare_context**: `new topic 1`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🟢 open | `lorem ipsum dolor sit amet lorem ipsu...` | - | - | `[0]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L1** | 1 | 40 | yes | lorem ipsum dolor sit amet lorem ipsum dolor si... |

**L1 after prepare_context**: `[###.........................|.....|.....]` 32/500 tok (6%); `|` marks low 70% / high 85%; L1 pages `[0]`, L2 pages `[]`

**L1 after record_reply**: `[###.........................|.....|.....]` 40/500 tok (8%); `|` marks low 70% / high 85%; L1 pages `[0]`, L2 pages `[]`

**Prompt sent to the model**

> **[USER]** lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ips...

<details><summary>Page contents (final state)</summary>

- **L1 page 0** (topic 1, 40 tok, OPEN)
  - `user`: lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ...
  - `assistant`: lorem ipsum dolor sit amet lorem

</details>

- ✅ setup: page 0 has exactly max_page_tokens — got `40`, expected `40`
### Turn 2 [page == limit]: "lorem ipsum dolor sit amet lorem ipsum d"

- **Reply (assistant)**: lorem ipsum dolor sit amet lorem
- **Events in prepare_context**: none
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🟢 open | `lorem ipsum dolor sit amet lorem ipsu...` | - | - | `[0, 1]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L1** | 1 | 40 |  | lorem ipsum dolor sit amet lorem ipsum dolor si... |
| 1 | **L1** | 1 | 18 | yes | lorem ipsum dolor sit amet lorem ipsum d |

**L1 after prepare_context**: `[####........................|.....|.....]` 50/500 tok (10%); `|` marks low 70% / high 85%; L1 pages `[0, 1]`, L2 pages `[]`

**L1 after record_reply**: `[#####.......................|.....|.....]` 58/500 tok (12%); `|` marks low 70% / high 85%; L1 pages `[0, 1]`, L2 pages `[]`

**Prompt sent to the model**

> **[USER]** lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ips...
> **[ASSISTANT]** lorem ipsum dolor sit amet lorem
> **[USER]** lorem ipsum dolor sit amet lorem ipsum d

<details><summary>Page contents (final state)</summary>

- **L1 page 0** (topic 1, 40 tok)
  - `user`: lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ...
  - `assistant`: lorem ipsum dolor sit amet lorem
- **L1 page 1** (topic 1, 18 tok, OPEN)
  - `user`: lorem ipsum dolor sit amet lorem ipsum d
  - `assistant`: lorem ipsum dolor sit amet lorem

</details>

- ✅ at exactly the limit the next turn opens a second page — got `[0, 1]`, expected `[0, 1]`
- ✅ the old page closes and the new one is open
- ✅ the topic itself stays open (a split is not a topic change) — got `True`, expected `True`
### Turn 1 [page == limit-1]: "lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet..."

- **Reply (assistant)**: lorem ipsum dolor sit amet lorem
- **Events in prepare_context**: `new topic 1`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🟢 open | `lorem ipsum dolor sit amet lorem ipsu...` | - | - | `[0]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L1** | 1 | 39 | yes | lorem ipsum dolor sit amet lorem ipsum dolor si... |

**L1 after prepare_context**: `[##..........................|.....|.....]` 31/500 tok (6%); `|` marks low 70% / high 85%; L1 pages `[0]`, L2 pages `[]`

**L1 after record_reply**: `[###.........................|.....|.....]` 39/500 tok (8%); `|` marks low 70% / high 85%; L1 pages `[0]`, L2 pages `[]`

**Prompt sent to the model**

> **[USER]** lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ips...

<details><summary>Page contents (final state)</summary>

- **L1 page 0** (topic 1, 39 tok, OPEN)
  - `user`: lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ...
  - `assistant`: lorem ipsum dolor sit amet lorem

</details>

- ✅ setup: page 0 is one token under the limit — got `39`, expected `39`
### Turn 2 [page == limit-1]: "lorem ipsum dolor sit amet lorem ipsum d"

- **Reply (assistant)**: lorem ipsum dolor sit amet lorem
- **Events in prepare_context**: none
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🟢 open | `lorem ipsum dolor sit amet lorem ipsu...` | - | - | `[0]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L1** | 1 | 57 | yes | lorem ipsum dolor sit amet lorem ipsum dolor si... |

**L1 after prepare_context**: `[####........................|.....|.....]` 49/500 tok (10%); `|` marks low 70% / high 85%; L1 pages `[0]`, L2 pages `[]`

**L1 after record_reply**: `[#####.......................|.....|.....]` 57/500 tok (11%); `|` marks low 70% / high 85%; L1 pages `[0]`, L2 pages `[]`

**Prompt sent to the model**

> **[USER]** lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ips...
> **[ASSISTANT]** lorem ipsum dolor sit amet lorem
> **[USER]** lorem ipsum dolor sit amet lorem ipsum d

<details><summary>Page contents (final state)</summary>

- **L1 page 0** (topic 1, 57 tok, OPEN)
  - `user`: lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ...
  - `assistant`: lorem ipsum dolor sit amet lorem
  - `user`: lorem ipsum dolor sit amet lorem ipsum d
  - `assistant`: lorem ipsum dolor sit amet lorem

</details>

- ✅ one token under the limit: no split — got `[0]`, expected `[0]`

**Result: ✅ PASS**  (6 checks, 0 failed, 4 turns, 0.00s)

---

## S6 — odd decider output is handled

> Unusual segmenter answers must not crash the manager or corrupt the tables.

### Turn 1 [continue on first message, return without id]: "lorem ipsum dolor sit amet lorem ipsum d"

- **Reply (assistant)**: lorem ipsum dolor si
- **Events in prepare_context**: `new topic 1`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🟢 open | `lorem ipsum dolor sit amet lorem ipsum d` | - | - | `[0]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L1** | 1 | 15 | yes | lorem ipsum dolor sit amet lorem ipsum d |

**L1 after prepare_context**: `[#...........................|.....|.....]` 10/500 tok (2%); `|` marks low 70% / high 85%; L1 pages `[0]`, L2 pages `[]`

**L1 after record_reply**: `[#...........................|.....|.....]` 15/500 tok (3%); `|` marks low 70% / high 85%; L1 pages `[0]`, L2 pages `[]`

**Prompt sent to the model**

> **[USER]** lorem ipsum dolor sit amet lorem ipsum d

<details><summary>Page contents (final state)</summary>

- **L1 page 0** (topic 1, 15 tok, OPEN)
  - `user`: lorem ipsum dolor sit amet lorem ipsum d
  - `assistant`: lorem ipsum dolor si

</details>

- ✅ 'continue' with no open topic still creates topic 1 — got `1`, expected `1`
### Turn 2 [continue on first message, return without id]: "lorem ipsum dolor sit amet lorem ipsum d"

- **Reply (assistant)**: lorem ipsum dolor si
- **Events in prepare_context**: `closed topic 1, card: dolor / sit / lorem`, `new topic 2`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🔴 closed | `dolor / sit / lorem` | lorem ipsum dolor sit amet lorem ipsum d | dolor, sit, lorem, amet, ipsum | `[0]` | 0 |
| 2 | 🟢 open | `lorem ipsum dolor sit amet lorem ipsum d` | - | - | `[1]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L1** | 1 | 15 |  | lorem ipsum dolor sit amet lorem ipsum d |
| 1 | **L1** | 2 | 15 | yes | lorem ipsum dolor sit amet lorem ipsum d |

**L1 after prepare_context**: `[##..........................|.....|.....]` 25/500 tok (5%); `|` marks low 70% / high 85%; L1 pages `[0, 1]`, L2 pages `[]`

**L1 after record_reply**: `[##..........................|.....|.....]` 30/500 tok (6%); `|` marks low 70% / high 85%; L1 pages `[0, 1]`, L2 pages `[]`

**Prompt sent to the model**

> **[USER]** lorem ipsum dolor sit amet lorem ipsum d
> **[ASSISTANT]** lorem ipsum dolor si
> **[USER]** lorem ipsum dolor sit amet lorem ipsum d

<details><summary>Page contents (final state)</summary>

- **L1 page 0** (topic 1, 15 tok)
  - `user`: lorem ipsum dolor sit amet lorem ipsum d
  - `assistant`: lorem ipsum dolor si
- **L1 page 1** (topic 2, 15 tok, OPEN)
  - `user`: lorem ipsum dolor sit amet lorem ipsum d
  - `assistant`: lorem ipsum dolor si

</details>

- ✅ 'return' without a topic_id is treated as a new topic — got `(2, False)`, expected `(2, False)`
### Turn 1 [return to the topic that is already open]: "alpha lorem ipsum dolor sit amet lorem i"

- **Reply (assistant)**: lorem ipsum dolor si
- **Events in prepare_context**: `new topic 1`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🟢 open | `alpha lorem ipsum dolor sit amet lorem i` | - | - | `[0]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L1** | 1 | 15 | yes | alpha lorem ipsum dolor sit amet lorem i |

**L1 after prepare_context**: `[#...........................|.....|.....]` 10/500 tok (2%); `|` marks low 70% / high 85%; L1 pages `[0]`, L2 pages `[]`

**L1 after record_reply**: `[#...........................|.....|.....]` 15/500 tok (3%); `|` marks low 70% / high 85%; L1 pages `[0]`, L2 pages `[]`

**Prompt sent to the model**

> **[USER]** alpha lorem ipsum dolor sit amet lorem i

<details><summary>Page contents (final state)</summary>

- **L1 page 0** (topic 1, 15 tok, OPEN)
  - `user`: alpha lorem ipsum dolor sit amet lorem i
  - `assistant`: lorem ipsum dolor si

</details>

### Turn 2 [return to the topic that is already open]: "alpha lorem ipsum dolor sit amet lorem i"

- **Reply (assistant)**: lorem ipsum dolor si
- **Events in prepare_context**: `closed topic 1, card: alpha / dolor / sit`, `return to topic 1 (alpha / dolor / sit)`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🟢 open | `alpha / dolor / sit` | alpha lorem ipsum dolor sit amet lorem i | alpha, dolor, sit, lorem, amet | `[0, 1]` | 0 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L1** | 1 | 15 |  | alpha lorem ipsum dolor sit amet lorem i |
| 1 | **L1** | 1 | 15 | yes | alpha lorem ipsum dolor sit amet lorem i |

**L1 after prepare_context**: `[##..........................|.....|.....]` 25/500 tok (5%); `|` marks low 70% / high 85%; L1 pages `[0, 1]`, L2 pages `[]`

**L1 after record_reply**: `[##..........................|.....|.....]` 30/500 tok (6%); `|` marks low 70% / high 85%; L1 pages `[0, 1]`, L2 pages `[]`

**Prompt sent to the model**

> **[USER]** alpha lorem ipsum dolor sit amet lorem i
> **[ASSISTANT]** lorem ipsum dolor si
> **[USER]** alpha lorem ipsum dolor sit amet lorem i

<details><summary>Page contents (final state)</summary>

- **L1 page 0** (topic 1, 15 tok)
  - `user`: alpha lorem ipsum dolor sit amet lorem i
  - `assistant`: lorem ipsum dolor si
- **L1 page 1** (topic 1, 15 tok, OPEN)
  - `user`: alpha lorem ipsum dolor sit amet lorem i
  - `assistant`: lorem ipsum dolor si

</details>

- ✅ returning to the open topic closes and reopens it with a fresh page — got `(True, [0, 1])`, expected `(True, [0, 1])`
### Turn 1 [return to a topic id that does not exist]: "alpha lorem ipsum dolor sit amet lorem i"

- **Reply (assistant)**: lorem ipsum dolor si
- **Events in prepare_context**: `new topic 1`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🟢 open | `alpha lorem ipsum dolor sit amet lorem i` | - | - | `[0]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L1** | 1 | 15 | yes | alpha lorem ipsum dolor sit amet lorem i |

**L1 after prepare_context**: `[#...........................|.....|.....]` 10/500 tok (2%); `|` marks low 70% / high 85%; L1 pages `[0]`, L2 pages `[]`

**L1 after record_reply**: `[#...........................|.....|.....]` 15/500 tok (3%); `|` marks low 70% / high 85%; L1 pages `[0]`, L2 pages `[]`

**Prompt sent to the model**

> **[USER]** alpha lorem ipsum dolor sit amet lorem i

<details><summary>Page contents (final state)</summary>

- **L1 page 0** (topic 1, 15 tok, OPEN)
  - `user`: alpha lorem ipsum dolor sit amet lorem i
  - `assistant`: lorem ipsum dolor si

</details>

### Turn 2 [return to a topic id that does not exist]: "beta lorem ipsum dolor sit amet lorem ip"

- ❌ **Raised** `KeyError: 99`
- **Reply (assistant)**: lorem ipsum dolor si
- **Events in prepare_context**: none
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🟢 open | `alpha lorem ipsum dolor sit amet lorem i` | - | - | `[0]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L1** | 1 | 15 | yes | alpha lorem ipsum dolor sit amet lorem i |

**L1 after prepare_context**: `[#...........................|.....|.....]` 15/500 tok (3%); `|` marks low 70% / high 85%; L1 pages `[0]`, L2 pages `[]`

**L1 after record_reply**: `[#...........................|.....|.....]` 15/500 tok (3%); `|` marks low 70% / high 85%; L1 pages `[0]`, L2 pages `[]`

**Prompt sent to the model**

> *(not produced)*

<details><summary>Page contents (final state)</summary>

- **L1 page 0** (topic 1, 15 tok, OPEN)
  - `user`: alpha lorem ipsum dolor sit amet lorem i
  - `assistant`: lorem ipsum dolor si

</details>

- ✅ an unknown topic id is either rejected or handled (got KeyError)
- ✅ after rejecting the unknown topic id the state is unchanged (nothing half-applied)

**Result: ✅ PASS**  (5 checks, 0 failed, 6 turns, 0.00s)

---

## R1 — router sees only closed topics

> The router is not called when nothing is closed, and never receives the open topic.

### Turn 1: "u0 lorem ipsum dolor sit amet lorem ipsu"

- **Reply (assistant)**: r0 lorem ipsum dolor sit
- **Events in prepare_context**: `new topic 1`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🟢 open | `u0 lorem ipsum dolor sit amet lorem ipsu` | - | - | `[0]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L1** | 1 | 16 | yes | u0 lorem ipsum dolor sit amet lorem ipsu |

**L1 after prepare_context**: `[#...........................|.....|.....]` 10/500 tok (2%); `|` marks low 70% / high 85%; L1 pages `[0]`, L2 pages `[]`

**L1 after record_reply**: `[#...........................|.....|.....]` 16/500 tok (3%); `|` marks low 70% / high 85%; L1 pages `[0]`, L2 pages `[]`

**Prompt sent to the model**

> **[USER]** u0 lorem ipsum dolor sit amet lorem ipsu

<details><summary>Page contents (final state)</summary>

- **L1 page 0** (topic 1, 16 tok, OPEN)
  - `user`: u0 lorem ipsum dolor sit amet lorem ipsu
  - `assistant`: r0 lorem ipsum dolor sit

</details>

### Turn 2: "u1 lorem ipsum dolor sit amet lorem ipsu"

- **Reply (assistant)**: r1 lorem ipsum dolor sit
- **Events in prepare_context**: `closed topic 1, card: dolor / ipsu / sit`, `new topic 2`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🔴 closed | `dolor / ipsu / sit` | u0 lorem ipsum dolor sit amet lorem ipsu | dolor, ipsu, sit, lorem, amet | `[0]` | 0 |
| 2 | 🟢 open | `u1 lorem ipsum dolor sit amet lorem ipsu` | - | - | `[1]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L1** | 1 | 16 |  | u0 lorem ipsum dolor sit amet lorem ipsu |
| 1 | **L1** | 2 | 16 | yes | u1 lorem ipsum dolor sit amet lorem ipsu |

**L1 after prepare_context**: `[##..........................|.....|.....]` 26/500 tok (5%); `|` marks low 70% / high 85%; L1 pages `[0, 1]`, L2 pages `[]`

**L1 after record_reply**: `[###.........................|.....|.....]` 32/500 tok (6%); `|` marks low 70% / high 85%; L1 pages `[0, 1]`, L2 pages `[]`

**Prompt sent to the model**

> **[USER]** u0 lorem ipsum dolor sit amet lorem ipsu
> **[ASSISTANT]** r0 lorem ipsum dolor sit
> **[USER]** u1 lorem ipsum dolor sit amet lorem ipsu

<details><summary>Page contents (final state)</summary>

- **L1 page 0** (topic 1, 16 tok)
  - `user`: u0 lorem ipsum dolor sit amet lorem ipsu
  - `assistant`: r0 lorem ipsum dolor sit
- **L1 page 1** (topic 2, 16 tok, OPEN)
  - `user`: u1 lorem ipsum dolor sit amet lorem ipsu
  - `assistant`: r1 lorem ipsum dolor sit

</details>

### Turn 3: "u2 lorem ipsum dolor sit amet lorem ipsu"

- **Reply (assistant)**: r2 lorem ipsum dolor sit
- **Events in prepare_context**: none
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🔴 closed | `dolor / ipsu / sit` | u0 lorem ipsum dolor sit amet lorem ipsu | dolor, ipsu, sit, lorem, amet | `[0]` | 0 |
| 2 | 🟢 open | `u1 lorem ipsum dolor sit amet lorem ipsu` | - | - | `[1]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L1** | 1 | 16 |  | u0 lorem ipsum dolor sit amet lorem ipsu |
| 1 | **L1** | 2 | 32 | yes | u1 lorem ipsum dolor sit amet lorem ipsu |

**L1 after prepare_context**: `[###.........................|.....|.....]` 42/500 tok (8%); `|` marks low 70% / high 85%; L1 pages `[0, 1]`, L2 pages `[]`

**L1 after record_reply**: `[####........................|.....|.....]` 48/500 tok (10%); `|` marks low 70% / high 85%; L1 pages `[0, 1]`, L2 pages `[]`

**Prompt sent to the model**

> **[USER]** u0 lorem ipsum dolor sit amet lorem ipsu
> **[ASSISTANT]** r0 lorem ipsum dolor sit
> **[USER]** u1 lorem ipsum dolor sit amet lorem ipsu
> **[ASSISTANT]** r1 lorem ipsum dolor sit
> **[USER]** u2 lorem ipsum dolor sit amet lorem ipsu

<details><summary>Page contents (final state)</summary>

- **L1 page 0** (topic 1, 16 tok)
  - `user`: u0 lorem ipsum dolor sit amet lorem ipsu
  - `assistant`: r0 lorem ipsum dolor sit
- **L1 page 1** (topic 2, 32 tok, OPEN)
  - `user`: u1 lorem ipsum dolor sit amet lorem ipsu
  - `assistant`: r1 lorem ipsum dolor sit
  - `user`: u2 lorem ipsum dolor sit amet lorem ipsu
  - `assistant`: r2 lorem ipsum dolor sit

</details>

### Turn 4: "u3 lorem ipsum dolor sit amet lorem ipsu"

- **Reply (assistant)**: r3 lorem ipsum dolor sit
- **Events in prepare_context**: `closed topic 2, card: dolor / ipsu / sit`, `new topic 3`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🔴 closed | `dolor / ipsu / sit` | u0 lorem ipsum dolor sit amet lorem ipsu | dolor, ipsu, sit, lorem, amet | `[0]` | 0 |
| 2 | 🔴 closed | `dolor / ipsu / sit` | u1 lorem ipsum dolor sit amet lorem ipsu; u2 lorem ipsum ... | dolor, ipsu, sit, lorem, amet | `[1]` | 1 |
| 3 | 🟢 open | `u3 lorem ipsum dolor sit amet lorem ipsu` | - | - | `[2]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L1** | 1 | 16 |  | u0 lorem ipsum dolor sit amet lorem ipsu |
| 1 | **L1** | 2 | 32 |  | u1 lorem ipsum dolor sit amet lorem ipsu |
| 2 | **L1** | 3 | 16 | yes | u3 lorem ipsum dolor sit amet lorem ipsu |

**L1 after prepare_context**: `[#####.......................|.....|.....]` 58/500 tok (12%); `|` marks low 70% / high 85%; L1 pages `[0, 1, 2]`, L2 pages `[]`

**L1 after record_reply**: `[#####.......................|.....|.....]` 64/500 tok (13%); `|` marks low 70% / high 85%; L1 pages `[0, 1, 2]`, L2 pages `[]`

**Prompt sent to the model**

> **[USER]** u0 lorem ipsum dolor sit amet lorem ipsu
> **[ASSISTANT]** r0 lorem ipsum dolor sit
> **[USER]** u1 lorem ipsum dolor sit amet lorem ipsu
> **[ASSISTANT]** r1 lorem ipsum dolor sit
> **[USER]** u2 lorem ipsum dolor sit amet lorem ipsu
> **[ASSISTANT]** r2 lorem ipsum dolor sit
> **[USER]** u3 lorem ipsum dolor sit amet lorem ipsu

<details><summary>Page contents (final state)</summary>

- **L1 page 0** (topic 1, 16 tok)
  - `user`: u0 lorem ipsum dolor sit amet lorem ipsu
  - `assistant`: r0 lorem ipsum dolor sit
- **L1 page 1** (topic 2, 32 tok)
  - `user`: u1 lorem ipsum dolor sit amet lorem ipsu
  - `assistant`: r1 lorem ipsum dolor sit
  - `user`: u2 lorem ipsum dolor sit amet lorem ipsu
  - `assistant`: r2 lorem ipsum dolor sit
- **L1 page 2** (topic 3, 16 tok, OPEN)
  - `user`: u3 lorem ipsum dolor sit amet lorem ipsu
  - `assistant`: r3 lorem ipsum dolor sit

</details>

- ✅ router was called on turns 2-4 with exactly the closed topics — got `[[1], [1], [1, 2]]`, expected `[[1], [1], [1, 2]]`
- ✅ router was skipped on turn 1 (no closed topics) — got `[2, 3, 4]`, expected `[2, 3, 4]`
- ✅ the open topic id never appears in what the router receives

**Result: ✅ PASS**  (3 checks, 0 failed, 4 turns, 0.00s)

---

## R2 — router gets the recent window

> The deciders see the last `recent_window` messages, not the whole history.

### Turn 1: "user1 lorem ipsum dolor sit amet lorem i"

- **Reply (assistant)**: reply1 lorem ipsum dolor
- **Events in prepare_context**: `new topic 1`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🟢 open | `user1 lorem ipsum dolor sit amet lorem i` | - | - | `[0]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L1** | 1 | 16 | yes | user1 lorem ipsum dolor sit amet lorem i |

**L1 after prepare_context**: `[#...........................|.....|.....]` 10/500 tok (2%); `|` marks low 70% / high 85%; L1 pages `[0]`, L2 pages `[]`

**L1 after record_reply**: `[#...........................|.....|.....]` 16/500 tok (3%); `|` marks low 70% / high 85%; L1 pages `[0]`, L2 pages `[]`

**Prompt sent to the model**

> **[USER]** user1 lorem ipsum dolor sit amet lorem i

<details><summary>Page contents (final state)</summary>

- **L1 page 0** (topic 1, 16 tok, OPEN)
  - `user`: user1 lorem ipsum dolor sit amet lorem i
  - `assistant`: reply1 lorem ipsum dolor

</details>

### Turn 2: "user2 lorem ipsum dolor sit amet lorem i"

- **Reply (assistant)**: reply2 lorem ipsum dolor
- **Events in prepare_context**: `closed topic 1, card: dolor / reply / sit`, `new topic 2`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🔴 closed | `dolor / reply / sit` | user1 lorem ipsum dolor sit amet lorem i | dolor, reply, sit, lorem, amet | `[0]` | 0 |
| 2 | 🟢 open | `user2 lorem ipsum dolor sit amet lorem i` | - | - | `[1]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L1** | 1 | 16 |  | user1 lorem ipsum dolor sit amet lorem i |
| 1 | **L1** | 2 | 16 | yes | user2 lorem ipsum dolor sit amet lorem i |

**L1 after prepare_context**: `[##..........................|.....|.....]` 26/500 tok (5%); `|` marks low 70% / high 85%; L1 pages `[0, 1]`, L2 pages `[]`

**L1 after record_reply**: `[###.........................|.....|.....]` 32/500 tok (6%); `|` marks low 70% / high 85%; L1 pages `[0, 1]`, L2 pages `[]`

**Prompt sent to the model**

> **[USER]** user1 lorem ipsum dolor sit amet lorem i
> **[ASSISTANT]** reply1 lorem ipsum dolor
> **[USER]** user2 lorem ipsum dolor sit amet lorem i

<details><summary>Page contents (final state)</summary>

- **L1 page 0** (topic 1, 16 tok)
  - `user`: user1 lorem ipsum dolor sit amet lorem i
  - `assistant`: reply1 lorem ipsum dolor
- **L1 page 1** (topic 2, 16 tok, OPEN)
  - `user`: user2 lorem ipsum dolor sit amet lorem i
  - `assistant`: reply2 lorem ipsum dolor

</details>

### Turn 3: "user3 lorem ipsum dolor sit amet lorem i"

- **Reply (assistant)**: reply3 lorem ipsum dolor
- **Events in prepare_context**: `closed topic 2, card: dolor / reply / sit`, `new topic 3`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🔴 closed | `dolor / reply / sit` | user1 lorem ipsum dolor sit amet lorem i | dolor, reply, sit, lorem, amet | `[0]` | 0 |
| 2 | 🔴 closed | `dolor / reply / sit` | user2 lorem ipsum dolor sit amet lorem i | dolor, reply, sit, lorem, amet | `[1]` | 1 |
| 3 | 🟢 open | `user3 lorem ipsum dolor sit amet lorem i` | - | - | `[2]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L1** | 1 | 16 |  | user1 lorem ipsum dolor sit amet lorem i |
| 1 | **L1** | 2 | 16 |  | user2 lorem ipsum dolor sit amet lorem i |
| 2 | **L1** | 3 | 16 | yes | user3 lorem ipsum dolor sit amet lorem i |

**L1 after prepare_context**: `[###.........................|.....|.....]` 42/500 tok (8%); `|` marks low 70% / high 85%; L1 pages `[0, 1, 2]`, L2 pages `[]`

**L1 after record_reply**: `[####........................|.....|.....]` 48/500 tok (10%); `|` marks low 70% / high 85%; L1 pages `[0, 1, 2]`, L2 pages `[]`

**Prompt sent to the model**

> **[USER]** user1 lorem ipsum dolor sit amet lorem i
> **[ASSISTANT]** reply1 lorem ipsum dolor
> **[USER]** user2 lorem ipsum dolor sit amet lorem i
> **[ASSISTANT]** reply2 lorem ipsum dolor
> **[USER]** user3 lorem ipsum dolor sit amet lorem i

<details><summary>Page contents (final state)</summary>

- **L1 page 0** (topic 1, 16 tok)
  - `user`: user1 lorem ipsum dolor sit amet lorem i
  - `assistant`: reply1 lorem ipsum dolor
- **L1 page 1** (topic 2, 16 tok)
  - `user`: user2 lorem ipsum dolor sit amet lorem i
  - `assistant`: reply2 lorem ipsum dolor
- **L1 page 2** (topic 3, 16 tok, OPEN)
  - `user`: user3 lorem ipsum dolor sit amet lorem i
  - `assistant`: reply3 lorem ipsum dolor

</details>

### Turn 4: "user4 lorem ipsum dolor sit amet lorem i"

- **Reply (assistant)**: reply4 lorem ipsum dolor
- **Events in prepare_context**: `closed topic 3, card: dolor / reply / sit`, `new topic 4`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🔴 closed | `dolor / reply / sit` | user1 lorem ipsum dolor sit amet lorem i | dolor, reply, sit, lorem, amet | `[0]` | 0 |
| 2 | 🔴 closed | `dolor / reply / sit` | user2 lorem ipsum dolor sit amet lorem i | dolor, reply, sit, lorem, amet | `[1]` | 1 |
| 3 | 🔴 closed | `dolor / reply / sit` | user3 lorem ipsum dolor sit amet lorem i | dolor, reply, sit, lorem, amet | `[2]` | 2 |
| 4 | 🟢 open | `user4 lorem ipsum dolor sit amet lorem i` | - | - | `[3]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L1** | 1 | 16 |  | user1 lorem ipsum dolor sit amet lorem i |
| 1 | **L1** | 2 | 16 |  | user2 lorem ipsum dolor sit amet lorem i |
| 2 | **L1** | 3 | 16 |  | user3 lorem ipsum dolor sit amet lorem i |
| 3 | **L1** | 4 | 16 | yes | user4 lorem ipsum dolor sit amet lorem i |

**L1 after prepare_context**: `[#####.......................|.....|.....]` 58/500 tok (12%); `|` marks low 70% / high 85%; L1 pages `[0, 1, 2, 3]`, L2 pages `[]`

**L1 after record_reply**: `[#####.......................|.....|.....]` 64/500 tok (13%); `|` marks low 70% / high 85%; L1 pages `[0, 1, 2, 3]`, L2 pages `[]`

**Prompt sent to the model**

> **[USER]** user1 lorem ipsum dolor sit amet lorem i
> **[ASSISTANT]** reply1 lorem ipsum dolor
> **[USER]** user2 lorem ipsum dolor sit amet lorem i
> **[ASSISTANT]** reply2 lorem ipsum dolor
> **[USER]** user3 lorem ipsum dolor sit amet lorem i
> **[ASSISTANT]** reply3 lorem ipsum dolor
> **[USER]** user4 lorem ipsum dolor sit amet lorem i

<details><summary>Page contents (final state)</summary>

- **L1 page 0** (topic 1, 16 tok)
  - `user`: user1 lorem ipsum dolor sit amet lorem i
  - `assistant`: reply1 lorem ipsum dolor
- **L1 page 1** (topic 2, 16 tok)
  - `user`: user2 lorem ipsum dolor sit amet lorem i
  - `assistant`: reply2 lorem ipsum dolor
- **L1 page 2** (topic 3, 16 tok)
  - `user`: user3 lorem ipsum dolor sit amet lorem i
  - `assistant`: reply3 lorem ipsum dolor
- **L1 page 3** (topic 4, 16 tok, OPEN)
  - `user`: user4 lorem ipsum dolor sit amet lorem i
  - `assistant`: reply4 lorem ipsum dolor

</details>

- ✅ on turn 4 the router saw exactly the last 4 messages before the new one (user2, reply2, user3, reply3) — got `['user2 lorem ipsum dolor sit amet lorem i', 'reply2 lorem ipsum dolor', 'user3 lorem ipsum dolor sit amet lorem i', 'reply3 lorem ipsum dolor']`, expected `['user2 lorem ipsum dolor sit amet lorem i', 'reply2 lorem ipsum dolor', 'user3 lorem ipsum dolor sit amet lorem i', 'reply3 lorem ipsum dolor']`
- ✅ and the new message separately — got `'user4 lorem ipsum dolor sit amet lorem i'`, expected `'user4 lorem ipsum dolor sit amet lorem i'`

**Result: ✅ PASS**  (2 checks, 0 failed, 4 turns, 0.00s)

---

## R3 — needed threshold boundary

> A topic scoring exactly needed_threshold is brought in; just below is not.

### Turn 1 [score 0.50]: "lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem "

- **Reply (assistant)**: lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem 
- **Events in prepare_context**: `new topic 1`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🟢 open | `lorem ipsum dolor sit amet lorem ipsu...` | - | - | `[0]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L1** | 1 | 30 | yes | lorem ipsum dolor sit amet lorem ipsum dolor si... |

**L1 after prepare_context**: `[######......|.......|...................]` 15/100 tok (15%); `|` marks low 30% / high 50%; L1 pages `[0]`, L2 pages `[]`

**L1 after record_reply**: `[############|.......|...................]` 30/100 tok (30%); `|` marks low 30% / high 50%; L1 pages `[0]`, L2 pages `[]`

**Prompt sent to the model**

> **[USER]** lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem 

<details><summary>Page contents (final state)</summary>

- **L1 page 0** (topic 1, 30 tok, OPEN)
  - `user`: lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem 
  - `assistant`: lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem 

</details>

### Turn 2 [score 0.50]: "lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor s"

- **Reply (assistant)**: lorem ipsum dolor si
- **Events in prepare_context**: `closed topic 1, card: dolor / sit / lorem`, `new topic 2`, `move page 0: L1 -> L2`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🔴 closed | `dolor / sit / lorem` | lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem  | dolor, sit, lorem, amet, ipsum | `[0]` | 0 |
| 2 | 🟢 open | `lorem ipsum dolor sit amet lorem ipsu...` | - | - | `[1]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L2** | 1 | 30 |  | lorem ipsum dolor sit amet lorem ipsum dolor si... |
| 1 | **L1** | 2 | 30 | yes | lorem ipsum dolor sit amet lorem ipsum dolor si... |

**L1 after prepare_context**: `[##########..|.......|...................]` 25/100 tok (25%); `|` marks low 30% / high 50%; L1 pages `[1]`, L2 pages `[0]`

**L1 after record_reply**: `[############|.......|...................]` 30/100 tok (30%); `|` marks low 30% / high 50%; L1 pages `[1]`, L2 pages `[0]`

**Prompt sent to the model**

> **[SYSTEM]** [earlier messages omitted]
> **[USER]** lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor s

<details><summary>Page contents (final state)</summary>

- **L1 page 1** (topic 2, 30 tok, OPEN)
  - `user`: lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ...
  - `assistant`: lorem ipsum dolor si
- **L2 page 0** (topic 1, 30 tok)
  - `user`: lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem 
  - `assistant`: lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem 

</details>

- ✅ [score 0.50] setup: page 0 was demoted to L2 on turn 2 — got `'L2'`, expected `'L2'`
### Turn 3 [score 0.50]: "lorem ipsum dolor si"

- **Reply (assistant)**: lorem ipsum dolor si
- **Events in prepare_context**: `move page 0: L2 -> L1`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🔴 closed | `dolor / sit / lorem` | lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem  | dolor, sit, lorem, amet, ipsum | `[0]` | 0 |
| 2 | 🟢 open | `lorem ipsum dolor sit amet lorem ipsu...` | - | - | `[1]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L1** | 1 | 30 |  | lorem ipsum dolor sit amet lorem ipsum dolor si... |
| 1 | **L1** | 2 | 40 | yes | lorem ipsum dolor sit amet lorem ipsum dolor si... |

**L1 after prepare_context**: `[############|#######|#####..............]` 65/100 tok (65%); `|` marks low 30% / high 50%; L1 pages `[0, 1]`, L2 pages `[]`

**L1 after record_reply**: `[############|#######|#######............]` 70/100 tok (70%); `|` marks low 30% / high 50%; L1 pages `[0, 1]`, L2 pages `[]`

**Prompt sent to the model**

> **[USER]** lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem 
> **[ASSISTANT]** lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem 
> **[USER]** lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor s
> **[ASSISTANT]** lorem ipsum dolor si
> **[USER]** lorem ipsum dolor si

<details><summary>Page contents (final state)</summary>

- **L1 page 0** (topic 1, 30 tok)
  - `user`: lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem 
  - `assistant`: lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem 
- **L1 page 1** (topic 2, 40 tok, OPEN)
  - `user`: lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ...
  - `assistant`: lorem ipsum dolor si
  - `user`: lorem ipsum dolor si
  - `assistant`: lorem ipsum dolor si

</details>

- ✅ score 0.50 == threshold: page 0 comes back to L1 — got `'L1'`, expected `'L1'`
### Turn 1 [score 0.49]: "lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem "

- **Reply (assistant)**: lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem 
- **Events in prepare_context**: `new topic 1`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🟢 open | `lorem ipsum dolor sit amet lorem ipsu...` | - | - | `[0]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L1** | 1 | 30 | yes | lorem ipsum dolor sit amet lorem ipsum dolor si... |

**L1 after prepare_context**: `[######......|.......|...................]` 15/100 tok (15%); `|` marks low 30% / high 50%; L1 pages `[0]`, L2 pages `[]`

**L1 after record_reply**: `[############|.......|...................]` 30/100 tok (30%); `|` marks low 30% / high 50%; L1 pages `[0]`, L2 pages `[]`

**Prompt sent to the model**

> **[USER]** lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem 

<details><summary>Page contents (final state)</summary>

- **L1 page 0** (topic 1, 30 tok, OPEN)
  - `user`: lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem 
  - `assistant`: lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem 

</details>

### Turn 2 [score 0.49]: "lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor s"

- **Reply (assistant)**: lorem ipsum dolor si
- **Events in prepare_context**: `closed topic 1, card: dolor / sit / lorem`, `new topic 2`, `move page 0: L1 -> L2`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🔴 closed | `dolor / sit / lorem` | lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem  | dolor, sit, lorem, amet, ipsum | `[0]` | 0 |
| 2 | 🟢 open | `lorem ipsum dolor sit amet lorem ipsu...` | - | - | `[1]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L2** | 1 | 30 |  | lorem ipsum dolor sit amet lorem ipsum dolor si... |
| 1 | **L1** | 2 | 30 | yes | lorem ipsum dolor sit amet lorem ipsum dolor si... |

**L1 after prepare_context**: `[##########..|.......|...................]` 25/100 tok (25%); `|` marks low 30% / high 50%; L1 pages `[1]`, L2 pages `[0]`

**L1 after record_reply**: `[############|.......|...................]` 30/100 tok (30%); `|` marks low 30% / high 50%; L1 pages `[1]`, L2 pages `[0]`

**Prompt sent to the model**

> **[SYSTEM]** [earlier messages omitted]
> **[USER]** lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor s

<details><summary>Page contents (final state)</summary>

- **L1 page 1** (topic 2, 30 tok, OPEN)
  - `user`: lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ...
  - `assistant`: lorem ipsum dolor si
- **L2 page 0** (topic 1, 30 tok)
  - `user`: lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem 
  - `assistant`: lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem 

</details>

- ✅ [score 0.49] setup: page 0 was demoted to L2 on turn 2 — got `'L2'`, expected `'L2'`
### Turn 3 [score 0.49]: "lorem ipsum dolor si"

- **Reply (assistant)**: lorem ipsum dolor si
- **Events in prepare_context**: none
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🔴 closed | `dolor / sit / lorem` | lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem  | dolor, sit, lorem, amet, ipsum | `[0]` | 0 |
| 2 | 🟢 open | `lorem ipsum dolor sit amet lorem ipsu...` | - | - | `[1]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L2** | 1 | 30 |  | lorem ipsum dolor sit amet lorem ipsum dolor si... |
| 1 | **L1** | 2 | 40 | yes | lorem ipsum dolor sit amet lorem ipsum dolor si... |

**L1 after prepare_context**: `[############|#......|...................]` 35/100 tok (35%); `|` marks low 30% / high 50%; L1 pages `[1]`, L2 pages `[0]`

**L1 after record_reply**: `[############|###....|...................]` 40/100 tok (40%); `|` marks low 30% / high 50%; L1 pages `[1]`, L2 pages `[0]`

**Prompt sent to the model**

> **[SYSTEM]** [earlier messages omitted]
> **[USER]** lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor s
> **[ASSISTANT]** lorem ipsum dolor si
> **[USER]** lorem ipsum dolor si

<details><summary>Page contents (final state)</summary>

- **L1 page 1** (topic 2, 40 tok, OPEN)
  - `user`: lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ...
  - `assistant`: lorem ipsum dolor si
  - `user`: lorem ipsum dolor si
  - `assistant`: lorem ipsum dolor si
- **L2 page 0** (topic 1, 30 tok)
  - `user`: lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem 
  - `assistant`: lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem 

</details>

- ✅ score 0.49 < threshold: page 0 stays in L2 — got `'L2'`, expected `'L2'`

**Result: ✅ PASS**  (4 checks, 0 failed, 6 turns, 0.00s)

---

## R4 — open topic always scores 1

> The current topic is always treated as fully needed, whatever the router says about others.

### Turn 1: "lorem ipsum dolor sit amet lorem ipsum d"

- **Reply (assistant)**: lorem ipsum dolor si
- **Events in prepare_context**: `new topic 1`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🟢 open | `lorem ipsum dolor sit amet lorem ipsum d` | - | - | `[0]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L1** | 1 | 15 | yes | lorem ipsum dolor sit amet lorem ipsum d |

**L1 after prepare_context**: `[#...........................|.....|.....]` 10/500 tok (2%); `|` marks low 70% / high 85%; L1 pages `[0]`, L2 pages `[]`

**L1 after record_reply**: `[#...........................|.....|.....]` 15/500 tok (3%); `|` marks low 70% / high 85%; L1 pages `[0]`, L2 pages `[]`

**Prompt sent to the model**

> **[USER]** lorem ipsum dolor sit amet lorem ipsum d

<details><summary>Page contents (final state)</summary>

- **L1 page 0** (topic 1, 15 tok, OPEN)
  - `user`: lorem ipsum dolor sit amet lorem ipsum d
  - `assistant`: lorem ipsum dolor si

</details>

### Turn 2: "lorem ipsum dolor sit amet lorem ipsum d"

- **Reply (assistant)**: lorem ipsum dolor si
- **Events in prepare_context**: `closed topic 1, card: dolor / sit / lorem`, `new topic 2`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🔴 closed | `dolor / sit / lorem` | lorem ipsum dolor sit amet lorem ipsum d | dolor, sit, lorem, amet, ipsum | `[0]` | 0 |
| 2 | 🟢 open | `lorem ipsum dolor sit amet lorem ipsum d` | - | - | `[1]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L1** | 1 | 15 |  | lorem ipsum dolor sit amet lorem ipsum d |
| 1 | **L1** | 2 | 15 | yes | lorem ipsum dolor sit amet lorem ipsum d |

**L1 after prepare_context**: `[##..........................|.....|.....]` 25/500 tok (5%); `|` marks low 70% / high 85%; L1 pages `[0, 1]`, L2 pages `[]`

**L1 after record_reply**: `[##..........................|.....|.....]` 30/500 tok (6%); `|` marks low 70% / high 85%; L1 pages `[0, 1]`, L2 pages `[]`

**Prompt sent to the model**

> **[USER]** lorem ipsum dolor sit amet lorem ipsum d
> **[ASSISTANT]** lorem ipsum dolor si
> **[USER]** lorem ipsum dolor sit amet lorem ipsum d

<details><summary>Page contents (final state)</summary>

- **L1 page 0** (topic 1, 15 tok)
  - `user`: lorem ipsum dolor sit amet lorem ipsum d
  - `assistant`: lorem ipsum dolor si
- **L1 page 1** (topic 2, 15 tok, OPEN)
  - `user`: lorem ipsum dolor sit amet lorem ipsum d
  - `assistant`: lorem ipsum dolor si

</details>

- ✅ open topic 2 has score 1.0 — got `1.0`, expected `1.0`
- ✅ closed topic 1 keeps the router's score — got `0.3`, expected `0.3`

**Result: ✅ PASS**  (2 checks, 0 failed, 2 turns, 0.00s)

---

## B1 — needed page returns from L2 intact

> A returning topic's old page comes back from L2 with its content, and unrelated pages make way.

### Turn 1: "alpha topic question lorem ipsum dolor sit amet lorem ipsum "

- **Reply (assistant)**: alpha topic answer lorem ipsum dolor sit amet lorem ipsum do
- **Events in prepare_context**: `new topic 1`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🟢 open | `alpha topic question lorem ipsum dolo...` | - | - | `[0]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L1** | 1 | 30 | yes | alpha topic question lorem ipsum dolor sit amet... |

**L1 after prepare_context**: `[######......|.......|...................]` 15/100 tok (15%); `|` marks low 30% / high 50%; L1 pages `[0]`, L2 pages `[]`

**L1 after record_reply**: `[############|.......|...................]` 30/100 tok (30%); `|` marks low 30% / high 50%; L1 pages `[0]`, L2 pages `[]`

**Prompt sent to the model**

> **[USER]** alpha topic question lorem ipsum dolor sit amet lorem ipsum 

<details><summary>Page contents (final state)</summary>

- **L1 page 0** (topic 1, 30 tok, OPEN)
  - `user`: alpha topic question lorem ipsum dolor sit amet lorem ipsum 
  - `assistant`: alpha topic answer lorem ipsum dolor sit amet lorem ipsum do

</details>

### Turn 2: "beta lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum do"

- **Reply (assistant)**: lorem ipsum dolor si
- **Events in prepare_context**: `closed topic 1, card: answer / alpha / dolor`, `new topic 2`, `move page 0: L1 -> L2`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🔴 closed | `answer / alpha / dolor` | alpha topic question lorem ipsum dolor sit amet lorem ipsum  | answer, alpha, dolor, sit, lorem | `[0]` | 0 |
| 2 | 🟢 open | `beta lorem ipsum dolor sit amet lorem...` | - | - | `[1]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L2** | 1 | 30 |  | alpha topic question lorem ipsum dolor sit amet... |
| 1 | **L1** | 2 | 30 | yes | beta lorem ipsum dolor sit amet lorem ipsum dol... |

**L1 after prepare_context**: `[##########..|.......|...................]` 25/100 tok (25%); `|` marks low 30% / high 50%; L1 pages `[1]`, L2 pages `[0]`

**L1 after record_reply**: `[############|.......|...................]` 30/100 tok (30%); `|` marks low 30% / high 50%; L1 pages `[1]`, L2 pages `[0]`

**Prompt sent to the model**

> **[SYSTEM]** [earlier messages omitted]
> **[USER]** beta lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum do

<details><summary>Page contents (final state)</summary>

- **L1 page 1** (topic 2, 30 tok, OPEN)
  - `user`: beta lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet l...
  - `assistant`: lorem ipsum dolor si
- **L2 page 0** (topic 1, 30 tok)
  - `user`: alpha topic question lorem ipsum dolor sit amet lorem ipsum 
  - `assistant`: alpha topic answer lorem ipsum dolor sit amet lorem ipsum do

</details>

- ✅ setup: page 0 is in L2 after topic 2 filled L1 — got `'L2'`, expected `'L2'`
### Turn 3: "back to alpha lorem ipsum dolor sit amet"

- **Reply (assistant)**: lorem ipsum dolor sit amet lorem ipsum d
- **Events in prepare_context**: `closed topic 2, card: dolor / sit / lorem`, `return to topic 1 (answer / alpha / dolor)`, `move page 0: L2 -> L1`, `move page 1: L1 -> L2`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🟢 open | `answer / alpha / dolor` | alpha topic question lorem ipsum dolor sit amet lorem ipsum  | answer, alpha, dolor, sit, lorem | `[0, 2]` | 0 |
| 2 | 🔴 closed | `dolor / sit / lorem` | beta lorem ipsum dolor sit amet lorem ipsum dolor sit ame... | dolor, sit, lorem, amet, beta | `[1]` | 1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L1** | 1 | 30 |  | alpha topic question lorem ipsum dolor sit amet... |
| 1 | **L2** | 2 | 30 |  | beta lorem ipsum dolor sit amet lorem ipsum dol... |
| 2 | **L1** | 1 | 20 | yes | back to alpha lorem ipsum dolor sit amet |

**L1 after prepare_context**: `[############|###....|...................]` 40/100 tok (40%); `|` marks low 30% / high 50%; L1 pages `[0, 2]`, L2 pages `[1]`

**L1 after record_reply**: `[############|#######|...................]` 50/100 tok (50%); `|` marks low 30% / high 50%; L1 pages `[0, 2]`, L2 pages `[1]`

**Prompt sent to the model**

> **[USER]** alpha topic question lorem ipsum dolor sit amet lorem ipsum 
> **[ASSISTANT]** alpha topic answer lorem ipsum dolor sit amet lorem ipsum do
> **[SYSTEM]** [earlier messages omitted]
> **[USER]** back to alpha lorem ipsum dolor sit amet

<details><summary>Page contents (final state)</summary>

- **L1 page 0** (topic 1, 30 tok)
  - `user`: alpha topic question lorem ipsum dolor sit amet lorem ipsum 
  - `assistant`: alpha topic answer lorem ipsum dolor sit amet lorem ipsum do
- **L1 page 2** (topic 1, 20 tok, OPEN)
  - `user`: back to alpha lorem ipsum dolor sit amet
  - `assistant`: lorem ipsum dolor sit amet lorem ipsum d
- **L2 page 1** (topic 2, 30 tok)
  - `user`: beta lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet l...
  - `assistant`: lorem ipsum dolor si

</details>

- ✅ page 0 is back in L1 — got `'L1'`, expected `'L1'`
- ✅ its messages are identical to before — got `['alpha topic question lorem ipsum dolor sit amet lorem ipsum ', 'alpha topic answer lorem ipsum dolor sit amet lorem ipsum do']`, expected `['alpha topic question lorem ipsum dolor sit amet lorem ipsum ', 'alpha topic answer lorem ipsum dolor sit amet lorem ipsum do']`
- ✅ the old user message is in the prompt
- ✅ the unrelated topic-2 page was demoted to make room — got `'L2'`, expected `'L2'`
- ✅ a gap marker sits between old page 0 and the new page 2 (page 1 is missing) — got `2`, expected `2`
- ✅ topic 1 lists pages [0, 2] — got `[0, 2]`, expected `[0, 2]`

**Result: ✅ PASS**  (7 checks, 0 failed, 3 turns, 0.00s)

---

## B2 — newest pages first and skip when no room

> When a topic has two pages in L2 but room for one, the NEWEST comes back and the skip is logged.

### Turn 1: "a lorem ipsum dolor sit amet lorem ipsum"

- **Reply (assistant)**: lorem ipsum dolor sit amet lorem ipsum d
- **Events in prepare_context**: `new topic 1`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🟢 open | `a lorem ipsum dolor sit amet lorem ipsum` | - | - | `[0]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L1** | 1 | 20 | yes | a lorem ipsum dolor sit amet lorem ipsum |

**L1 after prepare_context**: `[#####.......|.......|...................]` 10/80 tok (12%); `|` marks low 30% / high 50%; L1 pages `[0]`, L2 pages `[]`

**L1 after record_reply**: `[##########..|.......|...................]` 20/80 tok (25%); `|` marks low 30% / high 50%; L1 pages `[0]`, L2 pages `[]`

**Prompt sent to the model**

> **[USER]** a lorem ipsum dolor sit amet lorem ipsum

<details><summary>Page contents (final state)</summary>

- **L1 page 0** (topic 1, 20 tok, OPEN)
  - `user`: a lorem ipsum dolor sit amet lorem ipsum
  - `assistant`: lorem ipsum dolor sit amet lorem ipsum d

</details>

### Turn 2: "b lorem ipsum dolor sit amet lorem ipsum"

- **Reply (assistant)**: lorem ipsum dolor sit amet lorem ipsum d
- **Events in prepare_context**: none
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🟢 open | `a lorem ipsum dolor sit amet lorem ipsum` | - | - | `[0, 1]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L1** | 1 | 20 |  | a lorem ipsum dolor sit amet lorem ipsum |
| 1 | **L1** | 1 | 20 | yes | b lorem ipsum dolor sit amet lorem ipsum |

**L1 after prepare_context**: `[############|##.....|...................]` 30/80 tok (38%); `|` marks low 30% / high 50%; L1 pages `[0, 1]`, L2 pages `[]`

**L1 after record_reply**: `[############|#######|...................]` 40/80 tok (50%); `|` marks low 30% / high 50%; L1 pages `[0, 1]`, L2 pages `[]`

**Prompt sent to the model**

> **[USER]** a lorem ipsum dolor sit amet lorem ipsum
> **[ASSISTANT]** lorem ipsum dolor sit amet lorem ipsum d
> **[USER]** b lorem ipsum dolor sit amet lorem ipsum

<details><summary>Page contents (final state)</summary>

- **L1 page 0** (topic 1, 20 tok)
  - `user`: a lorem ipsum dolor sit amet lorem ipsum
  - `assistant`: lorem ipsum dolor sit amet lorem ipsum d
- **L1 page 1** (topic 1, 20 tok, OPEN)
  - `user`: b lorem ipsum dolor sit amet lorem ipsum
  - `assistant`: lorem ipsum dolor sit amet lorem ipsum d

</details>

### Turn 3: "c lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit am..."

- **Reply (assistant)**: lorem ipsum dolor sit amet lorem ipsum d
- **Events in prepare_context**: `closed topic 1, card: dolor / sit / lorem`, `new topic 2`, `move page 0: L1 -> L2`, `move page 1: L1 -> L2`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🔴 closed | `dolor / sit / lorem` | a lorem ipsum dolor sit amet lorem ipsum; b lorem ipsum d... | dolor, sit, lorem, amet, ipsum | `[0, 1]` | 1 |
| 2 | 🟢 open | `c lorem ipsum dolor sit amet lorem ip...` | - | - | `[2]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L2** | 1 | 20 |  | a lorem ipsum dolor sit amet lorem ipsum |
| 1 | **L2** | 1 | 20 |  | b lorem ipsum dolor sit amet lorem ipsum |
| 2 | **L1** | 2 | 40 | yes | c lorem ipsum dolor sit amet lorem ipsum dolor ... |

**L1 after prepare_context**: `[############|##.....|...................]` 30/80 tok (38%); `|` marks low 30% / high 50%; L1 pages `[2]`, L2 pages `[0, 1]`

**L1 after record_reply**: `[############|#######|...................]` 40/80 tok (50%); `|` marks low 30% / high 50%; L1 pages `[2]`, L2 pages `[0, 1]`

**Prompt sent to the model**

> **[SYSTEM]** [earlier messages omitted]
> **[USER]** c lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsu

<details><summary>Page contents (final state)</summary>

- **L1 page 2** (topic 2, 40 tok, OPEN)
  - `user`: c lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lore...
  - `assistant`: lorem ipsum dolor sit amet lorem ipsum d
- **L2 page 0** (topic 1, 20 tok)
  - `user`: a lorem ipsum dolor sit amet lorem ipsum
  - `assistant`: lorem ipsum dolor sit amet lorem ipsum d
- **L2 page 1** (topic 1, 20 tok)
  - `user`: b lorem ipsum dolor sit amet lorem ipsum
  - `assistant`: lorem ipsum dolor sit amet lorem ipsum d

</details>

- ✅ setup: both pages of topic 1 are in L2 — got `('L2', 'L2')`, expected `('L2', 'L2')`
### Turn 4: "d lorem ipsum dolor sit amet lorem ipsum"

- **Reply (assistant)**: lorem ipsum dolor si
- **Events in prepare_context**: `closed topic 2, card: dolor / ipsu / sit`, `return to topic 1 (dolor / sit / lorem)`, `move page 1: L2 -> L1`, `no room for page 0 of topic 1`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🟢 open | `dolor / sit / lorem` | a lorem ipsum dolor sit amet lorem ipsum; b lorem ipsum d... | dolor, sit, lorem, amet, ipsum | `[0, 1, 3]` | 1 |
| 2 | 🔴 closed | `dolor / ipsu / sit` | c lorem ipsum dolor sit amet lorem ipsum dolor sit amet l... | dolor, ipsu, sit, lorem, amet | `[2]` | 2 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L2** | 1 | 20 |  | a lorem ipsum dolor sit amet lorem ipsum |
| 1 | **L1** | 1 | 20 |  | b lorem ipsum dolor sit amet lorem ipsum |
| 2 | **L1** | 2 | 40 |  | c lorem ipsum dolor sit amet lorem ipsum dolor ... |
| 3 | **L1** | 1 | 15 | yes | d lorem ipsum dolor sit amet lorem ipsum |

**L1 after prepare_context**: `[############|#######|##############.....]` 70/80 tok (88%); `|` marks low 30% / high 50%; L1 pages `[1, 2, 3]`, L2 pages `[0]`

**L1 after record_reply**: `[############|#######|#################..]` 75/80 tok (94%); `|` marks low 30% / high 50%; L1 pages `[1, 2, 3]`, L2 pages `[0]`

**Prompt sent to the model**

> **[SYSTEM]** [earlier messages omitted]
> **[USER]** b lorem ipsum dolor sit amet lorem ipsum
> **[ASSISTANT]** lorem ipsum dolor sit amet lorem ipsum d
> **[USER]** c lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsu
> **[ASSISTANT]** lorem ipsum dolor sit amet lorem ipsum d
> **[USER]** d lorem ipsum dolor sit amet lorem ipsum

<details><summary>Page contents (final state)</summary>

- **L1 page 1** (topic 1, 20 tok)
  - `user`: b lorem ipsum dolor sit amet lorem ipsum
  - `assistant`: lorem ipsum dolor sit amet lorem ipsum d
- **L1 page 2** (topic 2, 40 tok)
  - `user`: c lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lore...
  - `assistant`: lorem ipsum dolor sit amet lorem ipsum d
- **L1 page 3** (topic 1, 15 tok, OPEN)
  - `user`: d lorem ipsum dolor sit amet lorem ipsum
  - `assistant`: lorem ipsum dolor si
- **L2 page 0** (topic 1, 20 tok)
  - `user`: a lorem ipsum dolor sit amet lorem ipsum
  - `assistant`: lorem ipsum dolor sit amet lorem ipsum d

</details>

- ✅ the newer page 1 came back — got `'L1'`, expected `'L1'`
- ✅ the older page 0 did not fit and stays in L2 — got `'L2'`, expected `'L2'`
- ✅ a 'no room for page 0 of topic 1' event was logged
- ✅ topic 2's page (score 1.0) was not evicted to make room — got `'L1'`, expected `'L1'`

**Result: ✅ PASS**  (5 checks, 0 failed, 4 turns, 0.00s)

---

## B3 — page too big to fit is skipped safely

> A needed page that cannot fit even after making room stays in L2 and nothing crashes.

### Turn 1: "big lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit ..."

- **Reply (assistant)**: lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet...
- **Events in prepare_context**: `new topic 1`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🟢 open | `big lorem ipsum dolor sit amet lorem ...` | - | - | `[0]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L1** | 1 | 60 | yes | big lorem ipsum dolor sit amet lorem ipsum dolo... |

**L1 after prepare_context**: `[############|.......|...................]` 30/100 tok (30%); `|` marks low 30% / high 50%; L1 pages `[0]`, L2 pages `[]`

**L1 after record_reply**: `[############|#######|###................]` 60/100 tok (60%); `|` marks low 30% / high 50%; L1 pages `[0]`, L2 pages `[]`

**Prompt sent to the model**

> **[USER]** big lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ip

<details><summary>Page contents (final state)</summary>

- **L1 page 0** (topic 1, 60 tok, OPEN)
  - `user`: big lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lo...
  - `assistant`: lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ...

</details>

### Turn 2: "topic two lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolo..."

- **Reply (assistant)**: lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet
- **Events in prepare_context**: `closed topic 1, card: dolor / sit / lorem`, `new topic 2`, `move page 0: L1 -> L2`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🔴 closed | `dolor / sit / lorem` | big lorem ipsum dolor sit amet lorem ipsum dolor sit amet... | dolor, sit, lorem, amet, big | `[0]` | 0 |
| 2 | 🟢 open | `topic two lorem ipsum dolor sit amet ...` | - | - | `[1]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L2** | 1 | 60 |  | big lorem ipsum dolor sit amet lorem ipsum dolo... |
| 1 | **L1** | 2 | 50 | yes | topic two lorem ipsum dolor sit amet lorem ipsu... |

**L1 after prepare_context**: `[############|.......|...................]` 30/100 tok (30%); `|` marks low 30% / high 50%; L1 pages `[1]`, L2 pages `[0]`

**L1 after record_reply**: `[############|#######|...................]` 50/100 tok (50%); `|` marks low 30% / high 50%; L1 pages `[1]`, L2 pages `[0]`

**Prompt sent to the model**

> **[SYSTEM]** [earlier messages omitted]
> **[USER]** topic two lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lo

<details><summary>Page contents (final state)</summary>

- **L1 page 1** (topic 2, 50 tok, OPEN)
  - `user`: topic two lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit a...
  - `assistant`: lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet
- **L2 page 0** (topic 1, 60 tok)
  - `user`: big lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lo...
  - `assistant`: lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ...

</details>

- ✅ setup: the 60-token page 0 is in L2 — got `'L2'`, expected `'L2'`
### Turn 3: "more lorem ipsum dol"

- **Reply (assistant)**: lorem ipsum dolor si
- **Events in prepare_context**: `no room for page 0 of topic 1`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🔴 closed | `dolor / sit / lorem` | big lorem ipsum dolor sit amet lorem ipsum dolor sit amet... | dolor, sit, lorem, amet, big | `[0]` | 0 |
| 2 | 🟢 open | `topic two lorem ipsum dolor sit amet ...` | - | - | `[1]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L2** | 1 | 60 |  | big lorem ipsum dolor sit amet lorem ipsum dolo... |
| 1 | **L1** | 2 | 60 | yes | topic two lorem ipsum dolor sit amet lorem ipsu... |

**L1 after prepare_context**: `[############|#######|#..................]` 55/100 tok (55%); `|` marks low 30% / high 50%; L1 pages `[1]`, L2 pages `[0]`

**L1 after record_reply**: `[############|#######|###................]` 60/100 tok (60%); `|` marks low 30% / high 50%; L1 pages `[1]`, L2 pages `[0]`

**Prompt sent to the model**

> **[SYSTEM]** [earlier messages omitted]
> **[USER]** topic two lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lo
> **[ASSISTANT]** lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet
> **[USER]** more lorem ipsum dol

<details><summary>Page contents (final state)</summary>

- **L1 page 1** (topic 2, 60 tok, OPEN)
  - `user`: topic two lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit a...
  - `assistant`: lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet
  - `user`: more lorem ipsum dol
  - `assistant`: lorem ipsum dolor si
- **L2 page 0** (topic 1, 60 tok)
  - `user`: big lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lo...
  - `assistant`: lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ...

</details>

- ✅ page 0 (score 0.9) could not fit and remains in L2 — got `'L2'`, expected `'L2'`
- ✅ the skip was logged
- ✅ the open page is untouched

**Result: ✅ PASS**  (4 checks, 0 failed, 3 turns, 0.00s)

---

## B4 — needed page already in L1 is not moved

> Pages that are already in L1 are never moved just because their topic is needed.

### Turn 1: "one lorem ipsum dolor sit amet lorem ips"

- **Reply (assistant)**: lorem ipsum dolor si
- **Events in prepare_context**: `new topic 1`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🟢 open | `one lorem ipsum dolor sit amet lorem ips` | - | - | `[0]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L1** | 1 | 15 | yes | one lorem ipsum dolor sit amet lorem ips |

**L1 after prepare_context**: `[#...........................|.....|.....]` 10/500 tok (2%); `|` marks low 70% / high 85%; L1 pages `[0]`, L2 pages `[]`

**L1 after record_reply**: `[#...........................|.....|.....]` 15/500 tok (3%); `|` marks low 70% / high 85%; L1 pages `[0]`, L2 pages `[]`

**Prompt sent to the model**

> **[USER]** one lorem ipsum dolor sit amet lorem ips

<details><summary>Page contents (final state)</summary>

- **L1 page 0** (topic 1, 15 tok, OPEN)
  - `user`: one lorem ipsum dolor sit amet lorem ips
  - `assistant`: lorem ipsum dolor si

</details>

### Turn 2: "two lorem ipsum dolor sit amet lorem ips"

- **Reply (assistant)**: lorem ipsum dolor si
- **Events in prepare_context**: `closed topic 1, card: one / ips / dolor`, `new topic 2`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🔴 closed | `one / ips / dolor` | one lorem ipsum dolor sit amet lorem ips | one, ips, dolor, sit, lorem | `[0]` | 0 |
| 2 | 🟢 open | `two lorem ipsum dolor sit amet lorem ips` | - | - | `[1]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L1** | 1 | 15 |  | one lorem ipsum dolor sit amet lorem ips |
| 1 | **L1** | 2 | 15 | yes | two lorem ipsum dolor sit amet lorem ips |

**L1 after prepare_context**: `[##..........................|.....|.....]` 25/500 tok (5%); `|` marks low 70% / high 85%; L1 pages `[0, 1]`, L2 pages `[]`

**L1 after record_reply**: `[##..........................|.....|.....]` 30/500 tok (6%); `|` marks low 70% / high 85%; L1 pages `[0, 1]`, L2 pages `[]`

**Prompt sent to the model**

> **[USER]** one lorem ipsum dolor sit amet lorem ips
> **[ASSISTANT]** lorem ipsum dolor si
> **[USER]** two lorem ipsum dolor sit amet lorem ips

<details><summary>Page contents (final state)</summary>

- **L1 page 0** (topic 1, 15 tok)
  - `user`: one lorem ipsum dolor sit amet lorem ips
  - `assistant`: lorem ipsum dolor si
- **L1 page 1** (topic 2, 15 tok, OPEN)
  - `user`: two lorem ipsum dolor sit amet lorem ips
  - `assistant`: lorem ipsum dolor si

</details>

### Turn 3: "back to one lorem ipsum dolor sit amet l"

- **Reply (assistant)**: lorem ipsum dolor si
- **Events in prepare_context**: `closed topic 2, card: two / ips / dolor`, `return to topic 1 (one / ips / dolor)`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🟢 open | `one / ips / dolor` | one lorem ipsum dolor sit amet lorem ips | one, ips, dolor, sit, lorem | `[0, 2]` | 0 |
| 2 | 🔴 closed | `two / ips / dolor` | two lorem ipsum dolor sit amet lorem ips | two, ips, dolor, sit, lorem | `[1]` | 1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L1** | 1 | 15 |  | one lorem ipsum dolor sit amet lorem ips |
| 1 | **L1** | 2 | 15 |  | two lorem ipsum dolor sit amet lorem ips |
| 2 | **L1** | 1 | 15 | yes | back to one lorem ipsum dolor sit amet l |

**L1 after prepare_context**: `[###.........................|.....|.....]` 40/500 tok (8%); `|` marks low 70% / high 85%; L1 pages `[0, 1, 2]`, L2 pages `[]`

**L1 after record_reply**: `[####........................|.....|.....]` 45/500 tok (9%); `|` marks low 70% / high 85%; L1 pages `[0, 1, 2]`, L2 pages `[]`

**Prompt sent to the model**

> **[USER]** one lorem ipsum dolor sit amet lorem ips
> **[ASSISTANT]** lorem ipsum dolor si
> **[USER]** two lorem ipsum dolor sit amet lorem ips
> **[ASSISTANT]** lorem ipsum dolor si
> **[USER]** back to one lorem ipsum dolor sit amet l

<details><summary>Page contents (final state)</summary>

- **L1 page 0** (topic 1, 15 tok)
  - `user`: one lorem ipsum dolor sit amet lorem ips
  - `assistant`: lorem ipsum dolor si
- **L1 page 1** (topic 2, 15 tok)
  - `user`: two lorem ipsum dolor sit amet lorem ips
  - `assistant`: lorem ipsum dolor si
- **L1 page 2** (topic 1, 15 tok, OPEN)
  - `user`: back to one lorem ipsum dolor sit amet l
  - `assistant`: lorem ipsum dolor si

</details>

- ✅ no page moved on the return turn — got `[]`, expected `[]`
- ✅ all three pages are still in L1 — got `[0, 1, 2]`, expected `[0, 1, 2]`

**Result: ✅ PASS**  (2 checks, 0 failed, 3 turns, 0.00s)

---

## P1 — no demotion at or below high water

> Nothing is demoted while L1 is at or under the high-water mark.

### Turn 1: "t1 lorem ipsum dolor sit amet lo"

- **Reply (assistant)**: lorem ipsum dolor sit amet lorem
- **Events in prepare_context**: `new topic 1`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🟢 open | `t1 lorem ipsum dolor sit amet lo` | - | - | `[0]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L1** | 1 | 16 | yes | t1 lorem ipsum dolor sit amet lo |

**L1 after prepare_context**: `[###.................|.............|.....]` 8/100 tok (8%); `|` marks low 50% / high 85%; L1 pages `[0]`, L2 pages `[]`

**L1 after record_reply**: `[######..............|.............|.....]` 16/100 tok (16%); `|` marks low 50% / high 85%; L1 pages `[0]`, L2 pages `[]`

**Prompt sent to the model**

> **[USER]** t1 lorem ipsum dolor sit amet lo

<details><summary>Page contents (final state)</summary>

- **L1 page 0** (topic 1, 16 tok, OPEN)
  - `user`: t1 lorem ipsum dolor sit amet lo
  - `assistant`: lorem ipsum dolor sit amet lorem

</details>

- ✅ turn 1: 16% used, no page moved
### Turn 2: "t2 lorem ipsum dolor sit amet lo"

- **Reply (assistant)**: lorem ipsum dolor sit amet lorem
- **Events in prepare_context**: `closed topic 1, card: dolor / sit / lorem`, `new topic 2`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🔴 closed | `dolor / sit / lorem` | t1 lorem ipsum dolor sit amet lo | dolor, sit, lorem, amet, ipsum | `[0]` | 0 |
| 2 | 🟢 open | `t2 lorem ipsum dolor sit amet lo` | - | - | `[1]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L1** | 1 | 16 |  | t1 lorem ipsum dolor sit amet lo |
| 1 | **L1** | 2 | 16 | yes | t2 lorem ipsum dolor sit amet lo |

**L1 after prepare_context**: `[##########..........|.............|.....]` 24/100 tok (24%); `|` marks low 50% / high 85%; L1 pages `[0, 1]`, L2 pages `[]`

**L1 after record_reply**: `[#############.......|.............|.....]` 32/100 tok (32%); `|` marks low 50% / high 85%; L1 pages `[0, 1]`, L2 pages `[]`

**Prompt sent to the model**

> **[USER]** t1 lorem ipsum dolor sit amet lo
> **[ASSISTANT]** lorem ipsum dolor sit amet lorem
> **[USER]** t2 lorem ipsum dolor sit amet lo

<details><summary>Page contents (final state)</summary>

- **L1 page 0** (topic 1, 16 tok)
  - `user`: t1 lorem ipsum dolor sit amet lo
  - `assistant`: lorem ipsum dolor sit amet lorem
- **L1 page 1** (topic 2, 16 tok, OPEN)
  - `user`: t2 lorem ipsum dolor sit amet lo
  - `assistant`: lorem ipsum dolor sit amet lorem

</details>

- ✅ turn 2: 32% used, no page moved
### Turn 3: "t3 lorem ipsum dolor sit amet lo"

- **Reply (assistant)**: lorem ipsum dolor sit amet lorem
- **Events in prepare_context**: `closed topic 2, card: dolor / sit / lorem`, `new topic 3`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🔴 closed | `dolor / sit / lorem` | t1 lorem ipsum dolor sit amet lo | dolor, sit, lorem, amet, ipsum | `[0]` | 0 |
| 2 | 🔴 closed | `dolor / sit / lorem` | t2 lorem ipsum dolor sit amet lo | dolor, sit, lorem, amet, ipsum | `[1]` | 1 |
| 3 | 🟢 open | `t3 lorem ipsum dolor sit amet lo` | - | - | `[2]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L1** | 1 | 16 |  | t1 lorem ipsum dolor sit amet lo |
| 1 | **L1** | 2 | 16 |  | t2 lorem ipsum dolor sit amet lo |
| 2 | **L1** | 3 | 16 | yes | t3 lorem ipsum dolor sit amet lo |

**L1 after prepare_context**: `[################....|.............|.....]` 40/100 tok (40%); `|` marks low 50% / high 85%; L1 pages `[0, 1, 2]`, L2 pages `[]`

**L1 after record_reply**: `[###################.|.............|.....]` 48/100 tok (48%); `|` marks low 50% / high 85%; L1 pages `[0, 1, 2]`, L2 pages `[]`

**Prompt sent to the model**

> **[USER]** t1 lorem ipsum dolor sit amet lo
> **[ASSISTANT]** lorem ipsum dolor sit amet lorem
> **[USER]** t2 lorem ipsum dolor sit amet lo
> **[ASSISTANT]** lorem ipsum dolor sit amet lorem
> **[USER]** t3 lorem ipsum dolor sit amet lo

<details><summary>Page contents (final state)</summary>

- **L1 page 0** (topic 1, 16 tok)
  - `user`: t1 lorem ipsum dolor sit amet lo
  - `assistant`: lorem ipsum dolor sit amet lorem
- **L1 page 1** (topic 2, 16 tok)
  - `user`: t2 lorem ipsum dolor sit amet lo
  - `assistant`: lorem ipsum dolor sit amet lorem
- **L1 page 2** (topic 3, 16 tok, OPEN)
  - `user`: t3 lorem ipsum dolor sit amet lo
  - `assistant`: lorem ipsum dolor sit amet lorem

</details>

- ✅ turn 3: 48% used, no page moved
### Turn 4: "t4 lorem ipsum dolor sit amet lo"

- **Reply (assistant)**: lorem ipsum dolor sit amet lorem
- **Events in prepare_context**: `closed topic 3, card: dolor / sit / lorem`, `new topic 4`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🔴 closed | `dolor / sit / lorem` | t1 lorem ipsum dolor sit amet lo | dolor, sit, lorem, amet, ipsum | `[0]` | 0 |
| 2 | 🔴 closed | `dolor / sit / lorem` | t2 lorem ipsum dolor sit amet lo | dolor, sit, lorem, amet, ipsum | `[1]` | 1 |
| 3 | 🔴 closed | `dolor / sit / lorem` | t3 lorem ipsum dolor sit amet lo | dolor, sit, lorem, amet, ipsum | `[2]` | 2 |
| 4 | 🟢 open | `t4 lorem ipsum dolor sit amet lo` | - | - | `[3]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L1** | 1 | 16 |  | t1 lorem ipsum dolor sit amet lo |
| 1 | **L1** | 2 | 16 |  | t2 lorem ipsum dolor sit amet lo |
| 2 | **L1** | 3 | 16 |  | t3 lorem ipsum dolor sit amet lo |
| 3 | **L1** | 4 | 16 | yes | t4 lorem ipsum dolor sit amet lo |

**L1 after prepare_context**: `[####################|#............|.....]` 56/100 tok (56%); `|` marks low 50% / high 85%; L1 pages `[0, 1, 2, 3]`, L2 pages `[]`

**L1 after record_reply**: `[####################|#####........|.....]` 64/100 tok (64%); `|` marks low 50% / high 85%; L1 pages `[0, 1, 2, 3]`, L2 pages `[]`

**Prompt sent to the model**

> **[USER]** t1 lorem ipsum dolor sit amet lo
> **[ASSISTANT]** lorem ipsum dolor sit amet lorem
> **[USER]** t2 lorem ipsum dolor sit amet lo
> **[ASSISTANT]** lorem ipsum dolor sit amet lorem
> **[USER]** t3 lorem ipsum dolor sit amet lo
> **[ASSISTANT]** lorem ipsum dolor sit amet lorem
> **[USER]** t4 lorem ipsum dolor sit amet lo

<details><summary>Page contents (final state)</summary>

- **L1 page 0** (topic 1, 16 tok)
  - `user`: t1 lorem ipsum dolor sit amet lo
  - `assistant`: lorem ipsum dolor sit amet lorem
- **L1 page 1** (topic 2, 16 tok)
  - `user`: t2 lorem ipsum dolor sit amet lo
  - `assistant`: lorem ipsum dolor sit amet lorem
- **L1 page 2** (topic 3, 16 tok)
  - `user`: t3 lorem ipsum dolor sit amet lo
  - `assistant`: lorem ipsum dolor sit amet lorem
- **L1 page 3** (topic 4, 16 tok, OPEN)
  - `user`: t4 lorem ipsum dolor sit amet lo
  - `assistant`: lorem ipsum dolor sit amet lorem

</details>

- ✅ turn 4: 64% used, no page moved
### Turn 5: "t5 lorem ipsum dolor sit amet lo"

- **Reply (assistant)**: lorem ipsum dolor sit amet lorem
- **Events in prepare_context**: `closed topic 4, card: dolor / sit / lorem`, `new topic 5`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🔴 closed | `dolor / sit / lorem` | t1 lorem ipsum dolor sit amet lo | dolor, sit, lorem, amet, ipsum | `[0]` | 0 |
| 2 | 🔴 closed | `dolor / sit / lorem` | t2 lorem ipsum dolor sit amet lo | dolor, sit, lorem, amet, ipsum | `[1]` | 1 |
| 3 | 🔴 closed | `dolor / sit / lorem` | t3 lorem ipsum dolor sit amet lo | dolor, sit, lorem, amet, ipsum | `[2]` | 2 |
| 4 | 🔴 closed | `dolor / sit / lorem` | t4 lorem ipsum dolor sit amet lo | dolor, sit, lorem, amet, ipsum | `[3]` | 3 |
| 5 | 🟢 open | `t5 lorem ipsum dolor sit amet lo` | - | - | `[4]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L1** | 1 | 16 |  | t1 lorem ipsum dolor sit amet lo |
| 1 | **L1** | 2 | 16 |  | t2 lorem ipsum dolor sit amet lo |
| 2 | **L1** | 3 | 16 |  | t3 lorem ipsum dolor sit amet lo |
| 3 | **L1** | 4 | 16 |  | t4 lorem ipsum dolor sit amet lo |
| 4 | **L1** | 5 | 16 | yes | t5 lorem ipsum dolor sit amet lo |

**L1 after prepare_context**: `[####################|########.....|.....]` 72/100 tok (72%); `|` marks low 50% / high 85%; L1 pages `[0, 1, 2, 3, 4]`, L2 pages `[]`

**L1 after record_reply**: `[####################|###########..|.....]` 80/100 tok (80%); `|` marks low 50% / high 85%; L1 pages `[0, 1, 2, 3, 4]`, L2 pages `[]`

**Prompt sent to the model**

> **[USER]** t1 lorem ipsum dolor sit amet lo
> **[ASSISTANT]** lorem ipsum dolor sit amet lorem
> **[USER]** t2 lorem ipsum dolor sit amet lo
> **[ASSISTANT]** lorem ipsum dolor sit amet lorem
> **[USER]** t3 lorem ipsum dolor sit amet lo
> **[ASSISTANT]** lorem ipsum dolor sit amet lorem
> **[USER]** t4 lorem ipsum dolor sit amet lo
> **[ASSISTANT]** lorem ipsum dolor sit amet lorem
> **[USER]** t5 lorem ipsum dolor sit amet lo

<details><summary>Page contents (final state)</summary>

- **L1 page 0** (topic 1, 16 tok)
  - `user`: t1 lorem ipsum dolor sit amet lo
  - `assistant`: lorem ipsum dolor sit amet lorem
- **L1 page 1** (topic 2, 16 tok)
  - `user`: t2 lorem ipsum dolor sit amet lo
  - `assistant`: lorem ipsum dolor sit amet lorem
- **L1 page 2** (topic 3, 16 tok)
  - `user`: t3 lorem ipsum dolor sit amet lo
  - `assistant`: lorem ipsum dolor sit amet lorem
- **L1 page 3** (topic 4, 16 tok)
  - `user`: t4 lorem ipsum dolor sit amet lo
  - `assistant`: lorem ipsum dolor sit amet lorem
- **L1 page 4** (topic 5, 16 tok, OPEN)
  - `user`: t5 lorem ipsum dolor sit amet lo
  - `assistant`: lorem ipsum dolor sit amet lorem

</details>

- ✅ turn 5: 80% used, no page moved
- ✅ L2 is still empty — got `0`, expected `0`

**Result: ✅ PASS**  (6 checks, 0 failed, 5 turns, 0.00s)

---

## P2 — demotion continues down to low water and stops

> Above high-water the manager demotes oldest-first until at or below low-water, then stops.

### Turn 1 [fill]: "t1 lorem ipsum dolor sit amet lo"

- **Reply (assistant)**: lorem ipsum dolor sit amet lorem
- **Events in prepare_context**: `new topic 1`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🟢 open | `t1 lorem ipsum dolor sit amet lo` | - | - | `[0]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L1** | 1 | 16 | yes | t1 lorem ipsum dolor sit amet lo |

**L1 after prepare_context**: `[###.................|.............|.....]` 8/100 tok (8%); `|` marks low 50% / high 85%; L1 pages `[0]`, L2 pages `[]`

**L1 after record_reply**: `[######..............|.............|.....]` 16/100 tok (16%); `|` marks low 50% / high 85%; L1 pages `[0]`, L2 pages `[]`

**Prompt sent to the model**

> **[USER]** t1 lorem ipsum dolor sit amet lo

<details><summary>Page contents (final state)</summary>

- **L1 page 0** (topic 1, 16 tok, OPEN)
  - `user`: t1 lorem ipsum dolor sit amet lo
  - `assistant`: lorem ipsum dolor sit amet lorem

</details>

- ✅ [fill] turn 1: no demotion while at or under high-water (16%) — got `[]`, expected `[]`
### Turn 2 [fill]: "t2 lorem ipsum dolor sit amet lo"

- **Reply (assistant)**: lorem ipsum dolor sit amet lorem
- **Events in prepare_context**: `closed topic 1, card: dolor / sit / lorem`, `new topic 2`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🔴 closed | `dolor / sit / lorem` | t1 lorem ipsum dolor sit amet lo | dolor, sit, lorem, amet, ipsum | `[0]` | 0 |
| 2 | 🟢 open | `t2 lorem ipsum dolor sit amet lo` | - | - | `[1]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L1** | 1 | 16 |  | t1 lorem ipsum dolor sit amet lo |
| 1 | **L1** | 2 | 16 | yes | t2 lorem ipsum dolor sit amet lo |

**L1 after prepare_context**: `[##########..........|.............|.....]` 24/100 tok (24%); `|` marks low 50% / high 85%; L1 pages `[0, 1]`, L2 pages `[]`

**L1 after record_reply**: `[#############.......|.............|.....]` 32/100 tok (32%); `|` marks low 50% / high 85%; L1 pages `[0, 1]`, L2 pages `[]`

**Prompt sent to the model**

> **[USER]** t1 lorem ipsum dolor sit amet lo
> **[ASSISTANT]** lorem ipsum dolor sit amet lorem
> **[USER]** t2 lorem ipsum dolor sit amet lo

<details><summary>Page contents (final state)</summary>

- **L1 page 0** (topic 1, 16 tok)
  - `user`: t1 lorem ipsum dolor sit amet lo
  - `assistant`: lorem ipsum dolor sit amet lorem
- **L1 page 1** (topic 2, 16 tok, OPEN)
  - `user`: t2 lorem ipsum dolor sit amet lo
  - `assistant`: lorem ipsum dolor sit amet lorem

</details>

- ✅ [fill] turn 2: no demotion while at or under high-water (32%) — got `[]`, expected `[]`
### Turn 3 [fill]: "t3 lorem ipsum dolor sit amet lo"

- **Reply (assistant)**: lorem ipsum dolor sit amet lorem
- **Events in prepare_context**: `closed topic 2, card: dolor / sit / lorem`, `new topic 3`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🔴 closed | `dolor / sit / lorem` | t1 lorem ipsum dolor sit amet lo | dolor, sit, lorem, amet, ipsum | `[0]` | 0 |
| 2 | 🔴 closed | `dolor / sit / lorem` | t2 lorem ipsum dolor sit amet lo | dolor, sit, lorem, amet, ipsum | `[1]` | 1 |
| 3 | 🟢 open | `t3 lorem ipsum dolor sit amet lo` | - | - | `[2]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L1** | 1 | 16 |  | t1 lorem ipsum dolor sit amet lo |
| 1 | **L1** | 2 | 16 |  | t2 lorem ipsum dolor sit amet lo |
| 2 | **L1** | 3 | 16 | yes | t3 lorem ipsum dolor sit amet lo |

**L1 after prepare_context**: `[################....|.............|.....]` 40/100 tok (40%); `|` marks low 50% / high 85%; L1 pages `[0, 1, 2]`, L2 pages `[]`

**L1 after record_reply**: `[###################.|.............|.....]` 48/100 tok (48%); `|` marks low 50% / high 85%; L1 pages `[0, 1, 2]`, L2 pages `[]`

**Prompt sent to the model**

> **[USER]** t1 lorem ipsum dolor sit amet lo
> **[ASSISTANT]** lorem ipsum dolor sit amet lorem
> **[USER]** t2 lorem ipsum dolor sit amet lo
> **[ASSISTANT]** lorem ipsum dolor sit amet lorem
> **[USER]** t3 lorem ipsum dolor sit amet lo

<details><summary>Page contents (final state)</summary>

- **L1 page 0** (topic 1, 16 tok)
  - `user`: t1 lorem ipsum dolor sit amet lo
  - `assistant`: lorem ipsum dolor sit amet lorem
- **L1 page 1** (topic 2, 16 tok)
  - `user`: t2 lorem ipsum dolor sit amet lo
  - `assistant`: lorem ipsum dolor sit amet lorem
- **L1 page 2** (topic 3, 16 tok, OPEN)
  - `user`: t3 lorem ipsum dolor sit amet lo
  - `assistant`: lorem ipsum dolor sit amet lorem

</details>

- ✅ [fill] turn 3: no demotion while at or under high-water (48%) — got `[]`, expected `[]`
### Turn 4 [fill]: "t4 lorem ipsum dolor sit amet lo"

- **Reply (assistant)**: lorem ipsum dolor sit amet lorem
- **Events in prepare_context**: `closed topic 3, card: dolor / sit / lorem`, `new topic 4`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🔴 closed | `dolor / sit / lorem` | t1 lorem ipsum dolor sit amet lo | dolor, sit, lorem, amet, ipsum | `[0]` | 0 |
| 2 | 🔴 closed | `dolor / sit / lorem` | t2 lorem ipsum dolor sit amet lo | dolor, sit, lorem, amet, ipsum | `[1]` | 1 |
| 3 | 🔴 closed | `dolor / sit / lorem` | t3 lorem ipsum dolor sit amet lo | dolor, sit, lorem, amet, ipsum | `[2]` | 2 |
| 4 | 🟢 open | `t4 lorem ipsum dolor sit amet lo` | - | - | `[3]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L1** | 1 | 16 |  | t1 lorem ipsum dolor sit amet lo |
| 1 | **L1** | 2 | 16 |  | t2 lorem ipsum dolor sit amet lo |
| 2 | **L1** | 3 | 16 |  | t3 lorem ipsum dolor sit amet lo |
| 3 | **L1** | 4 | 16 | yes | t4 lorem ipsum dolor sit amet lo |

**L1 after prepare_context**: `[####################|#............|.....]` 56/100 tok (56%); `|` marks low 50% / high 85%; L1 pages `[0, 1, 2, 3]`, L2 pages `[]`

**L1 after record_reply**: `[####################|#####........|.....]` 64/100 tok (64%); `|` marks low 50% / high 85%; L1 pages `[0, 1, 2, 3]`, L2 pages `[]`

**Prompt sent to the model**

> **[USER]** t1 lorem ipsum dolor sit amet lo
> **[ASSISTANT]** lorem ipsum dolor sit amet lorem
> **[USER]** t2 lorem ipsum dolor sit amet lo
> **[ASSISTANT]** lorem ipsum dolor sit amet lorem
> **[USER]** t3 lorem ipsum dolor sit amet lo
> **[ASSISTANT]** lorem ipsum dolor sit amet lorem
> **[USER]** t4 lorem ipsum dolor sit amet lo

<details><summary>Page contents (final state)</summary>

- **L1 page 0** (topic 1, 16 tok)
  - `user`: t1 lorem ipsum dolor sit amet lo
  - `assistant`: lorem ipsum dolor sit amet lorem
- **L1 page 1** (topic 2, 16 tok)
  - `user`: t2 lorem ipsum dolor sit amet lo
  - `assistant`: lorem ipsum dolor sit amet lorem
- **L1 page 2** (topic 3, 16 tok)
  - `user`: t3 lorem ipsum dolor sit amet lo
  - `assistant`: lorem ipsum dolor sit amet lorem
- **L1 page 3** (topic 4, 16 tok, OPEN)
  - `user`: t4 lorem ipsum dolor sit amet lo
  - `assistant`: lorem ipsum dolor sit amet lorem

</details>

- ✅ [fill] turn 4: no demotion while at or under high-water (64%) — got `[]`, expected `[]`
### Turn 5 [fill]: "t5 lorem ipsum dolor sit amet lo"

- **Reply (assistant)**: lorem ipsum dolor sit amet lorem
- **Events in prepare_context**: `closed topic 4, card: dolor / sit / lorem`, `new topic 5`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🔴 closed | `dolor / sit / lorem` | t1 lorem ipsum dolor sit amet lo | dolor, sit, lorem, amet, ipsum | `[0]` | 0 |
| 2 | 🔴 closed | `dolor / sit / lorem` | t2 lorem ipsum dolor sit amet lo | dolor, sit, lorem, amet, ipsum | `[1]` | 1 |
| 3 | 🔴 closed | `dolor / sit / lorem` | t3 lorem ipsum dolor sit amet lo | dolor, sit, lorem, amet, ipsum | `[2]` | 2 |
| 4 | 🔴 closed | `dolor / sit / lorem` | t4 lorem ipsum dolor sit amet lo | dolor, sit, lorem, amet, ipsum | `[3]` | 3 |
| 5 | 🟢 open | `t5 lorem ipsum dolor sit amet lo` | - | - | `[4]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L1** | 1 | 16 |  | t1 lorem ipsum dolor sit amet lo |
| 1 | **L1** | 2 | 16 |  | t2 lorem ipsum dolor sit amet lo |
| 2 | **L1** | 3 | 16 |  | t3 lorem ipsum dolor sit amet lo |
| 3 | **L1** | 4 | 16 |  | t4 lorem ipsum dolor sit amet lo |
| 4 | **L1** | 5 | 16 | yes | t5 lorem ipsum dolor sit amet lo |

**L1 after prepare_context**: `[####################|########.....|.....]` 72/100 tok (72%); `|` marks low 50% / high 85%; L1 pages `[0, 1, 2, 3, 4]`, L2 pages `[]`

**L1 after record_reply**: `[####################|###########..|.....]` 80/100 tok (80%); `|` marks low 50% / high 85%; L1 pages `[0, 1, 2, 3, 4]`, L2 pages `[]`

**Prompt sent to the model**

> **[USER]** t1 lorem ipsum dolor sit amet lo
> **[ASSISTANT]** lorem ipsum dolor sit amet lorem
> **[USER]** t2 lorem ipsum dolor sit amet lo
> **[ASSISTANT]** lorem ipsum dolor sit amet lorem
> **[USER]** t3 lorem ipsum dolor sit amet lo
> **[ASSISTANT]** lorem ipsum dolor sit amet lorem
> **[USER]** t4 lorem ipsum dolor sit amet lo
> **[ASSISTANT]** lorem ipsum dolor sit amet lorem
> **[USER]** t5 lorem ipsum dolor sit amet lo

<details><summary>Page contents (final state)</summary>

- **L1 page 0** (topic 1, 16 tok)
  - `user`: t1 lorem ipsum dolor sit amet lo
  - `assistant`: lorem ipsum dolor sit amet lorem
- **L1 page 1** (topic 2, 16 tok)
  - `user`: t2 lorem ipsum dolor sit amet lo
  - `assistant`: lorem ipsum dolor sit amet lorem
- **L1 page 2** (topic 3, 16 tok)
  - `user`: t3 lorem ipsum dolor sit amet lo
  - `assistant`: lorem ipsum dolor sit amet lorem
- **L1 page 3** (topic 4, 16 tok)
  - `user`: t4 lorem ipsum dolor sit amet lo
  - `assistant`: lorem ipsum dolor sit amet lorem
- **L1 page 4** (topic 5, 16 tok, OPEN)
  - `user`: t5 lorem ipsum dolor sit amet lo
  - `assistant`: lorem ipsum dolor sit amet lorem

</details>

- ✅ [fill] turn 5: no demotion while at or under high-water (80%) — got `[]`, expected `[]`
### Turn 6 [fill]: "t6 lorem ipsum dolor sit amet lorem ipsu"

- **Reply (assistant)**: lorem ipsum dolor sit amet lorem
- **Events in prepare_context**: `closed topic 5, card: dolor / sit / lorem`, `new topic 6`, `move page 0: L1 -> L2`, `move page 1: L1 -> L2`, `move page 2: L1 -> L2`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🔴 closed | `dolor / sit / lorem` | t1 lorem ipsum dolor sit amet lo | dolor, sit, lorem, amet, ipsum | `[0]` | 0 |
| 2 | 🔴 closed | `dolor / sit / lorem` | t2 lorem ipsum dolor sit amet lo | dolor, sit, lorem, amet, ipsum | `[1]` | 1 |
| 3 | 🔴 closed | `dolor / sit / lorem` | t3 lorem ipsum dolor sit amet lo | dolor, sit, lorem, amet, ipsum | `[2]` | 2 |
| 4 | 🔴 closed | `dolor / sit / lorem` | t4 lorem ipsum dolor sit amet lo | dolor, sit, lorem, amet, ipsum | `[3]` | 3 |
| 5 | 🔴 closed | `dolor / sit / lorem` | t5 lorem ipsum dolor sit amet lo | dolor, sit, lorem, amet, ipsum | `[4]` | 4 |
| 6 | 🟢 open | `t6 lorem ipsum dolor sit amet lorem ipsu` | - | - | `[5]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L2** | 1 | 16 |  | t1 lorem ipsum dolor sit amet lo |
| 1 | **L2** | 2 | 16 |  | t2 lorem ipsum dolor sit amet lo |
| 2 | **L2** | 3 | 16 |  | t3 lorem ipsum dolor sit amet lo |
| 3 | **L1** | 4 | 16 |  | t4 lorem ipsum dolor sit amet lo |
| 4 | **L1** | 5 | 16 |  | t5 lorem ipsum dolor sit amet lo |
| 5 | **L1** | 6 | 18 | yes | t6 lorem ipsum dolor sit amet lorem ipsu |

**L1 after prepare_context**: `[#################...|.............|.....]` 42/100 tok (42%); `|` marks low 50% / high 85%; L1 pages `[3, 4, 5]`, L2 pages `[0, 1, 2]`

**L1 after record_reply**: `[####################|.............|.....]` 50/100 tok (50%); `|` marks low 50% / high 85%; L1 pages `[3, 4, 5]`, L2 pages `[0, 1, 2]`

**Prompt sent to the model**

> **[SYSTEM]** [earlier messages omitted]
> **[USER]** t4 lorem ipsum dolor sit amet lo
> **[ASSISTANT]** lorem ipsum dolor sit amet lorem
> **[USER]** t5 lorem ipsum dolor sit amet lo
> **[ASSISTANT]** lorem ipsum dolor sit amet lorem
> **[USER]** t6 lorem ipsum dolor sit amet lorem ipsu

<details><summary>Page contents (final state)</summary>

- **L1 page 3** (topic 4, 16 tok)
  - `user`: t4 lorem ipsum dolor sit amet lo
  - `assistant`: lorem ipsum dolor sit amet lorem
- **L1 page 4** (topic 5, 16 tok)
  - `user`: t5 lorem ipsum dolor sit amet lo
  - `assistant`: lorem ipsum dolor sit amet lorem
- **L1 page 5** (topic 6, 18 tok, OPEN)
  - `user`: t6 lorem ipsum dolor sit amet lorem ipsu
  - `assistant`: lorem ipsum dolor sit amet lorem
- **L2 page 0** (topic 1, 16 tok)
  - `user`: t1 lorem ipsum dolor sit amet lo
  - `assistant`: lorem ipsum dolor sit amet lorem
- **L2 page 1** (topic 2, 16 tok)
  - `user`: t2 lorem ipsum dolor sit amet lo
  - `assistant`: lorem ipsum dolor sit amet lorem
- **L2 page 2** (topic 3, 16 tok)
  - `user`: t3 lorem ipsum dolor sit amet lo
  - `assistant`: lorem ipsum dolor sit amet lorem

</details>

- ✅ exactly the three oldest pages were demoted (a single demotion would not reach low-water) — got `[0, 1, 2]`, expected `[0, 1, 2]`
- ✅ right after the pressure check L1 is at 42% (<= 50% low-water)
- ✅ pages 3, 4 and 5 remain in L1: it stopped as soon as low-water was reached — got `[3, 4, 5]`, expected `[3, 4, 5]`
### Turn 7 [fill]: "t7 lorem ipsum dolor sit amet lorem ipsu"

- **Reply (assistant)**: lorem ipsum dolor sit amet lorem
- **Events in prepare_context**: `closed topic 6, card: dolor / ipsu / sit`, `new topic 7`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🔴 closed | `dolor / sit / lorem` | t1 lorem ipsum dolor sit amet lo | dolor, sit, lorem, amet, ipsum | `[0]` | 0 |
| 2 | 🔴 closed | `dolor / sit / lorem` | t2 lorem ipsum dolor sit amet lo | dolor, sit, lorem, amet, ipsum | `[1]` | 1 |
| 3 | 🔴 closed | `dolor / sit / lorem` | t3 lorem ipsum dolor sit amet lo | dolor, sit, lorem, amet, ipsum | `[2]` | 2 |
| 4 | 🔴 closed | `dolor / sit / lorem` | t4 lorem ipsum dolor sit amet lo | dolor, sit, lorem, amet, ipsum | `[3]` | 3 |
| 5 | 🔴 closed | `dolor / sit / lorem` | t5 lorem ipsum dolor sit amet lo | dolor, sit, lorem, amet, ipsum | `[4]` | 4 |
| 6 | 🔴 closed | `dolor / ipsu / sit` | t6 lorem ipsum dolor sit amet lorem ipsu | dolor, ipsu, sit, lorem, amet | `[5]` | 5 |
| 7 | 🟢 open | `t7 lorem ipsum dolor sit amet lorem ipsu` | - | - | `[6]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L2** | 1 | 16 |  | t1 lorem ipsum dolor sit amet lo |
| 1 | **L2** | 2 | 16 |  | t2 lorem ipsum dolor sit amet lo |
| 2 | **L2** | 3 | 16 |  | t3 lorem ipsum dolor sit amet lo |
| 3 | **L1** | 4 | 16 |  | t4 lorem ipsum dolor sit amet lo |
| 4 | **L1** | 5 | 16 |  | t5 lorem ipsum dolor sit amet lo |
| 5 | **L1** | 6 | 18 |  | t6 lorem ipsum dolor sit amet lorem ipsu |
| 6 | **L1** | 7 | 18 | yes | t7 lorem ipsum dolor sit amet lorem ipsu |

**L1 after prepare_context**: `[####################|###..........|.....]` 60/100 tok (60%); `|` marks low 50% / high 85%; L1 pages `[3, 4, 5, 6]`, L2 pages `[0, 1, 2]`

**L1 after record_reply**: `[####################|######.......|.....]` 68/100 tok (68%); `|` marks low 50% / high 85%; L1 pages `[3, 4, 5, 6]`, L2 pages `[0, 1, 2]`

**Prompt sent to the model**

> **[SYSTEM]** [earlier messages omitted]
> **[USER]** t4 lorem ipsum dolor sit amet lo
> **[ASSISTANT]** lorem ipsum dolor sit amet lorem
> **[USER]** t5 lorem ipsum dolor sit amet lo
> **[ASSISTANT]** lorem ipsum dolor sit amet lorem
> **[USER]** t6 lorem ipsum dolor sit amet lorem ipsu
> **[ASSISTANT]** lorem ipsum dolor sit amet lorem
> **[USER]** t7 lorem ipsum dolor sit amet lorem ipsu

<details><summary>Page contents (final state)</summary>

- **L1 page 3** (topic 4, 16 tok)
  - `user`: t4 lorem ipsum dolor sit amet lo
  - `assistant`: lorem ipsum dolor sit amet lorem
- **L1 page 4** (topic 5, 16 tok)
  - `user`: t5 lorem ipsum dolor sit amet lo
  - `assistant`: lorem ipsum dolor sit amet lorem
- **L1 page 5** (topic 6, 18 tok)
  - `user`: t6 lorem ipsum dolor sit amet lorem ipsu
  - `assistant`: lorem ipsum dolor sit amet lorem
- **L1 page 6** (topic 7, 18 tok, OPEN)
  - `user`: t7 lorem ipsum dolor sit amet lorem ipsu
  - `assistant`: lorem ipsum dolor sit amet lorem
- **L2 page 0** (topic 1, 16 tok)
  - `user`: t1 lorem ipsum dolor sit amet lo
  - `assistant`: lorem ipsum dolor sit amet lorem
- **L2 page 1** (topic 2, 16 tok)
  - `user`: t2 lorem ipsum dolor sit amet lo
  - `assistant`: lorem ipsum dolor sit amet lorem
- **L2 page 2** (topic 3, 16 tok)
  - `user`: t3 lorem ipsum dolor sit amet lo
  - `assistant`: lorem ipsum dolor sit amet lorem

</details>

- ✅ hysteresis: the next turn (~60%) triggers nothing because it is under high-water — got `[]`, expected `[]`

**Result: ✅ PASS**  (9 checks, 0 failed, 7 turns, 0.00s)

---

## P3 — newest pages are protected

> The newest protect_recent_pages pages are never demoted, even if low-water cannot be reached.

### Turn 1 [protect 3]: "t1 lorem ipsum dolor sit amet lo"

- **Reply (assistant)**: lorem ipsum dolor sit amet lorem
- **Events in prepare_context**: `new topic 1`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🟢 open | `t1 lorem ipsum dolor sit amet lo` | - | - | `[0]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L1** | 1 | 16 | yes | t1 lorem ipsum dolor sit amet lo |

**L1 after prepare_context**: `[##|...............................|.....]` 8/100 tok (8%); `|` marks low 5% / high 85%; L1 pages `[0]`, L2 pages `[]`

**L1 after record_reply**: `[##|###............................|.....]` 16/100 tok (16%); `|` marks low 5% / high 85%; L1 pages `[0]`, L2 pages `[]`

**Prompt sent to the model**

> **[USER]** t1 lorem ipsum dolor sit amet lo

<details><summary>Page contents (final state)</summary>

- **L1 page 0** (topic 1, 16 tok, OPEN)
  - `user`: t1 lorem ipsum dolor sit amet lo
  - `assistant`: lorem ipsum dolor sit amet lorem

</details>

- ✅ [protect 3] turn 1: no demotion while at or under high-water (16%) — got `[]`, expected `[]`
### Turn 2 [protect 3]: "t2 lorem ipsum dolor sit amet lo"

- **Reply (assistant)**: lorem ipsum dolor sit amet lorem
- **Events in prepare_context**: `closed topic 1, card: dolor / sit / lorem`, `new topic 2`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🔴 closed | `dolor / sit / lorem` | t1 lorem ipsum dolor sit amet lo | dolor, sit, lorem, amet, ipsum | `[0]` | 0 |
| 2 | 🟢 open | `t2 lorem ipsum dolor sit amet lo` | - | - | `[1]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L1** | 1 | 16 |  | t1 lorem ipsum dolor sit amet lo |
| 1 | **L1** | 2 | 16 | yes | t2 lorem ipsum dolor sit amet lo |

**L1 after prepare_context**: `[##|#######........................|.....]` 24/100 tok (24%); `|` marks low 5% / high 85%; L1 pages `[0, 1]`, L2 pages `[]`

**L1 after record_reply**: `[##|##########.....................|.....]` 32/100 tok (32%); `|` marks low 5% / high 85%; L1 pages `[0, 1]`, L2 pages `[]`

**Prompt sent to the model**

> **[USER]** t1 lorem ipsum dolor sit amet lo
> **[ASSISTANT]** lorem ipsum dolor sit amet lorem
> **[USER]** t2 lorem ipsum dolor sit amet lo

<details><summary>Page contents (final state)</summary>

- **L1 page 0** (topic 1, 16 tok)
  - `user`: t1 lorem ipsum dolor sit amet lo
  - `assistant`: lorem ipsum dolor sit amet lorem
- **L1 page 1** (topic 2, 16 tok, OPEN)
  - `user`: t2 lorem ipsum dolor sit amet lo
  - `assistant`: lorem ipsum dolor sit amet lorem

</details>

- ✅ [protect 3] turn 2: no demotion while at or under high-water (32%) — got `[]`, expected `[]`
### Turn 3 [protect 3]: "t3 lorem ipsum dolor sit amet lo"

- **Reply (assistant)**: lorem ipsum dolor sit amet lorem
- **Events in prepare_context**: `closed topic 2, card: dolor / sit / lorem`, `new topic 3`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🔴 closed | `dolor / sit / lorem` | t1 lorem ipsum dolor sit amet lo | dolor, sit, lorem, amet, ipsum | `[0]` | 0 |
| 2 | 🔴 closed | `dolor / sit / lorem` | t2 lorem ipsum dolor sit amet lo | dolor, sit, lorem, amet, ipsum | `[1]` | 1 |
| 3 | 🟢 open | `t3 lorem ipsum dolor sit amet lo` | - | - | `[2]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L1** | 1 | 16 |  | t1 lorem ipsum dolor sit amet lo |
| 1 | **L1** | 2 | 16 |  | t2 lorem ipsum dolor sit amet lo |
| 2 | **L1** | 3 | 16 | yes | t3 lorem ipsum dolor sit amet lo |

**L1 after prepare_context**: `[##|#############..................|.....]` 40/100 tok (40%); `|` marks low 5% / high 85%; L1 pages `[0, 1, 2]`, L2 pages `[]`

**L1 after record_reply**: `[##|################...............|.....]` 48/100 tok (48%); `|` marks low 5% / high 85%; L1 pages `[0, 1, 2]`, L2 pages `[]`

**Prompt sent to the model**

> **[USER]** t1 lorem ipsum dolor sit amet lo
> **[ASSISTANT]** lorem ipsum dolor sit amet lorem
> **[USER]** t2 lorem ipsum dolor sit amet lo
> **[ASSISTANT]** lorem ipsum dolor sit amet lorem
> **[USER]** t3 lorem ipsum dolor sit amet lo

<details><summary>Page contents (final state)</summary>

- **L1 page 0** (topic 1, 16 tok)
  - `user`: t1 lorem ipsum dolor sit amet lo
  - `assistant`: lorem ipsum dolor sit amet lorem
- **L1 page 1** (topic 2, 16 tok)
  - `user`: t2 lorem ipsum dolor sit amet lo
  - `assistant`: lorem ipsum dolor sit amet lorem
- **L1 page 2** (topic 3, 16 tok, OPEN)
  - `user`: t3 lorem ipsum dolor sit amet lo
  - `assistant`: lorem ipsum dolor sit amet lorem

</details>

- ✅ [protect 3] turn 3: no demotion while at or under high-water (48%) — got `[]`, expected `[]`
### Turn 4 [protect 3]: "t4 lorem ipsum dolor sit amet lo"

- **Reply (assistant)**: lorem ipsum dolor sit amet lorem
- **Events in prepare_context**: `closed topic 3, card: dolor / sit / lorem`, `new topic 4`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🔴 closed | `dolor / sit / lorem` | t1 lorem ipsum dolor sit amet lo | dolor, sit, lorem, amet, ipsum | `[0]` | 0 |
| 2 | 🔴 closed | `dolor / sit / lorem` | t2 lorem ipsum dolor sit amet lo | dolor, sit, lorem, amet, ipsum | `[1]` | 1 |
| 3 | 🔴 closed | `dolor / sit / lorem` | t3 lorem ipsum dolor sit amet lo | dolor, sit, lorem, amet, ipsum | `[2]` | 2 |
| 4 | 🟢 open | `t4 lorem ipsum dolor sit amet lo` | - | - | `[3]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L1** | 1 | 16 |  | t1 lorem ipsum dolor sit amet lo |
| 1 | **L1** | 2 | 16 |  | t2 lorem ipsum dolor sit amet lo |
| 2 | **L1** | 3 | 16 |  | t3 lorem ipsum dolor sit amet lo |
| 3 | **L1** | 4 | 16 | yes | t4 lorem ipsum dolor sit amet lo |

**L1 after prepare_context**: `[##|###################............|.....]` 56/100 tok (56%); `|` marks low 5% / high 85%; L1 pages `[0, 1, 2, 3]`, L2 pages `[]`

**L1 after record_reply**: `[##|#######################........|.....]` 64/100 tok (64%); `|` marks low 5% / high 85%; L1 pages `[0, 1, 2, 3]`, L2 pages `[]`

**Prompt sent to the model**

> **[USER]** t1 lorem ipsum dolor sit amet lo
> **[ASSISTANT]** lorem ipsum dolor sit amet lorem
> **[USER]** t2 lorem ipsum dolor sit amet lo
> **[ASSISTANT]** lorem ipsum dolor sit amet lorem
> **[USER]** t3 lorem ipsum dolor sit amet lo
> **[ASSISTANT]** lorem ipsum dolor sit amet lorem
> **[USER]** t4 lorem ipsum dolor sit amet lo

<details><summary>Page contents (final state)</summary>

- **L1 page 0** (topic 1, 16 tok)
  - `user`: t1 lorem ipsum dolor sit amet lo
  - `assistant`: lorem ipsum dolor sit amet lorem
- **L1 page 1** (topic 2, 16 tok)
  - `user`: t2 lorem ipsum dolor sit amet lo
  - `assistant`: lorem ipsum dolor sit amet lorem
- **L1 page 2** (topic 3, 16 tok)
  - `user`: t3 lorem ipsum dolor sit amet lo
  - `assistant`: lorem ipsum dolor sit amet lorem
- **L1 page 3** (topic 4, 16 tok, OPEN)
  - `user`: t4 lorem ipsum dolor sit amet lo
  - `assistant`: lorem ipsum dolor sit amet lorem

</details>

- ✅ [protect 3] turn 4: no demotion while at or under high-water (64%) — got `[]`, expected `[]`
### Turn 5 [protect 3]: "t5 lorem ipsum dolor sit amet lo"

- **Reply (assistant)**: lorem ipsum dolor sit amet lorem
- **Events in prepare_context**: `closed topic 4, card: dolor / sit / lorem`, `new topic 5`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🔴 closed | `dolor / sit / lorem` | t1 lorem ipsum dolor sit amet lo | dolor, sit, lorem, amet, ipsum | `[0]` | 0 |
| 2 | 🔴 closed | `dolor / sit / lorem` | t2 lorem ipsum dolor sit amet lo | dolor, sit, lorem, amet, ipsum | `[1]` | 1 |
| 3 | 🔴 closed | `dolor / sit / lorem` | t3 lorem ipsum dolor sit amet lo | dolor, sit, lorem, amet, ipsum | `[2]` | 2 |
| 4 | 🔴 closed | `dolor / sit / lorem` | t4 lorem ipsum dolor sit amet lo | dolor, sit, lorem, amet, ipsum | `[3]` | 3 |
| 5 | 🟢 open | `t5 lorem ipsum dolor sit amet lo` | - | - | `[4]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L1** | 1 | 16 |  | t1 lorem ipsum dolor sit amet lo |
| 1 | **L1** | 2 | 16 |  | t2 lorem ipsum dolor sit amet lo |
| 2 | **L1** | 3 | 16 |  | t3 lorem ipsum dolor sit amet lo |
| 3 | **L1** | 4 | 16 |  | t4 lorem ipsum dolor sit amet lo |
| 4 | **L1** | 5 | 16 | yes | t5 lorem ipsum dolor sit amet lo |

**L1 after prepare_context**: `[##|##########################.....|.....]` 72/100 tok (72%); `|` marks low 5% / high 85%; L1 pages `[0, 1, 2, 3, 4]`, L2 pages `[]`

**L1 after record_reply**: `[##|#############################..|.....]` 80/100 tok (80%); `|` marks low 5% / high 85%; L1 pages `[0, 1, 2, 3, 4]`, L2 pages `[]`

**Prompt sent to the model**

> **[USER]** t1 lorem ipsum dolor sit amet lo
> **[ASSISTANT]** lorem ipsum dolor sit amet lorem
> **[USER]** t2 lorem ipsum dolor sit amet lo
> **[ASSISTANT]** lorem ipsum dolor sit amet lorem
> **[USER]** t3 lorem ipsum dolor sit amet lo
> **[ASSISTANT]** lorem ipsum dolor sit amet lorem
> **[USER]** t4 lorem ipsum dolor sit amet lo
> **[ASSISTANT]** lorem ipsum dolor sit amet lorem
> **[USER]** t5 lorem ipsum dolor sit amet lo

<details><summary>Page contents (final state)</summary>

- **L1 page 0** (topic 1, 16 tok)
  - `user`: t1 lorem ipsum dolor sit amet lo
  - `assistant`: lorem ipsum dolor sit amet lorem
- **L1 page 1** (topic 2, 16 tok)
  - `user`: t2 lorem ipsum dolor sit amet lo
  - `assistant`: lorem ipsum dolor sit amet lorem
- **L1 page 2** (topic 3, 16 tok)
  - `user`: t3 lorem ipsum dolor sit amet lo
  - `assistant`: lorem ipsum dolor sit amet lorem
- **L1 page 3** (topic 4, 16 tok)
  - `user`: t4 lorem ipsum dolor sit amet lo
  - `assistant`: lorem ipsum dolor sit amet lorem
- **L1 page 4** (topic 5, 16 tok, OPEN)
  - `user`: t5 lorem ipsum dolor sit amet lo
  - `assistant`: lorem ipsum dolor sit amet lorem

</details>

- ✅ [protect 3] turn 5: no demotion while at or under high-water (80%) — got `[]`, expected `[]`
### Turn 6 [protect 3]: "t6 lorem ipsum dolor sit amet lorem ipsu"

- **Reply (assistant)**: lorem ipsum dolor sit amet lorem
- **Events in prepare_context**: `closed topic 5, card: dolor / sit / lorem`, `new topic 6`, `move page 0: L1 -> L2`, `move page 1: L1 -> L2`, `move page 2: L1 -> L2`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🔴 closed | `dolor / sit / lorem` | t1 lorem ipsum dolor sit amet lo | dolor, sit, lorem, amet, ipsum | `[0]` | 0 |
| 2 | 🔴 closed | `dolor / sit / lorem` | t2 lorem ipsum dolor sit amet lo | dolor, sit, lorem, amet, ipsum | `[1]` | 1 |
| 3 | 🔴 closed | `dolor / sit / lorem` | t3 lorem ipsum dolor sit amet lo | dolor, sit, lorem, amet, ipsum | `[2]` | 2 |
| 4 | 🔴 closed | `dolor / sit / lorem` | t4 lorem ipsum dolor sit amet lo | dolor, sit, lorem, amet, ipsum | `[3]` | 3 |
| 5 | 🔴 closed | `dolor / sit / lorem` | t5 lorem ipsum dolor sit amet lo | dolor, sit, lorem, amet, ipsum | `[4]` | 4 |
| 6 | 🟢 open | `t6 lorem ipsum dolor sit amet lorem ipsu` | - | - | `[5]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L2** | 1 | 16 |  | t1 lorem ipsum dolor sit amet lo |
| 1 | **L2** | 2 | 16 |  | t2 lorem ipsum dolor sit amet lo |
| 2 | **L2** | 3 | 16 |  | t3 lorem ipsum dolor sit amet lo |
| 3 | **L1** | 4 | 16 |  | t4 lorem ipsum dolor sit amet lo |
| 4 | **L1** | 5 | 16 |  | t5 lorem ipsum dolor sit amet lo |
| 5 | **L1** | 6 | 18 | yes | t6 lorem ipsum dolor sit amet lorem ipsu |

**L1 after prepare_context**: `[##|##############.................|.....]` 42/100 tok (42%); `|` marks low 5% / high 85%; L1 pages `[3, 4, 5]`, L2 pages `[0, 1, 2]`

**L1 after record_reply**: `[##|#################..............|.....]` 50/100 tok (50%); `|` marks low 5% / high 85%; L1 pages `[3, 4, 5]`, L2 pages `[0, 1, 2]`

**Prompt sent to the model**

> **[SYSTEM]** [earlier messages omitted]
> **[USER]** t4 lorem ipsum dolor sit amet lo
> **[ASSISTANT]** lorem ipsum dolor sit amet lorem
> **[USER]** t5 lorem ipsum dolor sit amet lo
> **[ASSISTANT]** lorem ipsum dolor sit amet lorem
> **[USER]** t6 lorem ipsum dolor sit amet lorem ipsu

<details><summary>Page contents (final state)</summary>

- **L1 page 3** (topic 4, 16 tok)
  - `user`: t4 lorem ipsum dolor sit amet lo
  - `assistant`: lorem ipsum dolor sit amet lorem
- **L1 page 4** (topic 5, 16 tok)
  - `user`: t5 lorem ipsum dolor sit amet lo
  - `assistant`: lorem ipsum dolor sit amet lorem
- **L1 page 5** (topic 6, 18 tok, OPEN)
  - `user`: t6 lorem ipsum dolor sit amet lorem ipsu
  - `assistant`: lorem ipsum dolor sit amet lorem
- **L2 page 0** (topic 1, 16 tok)
  - `user`: t1 lorem ipsum dolor sit amet lo
  - `assistant`: lorem ipsum dolor sit amet lorem
- **L2 page 1** (topic 2, 16 tok)
  - `user`: t2 lorem ipsum dolor sit amet lo
  - `assistant`: lorem ipsum dolor sit amet lorem
- **L2 page 2** (topic 3, 16 tok)
  - `user`: t3 lorem ipsum dolor sit amet lo
  - `assistant`: lorem ipsum dolor sit amet lorem

</details>

- ✅ only the three oldest pages were candidates — got `[0, 1, 2]`, expected `[0, 1, 2]`
- ✅ the newest three pages (3, 4, and open 5) stayed — got `[3, 4, 5]`, expected `[3, 4, 5]`
- ✅ L1 is still above low-water: protection wins over the target

**Result: ✅ PASS**  (8 checks, 0 failed, 6 turns, 0.00s)

---

## P4 — protect recent pages zero protects only the open page

> protect_recent_pages=0 means no extra protection (only the open page and needed topics are kept).

### Turn 1 [protect 0]: "t1 lorem ipsum dolor sit amet lo"

- **Reply (assistant)**: lorem ipsum dolor sit amet lorem
- **Events in prepare_context**: `new topic 1`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🟢 open | `t1 lorem ipsum dolor sit amet lo` | - | - | `[0]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L1** | 1 | 16 | yes | t1 lorem ipsum dolor sit amet lo |

**L1 after prepare_context**: `[##|...............................|.....]` 8/100 tok (8%); `|` marks low 5% / high 85%; L1 pages `[0]`, L2 pages `[]`

**L1 after record_reply**: `[##|###............................|.....]` 16/100 tok (16%); `|` marks low 5% / high 85%; L1 pages `[0]`, L2 pages `[]`

**Prompt sent to the model**

> **[USER]** t1 lorem ipsum dolor sit amet lo

<details><summary>Page contents (final state)</summary>

- **L1 page 0** (topic 1, 16 tok, OPEN)
  - `user`: t1 lorem ipsum dolor sit amet lo
  - `assistant`: lorem ipsum dolor sit amet lorem

</details>

- ✅ [protect 0] turn 1: no demotion while at or under high-water (16%) — got `[]`, expected `[]`
### Turn 2 [protect 0]: "t2 lorem ipsum dolor sit amet lo"

- **Reply (assistant)**: lorem ipsum dolor sit amet lorem
- **Events in prepare_context**: `closed topic 1, card: dolor / sit / lorem`, `new topic 2`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🔴 closed | `dolor / sit / lorem` | t1 lorem ipsum dolor sit amet lo | dolor, sit, lorem, amet, ipsum | `[0]` | 0 |
| 2 | 🟢 open | `t2 lorem ipsum dolor sit amet lo` | - | - | `[1]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L1** | 1 | 16 |  | t1 lorem ipsum dolor sit amet lo |
| 1 | **L1** | 2 | 16 | yes | t2 lorem ipsum dolor sit amet lo |

**L1 after prepare_context**: `[##|#######........................|.....]` 24/100 tok (24%); `|` marks low 5% / high 85%; L1 pages `[0, 1]`, L2 pages `[]`

**L1 after record_reply**: `[##|##########.....................|.....]` 32/100 tok (32%); `|` marks low 5% / high 85%; L1 pages `[0, 1]`, L2 pages `[]`

**Prompt sent to the model**

> **[USER]** t1 lorem ipsum dolor sit amet lo
> **[ASSISTANT]** lorem ipsum dolor sit amet lorem
> **[USER]** t2 lorem ipsum dolor sit amet lo

<details><summary>Page contents (final state)</summary>

- **L1 page 0** (topic 1, 16 tok)
  - `user`: t1 lorem ipsum dolor sit amet lo
  - `assistant`: lorem ipsum dolor sit amet lorem
- **L1 page 1** (topic 2, 16 tok, OPEN)
  - `user`: t2 lorem ipsum dolor sit amet lo
  - `assistant`: lorem ipsum dolor sit amet lorem

</details>

- ✅ [protect 0] turn 2: no demotion while at or under high-water (32%) — got `[]`, expected `[]`
### Turn 3 [protect 0]: "t3 lorem ipsum dolor sit amet lo"

- **Reply (assistant)**: lorem ipsum dolor sit amet lorem
- **Events in prepare_context**: `closed topic 2, card: dolor / sit / lorem`, `new topic 3`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🔴 closed | `dolor / sit / lorem` | t1 lorem ipsum dolor sit amet lo | dolor, sit, lorem, amet, ipsum | `[0]` | 0 |
| 2 | 🔴 closed | `dolor / sit / lorem` | t2 lorem ipsum dolor sit amet lo | dolor, sit, lorem, amet, ipsum | `[1]` | 1 |
| 3 | 🟢 open | `t3 lorem ipsum dolor sit amet lo` | - | - | `[2]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L1** | 1 | 16 |  | t1 lorem ipsum dolor sit amet lo |
| 1 | **L1** | 2 | 16 |  | t2 lorem ipsum dolor sit amet lo |
| 2 | **L1** | 3 | 16 | yes | t3 lorem ipsum dolor sit amet lo |

**L1 after prepare_context**: `[##|#############..................|.....]` 40/100 tok (40%); `|` marks low 5% / high 85%; L1 pages `[0, 1, 2]`, L2 pages `[]`

**L1 after record_reply**: `[##|################...............|.....]` 48/100 tok (48%); `|` marks low 5% / high 85%; L1 pages `[0, 1, 2]`, L2 pages `[]`

**Prompt sent to the model**

> **[USER]** t1 lorem ipsum dolor sit amet lo
> **[ASSISTANT]** lorem ipsum dolor sit amet lorem
> **[USER]** t2 lorem ipsum dolor sit amet lo
> **[ASSISTANT]** lorem ipsum dolor sit amet lorem
> **[USER]** t3 lorem ipsum dolor sit amet lo

<details><summary>Page contents (final state)</summary>

- **L1 page 0** (topic 1, 16 tok)
  - `user`: t1 lorem ipsum dolor sit amet lo
  - `assistant`: lorem ipsum dolor sit amet lorem
- **L1 page 1** (topic 2, 16 tok)
  - `user`: t2 lorem ipsum dolor sit amet lo
  - `assistant`: lorem ipsum dolor sit amet lorem
- **L1 page 2** (topic 3, 16 tok, OPEN)
  - `user`: t3 lorem ipsum dolor sit amet lo
  - `assistant`: lorem ipsum dolor sit amet lorem

</details>

- ✅ [protect 0] turn 3: no demotion while at or under high-water (48%) — got `[]`, expected `[]`
### Turn 4 [protect 0]: "t4 lorem ipsum dolor sit amet lo"

- **Reply (assistant)**: lorem ipsum dolor sit amet lorem
- **Events in prepare_context**: `closed topic 3, card: dolor / sit / lorem`, `new topic 4`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🔴 closed | `dolor / sit / lorem` | t1 lorem ipsum dolor sit amet lo | dolor, sit, lorem, amet, ipsum | `[0]` | 0 |
| 2 | 🔴 closed | `dolor / sit / lorem` | t2 lorem ipsum dolor sit amet lo | dolor, sit, lorem, amet, ipsum | `[1]` | 1 |
| 3 | 🔴 closed | `dolor / sit / lorem` | t3 lorem ipsum dolor sit amet lo | dolor, sit, lorem, amet, ipsum | `[2]` | 2 |
| 4 | 🟢 open | `t4 lorem ipsum dolor sit amet lo` | - | - | `[3]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L1** | 1 | 16 |  | t1 lorem ipsum dolor sit amet lo |
| 1 | **L1** | 2 | 16 |  | t2 lorem ipsum dolor sit amet lo |
| 2 | **L1** | 3 | 16 |  | t3 lorem ipsum dolor sit amet lo |
| 3 | **L1** | 4 | 16 | yes | t4 lorem ipsum dolor sit amet lo |

**L1 after prepare_context**: `[##|###################............|.....]` 56/100 tok (56%); `|` marks low 5% / high 85%; L1 pages `[0, 1, 2, 3]`, L2 pages `[]`

**L1 after record_reply**: `[##|#######################........|.....]` 64/100 tok (64%); `|` marks low 5% / high 85%; L1 pages `[0, 1, 2, 3]`, L2 pages `[]`

**Prompt sent to the model**

> **[USER]** t1 lorem ipsum dolor sit amet lo
> **[ASSISTANT]** lorem ipsum dolor sit amet lorem
> **[USER]** t2 lorem ipsum dolor sit amet lo
> **[ASSISTANT]** lorem ipsum dolor sit amet lorem
> **[USER]** t3 lorem ipsum dolor sit amet lo
> **[ASSISTANT]** lorem ipsum dolor sit amet lorem
> **[USER]** t4 lorem ipsum dolor sit amet lo

<details><summary>Page contents (final state)</summary>

- **L1 page 0** (topic 1, 16 tok)
  - `user`: t1 lorem ipsum dolor sit amet lo
  - `assistant`: lorem ipsum dolor sit amet lorem
- **L1 page 1** (topic 2, 16 tok)
  - `user`: t2 lorem ipsum dolor sit amet lo
  - `assistant`: lorem ipsum dolor sit amet lorem
- **L1 page 2** (topic 3, 16 tok)
  - `user`: t3 lorem ipsum dolor sit amet lo
  - `assistant`: lorem ipsum dolor sit amet lorem
- **L1 page 3** (topic 4, 16 tok, OPEN)
  - `user`: t4 lorem ipsum dolor sit amet lo
  - `assistant`: lorem ipsum dolor sit amet lorem

</details>

- ✅ [protect 0] turn 4: no demotion while at or under high-water (64%) — got `[]`, expected `[]`
### Turn 5 [protect 0]: "t5 lorem ipsum dolor sit amet lo"

- **Reply (assistant)**: lorem ipsum dolor sit amet lorem
- **Events in prepare_context**: `closed topic 4, card: dolor / sit / lorem`, `new topic 5`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🔴 closed | `dolor / sit / lorem` | t1 lorem ipsum dolor sit amet lo | dolor, sit, lorem, amet, ipsum | `[0]` | 0 |
| 2 | 🔴 closed | `dolor / sit / lorem` | t2 lorem ipsum dolor sit amet lo | dolor, sit, lorem, amet, ipsum | `[1]` | 1 |
| 3 | 🔴 closed | `dolor / sit / lorem` | t3 lorem ipsum dolor sit amet lo | dolor, sit, lorem, amet, ipsum | `[2]` | 2 |
| 4 | 🔴 closed | `dolor / sit / lorem` | t4 lorem ipsum dolor sit amet lo | dolor, sit, lorem, amet, ipsum | `[3]` | 3 |
| 5 | 🟢 open | `t5 lorem ipsum dolor sit amet lo` | - | - | `[4]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L1** | 1 | 16 |  | t1 lorem ipsum dolor sit amet lo |
| 1 | **L1** | 2 | 16 |  | t2 lorem ipsum dolor sit amet lo |
| 2 | **L1** | 3 | 16 |  | t3 lorem ipsum dolor sit amet lo |
| 3 | **L1** | 4 | 16 |  | t4 lorem ipsum dolor sit amet lo |
| 4 | **L1** | 5 | 16 | yes | t5 lorem ipsum dolor sit amet lo |

**L1 after prepare_context**: `[##|##########################.....|.....]` 72/100 tok (72%); `|` marks low 5% / high 85%; L1 pages `[0, 1, 2, 3, 4]`, L2 pages `[]`

**L1 after record_reply**: `[##|#############################..|.....]` 80/100 tok (80%); `|` marks low 5% / high 85%; L1 pages `[0, 1, 2, 3, 4]`, L2 pages `[]`

**Prompt sent to the model**

> **[USER]** t1 lorem ipsum dolor sit amet lo
> **[ASSISTANT]** lorem ipsum dolor sit amet lorem
> **[USER]** t2 lorem ipsum dolor sit amet lo
> **[ASSISTANT]** lorem ipsum dolor sit amet lorem
> **[USER]** t3 lorem ipsum dolor sit amet lo
> **[ASSISTANT]** lorem ipsum dolor sit amet lorem
> **[USER]** t4 lorem ipsum dolor sit amet lo
> **[ASSISTANT]** lorem ipsum dolor sit amet lorem
> **[USER]** t5 lorem ipsum dolor sit amet lo

<details><summary>Page contents (final state)</summary>

- **L1 page 0** (topic 1, 16 tok)
  - `user`: t1 lorem ipsum dolor sit amet lo
  - `assistant`: lorem ipsum dolor sit amet lorem
- **L1 page 1** (topic 2, 16 tok)
  - `user`: t2 lorem ipsum dolor sit amet lo
  - `assistant`: lorem ipsum dolor sit amet lorem
- **L1 page 2** (topic 3, 16 tok)
  - `user`: t3 lorem ipsum dolor sit amet lo
  - `assistant`: lorem ipsum dolor sit amet lorem
- **L1 page 3** (topic 4, 16 tok)
  - `user`: t4 lorem ipsum dolor sit amet lo
  - `assistant`: lorem ipsum dolor sit amet lorem
- **L1 page 4** (topic 5, 16 tok, OPEN)
  - `user`: t5 lorem ipsum dolor sit amet lo
  - `assistant`: lorem ipsum dolor sit amet lorem

</details>

- ✅ [protect 0] turn 5: no demotion while at or under high-water (80%) — got `[]`, expected `[]`
### Turn 6 [protect 0]: "t6 lorem ipsum dolor sit amet lorem ipsu"

- **Reply (assistant)**: lorem ipsum dolor sit amet lorem
- **Events in prepare_context**: `closed topic 5, card: dolor / sit / lorem`, `new topic 6`, `move page 0: L1 -> L2`, `move page 1: L1 -> L2`, `move page 2: L1 -> L2`, `move page 3: L1 -> L2`, `move page 4: L1 -> L2`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🔴 closed | `dolor / sit / lorem` | t1 lorem ipsum dolor sit amet lo | dolor, sit, lorem, amet, ipsum | `[0]` | 0 |
| 2 | 🔴 closed | `dolor / sit / lorem` | t2 lorem ipsum dolor sit amet lo | dolor, sit, lorem, amet, ipsum | `[1]` | 1 |
| 3 | 🔴 closed | `dolor / sit / lorem` | t3 lorem ipsum dolor sit amet lo | dolor, sit, lorem, amet, ipsum | `[2]` | 2 |
| 4 | 🔴 closed | `dolor / sit / lorem` | t4 lorem ipsum dolor sit amet lo | dolor, sit, lorem, amet, ipsum | `[3]` | 3 |
| 5 | 🔴 closed | `dolor / sit / lorem` | t5 lorem ipsum dolor sit amet lo | dolor, sit, lorem, amet, ipsum | `[4]` | 4 |
| 6 | 🟢 open | `t6 lorem ipsum dolor sit amet lorem ipsu` | - | - | `[5]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L2** | 1 | 16 |  | t1 lorem ipsum dolor sit amet lo |
| 1 | **L2** | 2 | 16 |  | t2 lorem ipsum dolor sit amet lo |
| 2 | **L2** | 3 | 16 |  | t3 lorem ipsum dolor sit amet lo |
| 3 | **L2** | 4 | 16 |  | t4 lorem ipsum dolor sit amet lo |
| 4 | **L2** | 5 | 16 |  | t5 lorem ipsum dolor sit amet lo |
| 5 | **L1** | 6 | 18 | yes | t6 lorem ipsum dolor sit amet lorem ipsu |

**L1 after prepare_context**: `[##|#..............................|.....]` 10/100 tok (10%); `|` marks low 5% / high 85%; L1 pages `[5]`, L2 pages `[0, 1, 2, 3, 4]`

**L1 after record_reply**: `[##|####...........................|.....]` 18/100 tok (18%); `|` marks low 5% / high 85%; L1 pages `[5]`, L2 pages `[0, 1, 2, 3, 4]`

**Prompt sent to the model**

> **[SYSTEM]** [earlier messages omitted]
> **[USER]** t6 lorem ipsum dolor sit amet lorem ipsu

<details><summary>Page contents (final state)</summary>

- **L1 page 5** (topic 6, 18 tok, OPEN)
  - `user`: t6 lorem ipsum dolor sit amet lorem ipsu
  - `assistant`: lorem ipsum dolor sit amet lorem
- **L2 page 0** (topic 1, 16 tok)
  - `user`: t1 lorem ipsum dolor sit amet lo
  - `assistant`: lorem ipsum dolor sit amet lorem
- **L2 page 1** (topic 2, 16 tok)
  - `user`: t2 lorem ipsum dolor sit amet lo
  - `assistant`: lorem ipsum dolor sit amet lorem
- **L2 page 2** (topic 3, 16 tok)
  - `user`: t3 lorem ipsum dolor sit amet lo
  - `assistant`: lorem ipsum dolor sit amet lorem
- **L2 page 3** (topic 4, 16 tok)
  - `user`: t4 lorem ipsum dolor sit amet lo
  - `assistant`: lorem ipsum dolor sit amet lorem
- **L2 page 4** (topic 5, 16 tok)
  - `user`: t5 lorem ipsum dolor sit amet lo
  - `assistant`: lorem ipsum dolor sit amet lorem

</details>

- ✅ all five closed pages are demotable — got `[0, 1, 2, 3, 4]`, expected `[0, 1, 2, 3, 4]`
- ✅ only the open page remains in L1 — got `[5]`, expected `[5]`

**Result: ✅ PASS**  (7 checks, 0 failed, 6 turns, 0.00s)

---

## P5 — victims are chosen by router score then age

> Lowest router score is demoted first; an older relevant page beats a newer irrelevant one.

### Turn 1: "t1 lorem ipsum dolor sit amet lorem ipsu"

- **Reply (assistant)**: lorem ipsum dolor sit amet lorem ipsum d
- **Events in prepare_context**: `new topic 1`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🟢 open | `t1 lorem ipsum dolor sit amet lorem ipsu` | - | - | `[0]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L1** | 1 | 20 | yes | t1 lorem ipsum dolor sit amet lorem ipsu |

**L1 after prepare_context**: `[####....................|.........|.....]` 10/100 tok (10%); `|` marks low 60% / high 85%; L1 pages `[0]`, L2 pages `[]`

**L1 after record_reply**: `[########................|.........|.....]` 20/100 tok (20%); `|` marks low 60% / high 85%; L1 pages `[0]`, L2 pages `[]`

**Prompt sent to the model**

> **[USER]** t1 lorem ipsum dolor sit amet lorem ipsu

<details><summary>Page contents (final state)</summary>

- **L1 page 0** (topic 1, 20 tok, OPEN)
  - `user`: t1 lorem ipsum dolor sit amet lorem ipsu
  - `assistant`: lorem ipsum dolor sit amet lorem ipsum d

</details>

### Turn 2: "t2 lorem ipsum dolor sit amet lorem ipsu"

- **Reply (assistant)**: lorem ipsum dolor sit amet lorem ipsum d
- **Events in prepare_context**: `closed topic 1, card: dolor / ipsu / sit`, `new topic 2`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🔴 closed | `dolor / ipsu / sit` | t1 lorem ipsum dolor sit amet lorem ipsu | dolor, ipsu, sit, lorem, amet | `[0]` | 0 |
| 2 | 🟢 open | `t2 lorem ipsum dolor sit amet lorem ipsu` | - | - | `[1]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L1** | 1 | 20 |  | t1 lorem ipsum dolor sit amet lorem ipsu |
| 1 | **L1** | 2 | 20 | yes | t2 lorem ipsum dolor sit amet lorem ipsu |

**L1 after prepare_context**: `[############............|.........|.....]` 30/100 tok (30%); `|` marks low 60% / high 85%; L1 pages `[0, 1]`, L2 pages `[]`

**L1 after record_reply**: `[################........|.........|.....]` 40/100 tok (40%); `|` marks low 60% / high 85%; L1 pages `[0, 1]`, L2 pages `[]`

**Prompt sent to the model**

> **[USER]** t1 lorem ipsum dolor sit amet lorem ipsu
> **[ASSISTANT]** lorem ipsum dolor sit amet lorem ipsum d
> **[USER]** t2 lorem ipsum dolor sit amet lorem ipsu

<details><summary>Page contents (final state)</summary>

- **L1 page 0** (topic 1, 20 tok)
  - `user`: t1 lorem ipsum dolor sit amet lorem ipsu
  - `assistant`: lorem ipsum dolor sit amet lorem ipsum d
- **L1 page 1** (topic 2, 20 tok, OPEN)
  - `user`: t2 lorem ipsum dolor sit amet lorem ipsu
  - `assistant`: lorem ipsum dolor sit amet lorem ipsum d

</details>

### Turn 3: "t3 lorem ipsum dolor sit amet lorem ipsu"

- **Reply (assistant)**: lorem ipsum dolor sit amet lorem ipsum d
- **Events in prepare_context**: `closed topic 2, card: dolor / ipsu / sit`, `new topic 3`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🔴 closed | `dolor / ipsu / sit` | t1 lorem ipsum dolor sit amet lorem ipsu | dolor, ipsu, sit, lorem, amet | `[0]` | 0 |
| 2 | 🔴 closed | `dolor / ipsu / sit` | t2 lorem ipsum dolor sit amet lorem ipsu | dolor, ipsu, sit, lorem, amet | `[1]` | 1 |
| 3 | 🟢 open | `t3 lorem ipsum dolor sit amet lorem ipsu` | - | - | `[2]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L1** | 1 | 20 |  | t1 lorem ipsum dolor sit amet lorem ipsu |
| 1 | **L1** | 2 | 20 |  | t2 lorem ipsum dolor sit amet lorem ipsu |
| 2 | **L1** | 3 | 20 | yes | t3 lorem ipsum dolor sit amet lorem ipsu |

**L1 after prepare_context**: `[####################....|.........|.....]` 50/100 tok (50%); `|` marks low 60% / high 85%; L1 pages `[0, 1, 2]`, L2 pages `[]`

**L1 after record_reply**: `[########################|.........|.....]` 60/100 tok (60%); `|` marks low 60% / high 85%; L1 pages `[0, 1, 2]`, L2 pages `[]`

**Prompt sent to the model**

> **[USER]** t1 lorem ipsum dolor sit amet lorem ipsu
> **[ASSISTANT]** lorem ipsum dolor sit amet lorem ipsum d
> **[USER]** t2 lorem ipsum dolor sit amet lorem ipsu
> **[ASSISTANT]** lorem ipsum dolor sit amet lorem ipsum d
> **[USER]** t3 lorem ipsum dolor sit amet lorem ipsu

<details><summary>Page contents (final state)</summary>

- **L1 page 0** (topic 1, 20 tok)
  - `user`: t1 lorem ipsum dolor sit amet lorem ipsu
  - `assistant`: lorem ipsum dolor sit amet lorem ipsum d
- **L1 page 1** (topic 2, 20 tok)
  - `user`: t2 lorem ipsum dolor sit amet lorem ipsu
  - `assistant`: lorem ipsum dolor sit amet lorem ipsum d
- **L1 page 2** (topic 3, 20 tok, OPEN)
  - `user`: t3 lorem ipsum dolor sit amet lorem ipsu
  - `assistant`: lorem ipsum dolor sit amet lorem ipsum d

</details>

### Turn 4: "t4 lorem ipsum dolor sit amet lorem ipsu"

- **Reply (assistant)**: lorem ipsum dolor sit amet lorem ipsum d
- **Events in prepare_context**: `closed topic 3, card: dolor / ipsu / sit`, `new topic 4`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🔴 closed | `dolor / ipsu / sit` | t1 lorem ipsum dolor sit amet lorem ipsu | dolor, ipsu, sit, lorem, amet | `[0]` | 0 |
| 2 | 🔴 closed | `dolor / ipsu / sit` | t2 lorem ipsum dolor sit amet lorem ipsu | dolor, ipsu, sit, lorem, amet | `[1]` | 1 |
| 3 | 🔴 closed | `dolor / ipsu / sit` | t3 lorem ipsum dolor sit amet lorem ipsu | dolor, ipsu, sit, lorem, amet | `[2]` | 2 |
| 4 | 🟢 open | `t4 lorem ipsum dolor sit amet lorem ipsu` | - | - | `[3]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L1** | 1 | 20 |  | t1 lorem ipsum dolor sit amet lorem ipsu |
| 1 | **L1** | 2 | 20 |  | t2 lorem ipsum dolor sit amet lorem ipsu |
| 2 | **L1** | 3 | 20 |  | t3 lorem ipsum dolor sit amet lorem ipsu |
| 3 | **L1** | 4 | 20 | yes | t4 lorem ipsum dolor sit amet lorem ipsu |

**L1 after prepare_context**: `[########################|###......|.....]` 70/100 tok (70%); `|` marks low 60% / high 85%; L1 pages `[0, 1, 2, 3]`, L2 pages `[]`

**L1 after record_reply**: `[########################|#######..|.....]` 80/100 tok (80%); `|` marks low 60% / high 85%; L1 pages `[0, 1, 2, 3]`, L2 pages `[]`

**Prompt sent to the model**

> **[USER]** t1 lorem ipsum dolor sit amet lorem ipsu
> **[ASSISTANT]** lorem ipsum dolor sit amet lorem ipsum d
> **[USER]** t2 lorem ipsum dolor sit amet lorem ipsu
> **[ASSISTANT]** lorem ipsum dolor sit amet lorem ipsum d
> **[USER]** t3 lorem ipsum dolor sit amet lorem ipsu
> **[ASSISTANT]** lorem ipsum dolor sit amet lorem ipsum d
> **[USER]** t4 lorem ipsum dolor sit amet lorem ipsu

<details><summary>Page contents (final state)</summary>

- **L1 page 0** (topic 1, 20 tok)
  - `user`: t1 lorem ipsum dolor sit amet lorem ipsu
  - `assistant`: lorem ipsum dolor sit amet lorem ipsum d
- **L1 page 1** (topic 2, 20 tok)
  - `user`: t2 lorem ipsum dolor sit amet lorem ipsu
  - `assistant`: lorem ipsum dolor sit amet lorem ipsum d
- **L1 page 2** (topic 3, 20 tok)
  - `user`: t3 lorem ipsum dolor sit amet lorem ipsu
  - `assistant`: lorem ipsum dolor sit amet lorem ipsum d
- **L1 page 3** (topic 4, 20 tok, OPEN)
  - `user`: t4 lorem ipsum dolor sit amet lorem ipsu
  - `assistant`: lorem ipsum dolor sit amet lorem ipsum d

</details>

### Turn 5: "t5 lorem ipsum dolor sit amet lorem ipsu"

- **Reply (assistant)**: lorem ipsum dolor si
- **Events in prepare_context**: `closed topic 4, card: dolor / ipsu / sit`, `new topic 5`, `move page 1: L1 -> L2`, `move page 3: L1 -> L2`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🔴 closed | `dolor / ipsu / sit` | t1 lorem ipsum dolor sit amet lorem ipsu | dolor, ipsu, sit, lorem, amet | `[0]` | 0 |
| 2 | 🔴 closed | `dolor / ipsu / sit` | t2 lorem ipsum dolor sit amet lorem ipsu | dolor, ipsu, sit, lorem, amet | `[1]` | 1 |
| 3 | 🔴 closed | `dolor / ipsu / sit` | t3 lorem ipsum dolor sit amet lorem ipsu | dolor, ipsu, sit, lorem, amet | `[2]` | 2 |
| 4 | 🔴 closed | `dolor / ipsu / sit` | t4 lorem ipsum dolor sit amet lorem ipsu | dolor, ipsu, sit, lorem, amet | `[3]` | 3 |
| 5 | 🟢 open | `t5 lorem ipsum dolor sit amet lorem ipsu` | - | - | `[4]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L1** | 1 | 20 |  | t1 lorem ipsum dolor sit amet lorem ipsu |
| 1 | **L2** | 2 | 20 |  | t2 lorem ipsum dolor sit amet lorem ipsu |
| 2 | **L1** | 3 | 20 |  | t3 lorem ipsum dolor sit amet lorem ipsu |
| 3 | **L2** | 4 | 20 |  | t4 lorem ipsum dolor sit amet lorem ipsu |
| 4 | **L1** | 5 | 15 | yes | t5 lorem ipsum dolor sit amet lorem ipsu |

**L1 after prepare_context**: `[####################....|.........|.....]` 50/100 tok (50%); `|` marks low 60% / high 85%; L1 pages `[0, 2, 4]`, L2 pages `[1, 3]`

**L1 after record_reply**: `[######################..|.........|.....]` 55/100 tok (55%); `|` marks low 60% / high 85%; L1 pages `[0, 2, 4]`, L2 pages `[1, 3]`

**Prompt sent to the model**

> **[USER]** t1 lorem ipsum dolor sit amet lorem ipsu
> **[ASSISTANT]** lorem ipsum dolor sit amet lorem ipsum d
> **[SYSTEM]** [earlier messages omitted]
> **[USER]** t3 lorem ipsum dolor sit amet lorem ipsu
> **[ASSISTANT]** lorem ipsum dolor sit amet lorem ipsum d
> **[SYSTEM]** [earlier messages omitted]
> **[USER]** t5 lorem ipsum dolor sit amet lorem ipsu

<details><summary>Page contents (final state)</summary>

- **L1 page 0** (topic 1, 20 tok)
  - `user`: t1 lorem ipsum dolor sit amet lorem ipsu
  - `assistant`: lorem ipsum dolor sit amet lorem ipsum d
- **L1 page 2** (topic 3, 20 tok)
  - `user`: t3 lorem ipsum dolor sit amet lorem ipsu
  - `assistant`: lorem ipsum dolor sit amet lorem ipsum d
- **L1 page 4** (topic 5, 15 tok, OPEN)
  - `user`: t5 lorem ipsum dolor sit amet lorem ipsu
  - `assistant`: lorem ipsum dolor si
- **L2 page 1** (topic 2, 20 tok)
  - `user`: t2 lorem ipsum dolor sit amet lorem ipsu
  - `assistant`: lorem ipsum dolor sit amet lorem ipsum d
- **L2 page 3** (topic 4, 20 tok)
  - `user`: t4 lorem ipsum dolor sit amet lorem ipsu
  - `assistant`: lorem ipsum dolor sit amet lorem ipsum d

</details>

- ✅ demoted in score order: topic 2 (0.05, page 1) then topic 4 (0.10, page 3) — got `[1, 3]`, expected `[1, 3]`
- ✅ the older pages 0 and 2 (score 0.25) survive over newer, less relevant ones — got `[0, 2, 4]`, expected `[0, 2, 4]`

**Result: ✅ PASS**  (2 checks, 0 failed, 5 turns, 0.00s)

---

## P6 — everything protected leaves L1 over high water

> If every page is protected, L1 may stay above high-water but must not crash or demote protected pages.

### Turn 1: "a lorem ipsum dolor sit amet lorem ipsum"

- **Reply (assistant)**: lorem ipsum dolor sit amet lorem ipsum d
- **Events in prepare_context**: `new topic 1`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🟢 open | `a lorem ipsum dolor sit amet lorem ipsum` | - | - | `[0]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L1** | 1 | 20 | yes | a lorem ipsum dolor sit amet lorem ipsum |

**L1 after prepare_context**: `[#######.....|.......|...................]` 10/60 tok (17%); `|` marks low 30% / high 50%; L1 pages `[0]`, L2 pages `[]`

**L1 after record_reply**: `[############|.......|...................]` 20/60 tok (33%); `|` marks low 30% / high 50%; L1 pages `[0]`, L2 pages `[]`

**Prompt sent to the model**

> **[USER]** a lorem ipsum dolor sit amet lorem ipsum

<details><summary>Page contents (final state)</summary>

- **L1 page 0** (topic 1, 20 tok, OPEN)
  - `user`: a lorem ipsum dolor sit amet lorem ipsum
  - `assistant`: lorem ipsum dolor sit amet lorem ipsum d

</details>

### Turn 2: "b lorem ipsum dolor sit amet lorem ipsum"

- **Reply (assistant)**: lorem ipsum dolor sit amet lorem ipsum d
- **Events in prepare_context**: `closed topic 1, card: dolor / sit / lorem`, `new topic 2`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🔴 closed | `dolor / sit / lorem` | a lorem ipsum dolor sit amet lorem ipsum | dolor, sit, lorem, amet, ipsum | `[0]` | 0 |
| 2 | 🟢 open | `b lorem ipsum dolor sit amet lorem ipsum` | - | - | `[1]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L1** | 1 | 20 |  | a lorem ipsum dolor sit amet lorem ipsum |
| 1 | **L1** | 2 | 20 | yes | b lorem ipsum dolor sit amet lorem ipsum |

**L1 after prepare_context**: `[############|#######|...................]` 30/60 tok (50%); `|` marks low 30% / high 50%; L1 pages `[0, 1]`, L2 pages `[]`

**L1 after record_reply**: `[############|#######|######.............]` 40/60 tok (67%); `|` marks low 30% / high 50%; L1 pages `[0, 1]`, L2 pages `[]`

**Prompt sent to the model**

> **[USER]** a lorem ipsum dolor sit amet lorem ipsum
> **[ASSISTANT]** lorem ipsum dolor sit amet lorem ipsum d
> **[USER]** b lorem ipsum dolor sit amet lorem ipsum

<details><summary>Page contents (final state)</summary>

- **L1 page 0** (topic 1, 20 tok)
  - `user`: a lorem ipsum dolor sit amet lorem ipsum
  - `assistant`: lorem ipsum dolor sit amet lorem ipsum d
- **L1 page 1** (topic 2, 20 tok, OPEN)
  - `user`: b lorem ipsum dolor sit amet lorem ipsum
  - `assistant`: lorem ipsum dolor sit amet lorem ipsum d

</details>

### Turn 3: "c lorem ipsum dolor "

- **Reply (assistant)**: lorem ipsum dolor si
- **Events in prepare_context**: `closed topic 2, card: dolor / sit / lorem`, `new topic 3`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🔴 closed | `dolor / sit / lorem` | a lorem ipsum dolor sit amet lorem ipsum | dolor, sit, lorem, amet, ipsum | `[0]` | 0 |
| 2 | 🔴 closed | `dolor / sit / lorem` | b lorem ipsum dolor sit amet lorem ipsum | dolor, sit, lorem, amet, ipsum | `[1]` | 1 |
| 3 | 🟢 open | `c lorem ipsum dolor ` | - | - | `[2]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L1** | 1 | 20 |  | a lorem ipsum dolor sit amet lorem ipsum |
| 1 | **L1** | 2 | 20 |  | b lorem ipsum dolor sit amet lorem ipsum |
| 2 | **L1** | 3 | 10 | yes | c lorem ipsum dolor  |

**L1 after prepare_context**: `[############|#######|#########..........]` 45/60 tok (75%); `|` marks low 30% / high 50%; L1 pages `[0, 1, 2]`, L2 pages `[]`

**L1 after record_reply**: `[############|#######|############.......]` 50/60 tok (83%); `|` marks low 30% / high 50%; L1 pages `[0, 1, 2]`, L2 pages `[]`

**Prompt sent to the model**

> **[USER]** a lorem ipsum dolor sit amet lorem ipsum
> **[ASSISTANT]** lorem ipsum dolor sit amet lorem ipsum d
> **[USER]** b lorem ipsum dolor sit amet lorem ipsum
> **[ASSISTANT]** lorem ipsum dolor sit amet lorem ipsum d
> **[USER]** c lorem ipsum dolor 

<details><summary>Page contents (final state)</summary>

- **L1 page 0** (topic 1, 20 tok)
  - `user`: a lorem ipsum dolor sit amet lorem ipsum
  - `assistant`: lorem ipsum dolor sit amet lorem ipsum d
- **L1 page 1** (topic 2, 20 tok)
  - `user`: b lorem ipsum dolor sit amet lorem ipsum
  - `assistant`: lorem ipsum dolor sit amet lorem ipsum d
- **L1 page 2** (topic 3, 10 tok, OPEN)
  - `user`: c lorem ipsum dolor 
  - `assistant`: lorem ipsum dolor si

</details>

- ✅ no page moved on the last turn — got `[]`, expected `[]`
- ✅ L1 is at 83%, above the 50% high-water mark
- ✅ all pages are still in L1 — got `[0, 1, 2]`, expected `[0, 1, 2]`

**Result: ✅ PASS**  (3 checks, 0 failed, 3 turns, 0.00s)

---

## T1 — replies and tool results go into the open page

> record_reply stores assistant and tool messages in order in the open page, and tokens are counted.

### Turn 1: "read the file lorem ipsum dolor sit amet"

- **Reply (assistant)**: calling readFile lorem i
- **Events in prepare_context**: `new topic 1`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🟢 open | `read the file lorem ipsum dolor sit amet` | - | - | `[0]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L1** | 1 | 16 | yes | read the file lorem ipsum dolor sit amet |

**L1 after prepare_context**: `[#...........................|.....|.....]` 10/500 tok (2%); `|` marks low 70% / high 85%; L1 pages `[0]`, L2 pages `[]`

**L1 after record_reply**: `[#...........................|.....|.....]` 16/500 tok (3%); `|` marks low 70% / high 85%; L1 pages `[0]`, L2 pages `[]`

**Prompt sent to the model**

> **[USER]** read the file lorem ipsum dolor sit amet

<details><summary>Page contents (final state)</summary>

- **L1 page 0** (topic 1, 16 tok, OPEN)
  - `user`: read the file lorem ipsum dolor sit amet
  - `assistant`: calling readFile lorem i

</details>

### Turn 2: "ok lorem ipsum dolor sit"

- **Reply (tool)**: file contents lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum ...
- **Events in prepare_context**: none
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🟢 open | `read the file lorem ipsum dolor sit amet` | - | - | `[0]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L1** | 1 | 52 | yes | read the file lorem ipsum dolor sit amet |

**L1 after prepare_context**: `[##..........................|.....|.....]` 22/500 tok (4%); `|` marks low 70% / high 85%; L1 pages `[0]`, L2 pages `[]`

**L1 after record_reply**: `[####........................|.....|.....]` 52/500 tok (10%); `|` marks low 70% / high 85%; L1 pages `[0]`, L2 pages `[]`

**Prompt sent to the model**

> **[USER]** read the file lorem ipsum dolor sit amet
> **[ASSISTANT]** calling readFile lorem i
> **[USER]** ok lorem ipsum dolor sit

<details><summary>Page contents (final state)</summary>

- **L1 page 0** (topic 1, 52 tok, OPEN)
  - `user`: read the file lorem ipsum dolor sit amet
  - `assistant`: calling readFile lorem i
  - `user`: ok lorem ipsum dolor sit
  - `tool`: file contents lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor s...

</details>

- ✅ roles are preserved in order — got `['user', 'assistant', 'user', 'tool']`, expected `['user', 'assistant', 'user', 'tool']`
- ✅ page tokens are the sum of all four messages — got `52`, expected `52`
- ✅ L1 used_tokens reflects the tool result — got `52`, expected `52`

**Result: ✅ PASS**  (3 checks, 0 failed, 2 turns, 0.00s)

---

## T2 — a needed page survives the reply

> A page brought in for this turn must not be evicted again when the reply is recorded (no thrash).

### Turn 1: "old lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit ..."

- **Reply (assistant)**: lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet...
- **Events in prepare_context**: `new topic 1`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🟢 open | `old lorem ipsum dolor sit amet lorem ...` | - | - | `[0]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L1** | 1 | 76 | yes | old lorem ipsum dolor sit amet lorem ipsum dolo... |

**L1 after prepare_context**: `[################......|.....|...........]` 40/100 tok (40%); `|` marks low 55% / high 70%; L1 pages `[0]`, L2 pages `[]`

**L1 after record_reply**: `[######################|#####|#..........]` 76/100 tok (76%); `|` marks low 55% / high 70%; L1 pages `[0]`, L2 pages `[]`

**Prompt sent to the model**

> **[USER]** old lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem...

<details><summary>Page contents (final state)</summary>

- **L1 page 0** (topic 1, 76 tok, OPEN)
  - `user`: old lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lo...
  - `assistant`: lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ...

</details>

### Turn 2: "other lorem ipsum dolor sit amet lorem ipsum dol"

- **Reply (assistant)**: lorem ipsum dolor sit amet lorem ipsum d
- **Events in prepare_context**: `closed topic 1, card: ips / dolor / sit`, `new topic 2`, `move page 0: L1 -> L2`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🔴 closed | `ips / dolor / sit` | old lorem ipsum dolor sit amet lorem ipsum dolor sit amet... | ips, dolor, sit, lorem, old | `[0]` | 0 |
| 2 | 🟢 open | `other lorem ipsum dolor sit amet lore...` | - | - | `[1]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L2** | 1 | 76 |  | old lorem ipsum dolor sit amet lorem ipsum dolo... |
| 1 | **L1** | 2 | 22 | yes | other lorem ipsum dolor sit amet lorem ipsum dol |

**L1 after prepare_context**: `[#####.................|.....|...........]` 12/100 tok (12%); `|` marks low 55% / high 70%; L1 pages `[1]`, L2 pages `[0]`

**L1 after record_reply**: `[#########.............|.....|...........]` 22/100 tok (22%); `|` marks low 55% / high 70%; L1 pages `[1]`, L2 pages `[0]`

**Prompt sent to the model**

> **[SYSTEM]** [earlier messages omitted]
> **[USER]** other lorem ipsum dolor sit amet lorem ipsum dol

<details><summary>Page contents (final state)</summary>

- **L1 page 1** (topic 2, 22 tok, OPEN)
  - `user`: other lorem ipsum dolor sit amet lorem ipsum dol
  - `assistant`: lorem ipsum dolor sit amet lorem ipsum d
- **L2 page 0** (topic 1, 76 tok)
  - `user`: old lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lo...
  - `assistant`: lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ...

</details>

- ✅ setup: the 76-token page 0 is in L2 — got `'L2'`, expected `'L2'`
### Turn 3: "back lorem ipsum dolor sit amet lorem ipsum dolor si"

- **Reply (assistant)**: lorem ipsum dolor sit amet lorem
- **Events in prepare_context**: `closed topic 2, card: dol / dolor / sit`, `return to topic 1 (ips / dolor / sit)`, `move page 1: L1 -> L2`, `move page 0: L2 -> L1`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🟢 open | `ips / dolor / sit` | old lorem ipsum dolor sit amet lorem ipsum dolor sit amet... | ips, dolor, sit, lorem, old | `[0, 2]` | 0 |
| 2 | 🔴 closed | `dol / dolor / sit` | other lorem ipsum dolor sit amet lorem ipsum dol | dol, dolor, sit, lorem, amet | `[1]` | 1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L1** | 1 | 76 |  | old lorem ipsum dolor sit amet lorem ipsum dolo... |
| 1 | **L2** | 2 | 22 |  | other lorem ipsum dolor sit amet lorem ipsum dol |
| 2 | **L1** | 1 | 21 | yes | back lorem ipsum dolor sit amet lorem ipsum dol... |

**L1 after prepare_context**: `[######################|#####|#######....]` 89/100 tok (89%); `|` marks low 55% / high 70%; L1 pages `[0, 2]`, L2 pages `[1]`

**L1 after record_reply**: `[######################|#####|##########.]` 97/100 tok (97%); `|` marks low 55% / high 70%; L1 pages `[0, 2]`, L2 pages `[1]`

**Prompt sent to the model**

> **[USER]** old lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem...
> **[ASSISTANT]** lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ips...
> **[SYSTEM]** [earlier messages omitted]
> **[USER]** back lorem ipsum dolor sit amet lorem ipsum dolor si

<details><summary>Page contents (final state)</summary>

- **L1 page 0** (topic 1, 76 tok)
  - `user`: old lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lo...
  - `assistant`: lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ...
- **L1 page 2** (topic 1, 21 tok, OPEN)
  - `user`: back lorem ipsum dolor sit amet lorem ipsum dolor si
  - `assistant`: lorem ipsum dolor sit amet lorem
- **L2 page 1** (topic 2, 22 tok)
  - `user`: other lorem ipsum dolor sit amet lorem ipsum dol
  - `assistant`: lorem ipsum dolor sit amet lorem ipsum d

</details>

- ✅ page 0 is still in L1 after the reply was recorded — got `'L1'`, expected `'L1'`
- ✅ page 0 moved exactly once this turn — got `1`, expected `1`

**Result: ✅ PASS**  (3 checks, 0 failed, 3 turns, 0.00s)

---

## T3 — a reply that does not fit is not lost

> The model's reply must always be stored. If L1 is packed with needed pages, something must give (and be logged).

### Turn 1: "old lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit ..."

- **Reply (assistant)**: lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet...
- **Events in prepare_context**: `new topic 1`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🟢 open | `old lorem ipsum dolor sit amet lorem ...` | - | - | `[0]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L1** | 1 | 76 | yes | old lorem ipsum dolor sit amet lorem ipsum dolo... |

**L1 after prepare_context**: `[################......|.....|...........]` 40/100 tok (40%); `|` marks low 55% / high 70%; L1 pages `[0]`, L2 pages `[]`

**L1 after record_reply**: `[######################|#####|#..........]` 76/100 tok (76%); `|` marks low 55% / high 70%; L1 pages `[0]`, L2 pages `[]`

**Prompt sent to the model**

> **[USER]** old lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem...

<details><summary>Page contents (final state)</summary>

- **L1 page 0** (topic 1, 76 tok, OPEN)
  - `user`: old lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lo...
  - `assistant`: lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ...

</details>

### Turn 2: "other lorem ipsum dolor sit amet lorem ipsum dol"

- **Reply (assistant)**: lorem ipsum dolor sit amet lorem ipsum d
- **Events in prepare_context**: `closed topic 1, card: ips / dolor / sit`, `new topic 2`, `move page 0: L1 -> L2`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🔴 closed | `ips / dolor / sit` | old lorem ipsum dolor sit amet lorem ipsum dolor sit amet... | ips, dolor, sit, lorem, old | `[0]` | 0 |
| 2 | 🟢 open | `other lorem ipsum dolor sit amet lore...` | - | - | `[1]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L2** | 1 | 76 |  | old lorem ipsum dolor sit amet lorem ipsum dolo... |
| 1 | **L1** | 2 | 22 | yes | other lorem ipsum dolor sit amet lorem ipsum dol |

**L1 after prepare_context**: `[#####.................|.....|...........]` 12/100 tok (12%); `|` marks low 55% / high 70%; L1 pages `[1]`, L2 pages `[0]`

**L1 after record_reply**: `[#########.............|.....|...........]` 22/100 tok (22%); `|` marks low 55% / high 70%; L1 pages `[1]`, L2 pages `[0]`

**Prompt sent to the model**

> **[SYSTEM]** [earlier messages omitted]
> **[USER]** other lorem ipsum dolor sit amet lorem ipsum dol

<details><summary>Page contents (final state)</summary>

- **L1 page 1** (topic 2, 22 tok, OPEN)
  - `user`: other lorem ipsum dolor sit amet lorem ipsum dol
  - `assistant`: lorem ipsum dolor sit amet lorem ipsum d
- **L2 page 0** (topic 1, 76 tok)
  - `user`: old lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lo...
  - `assistant`: lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ...

</details>

### Turn 3: "back lorem ipsum dolor sit amet lorem ipsum dolor si"

- **Reply (assistant)**: this reply is 15 tokens lorem ipsum dolor sit amet lorem ips
- **Events in prepare_context**: `closed topic 2, card: dol / dolor / sit`, `return to topic 1 (ips / dolor / sit)`, `move page 1: L1 -> L2`, `move page 0: L2 -> L1`
- **Events in record_reply**: `forced demotion of page 0: no room for reply`, `move page 0: L1 -> L2`
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🟢 open | `ips / dolor / sit` | old lorem ipsum dolor sit amet lorem ipsum dolor sit amet... | ips, dolor, sit, lorem, old | `[0, 2]` | 0 |
| 2 | 🔴 closed | `dol / dolor / sit` | other lorem ipsum dolor sit amet lorem ipsum dol | dol, dolor, sit, lorem, amet | `[1]` | 1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L2** | 1 | 76 |  | old lorem ipsum dolor sit amet lorem ipsum dolo... |
| 1 | **L2** | 2 | 22 |  | other lorem ipsum dolor sit amet lorem ipsum dol |
| 2 | **L1** | 1 | 28 | yes | back lorem ipsum dolor sit amet lorem ipsum dol... |

**L1 after prepare_context**: `[######################|#####|#######....]` 89/100 tok (89%); `|` marks low 55% / high 70%; L1 pages `[0, 2]`, L2 pages `[1]`

**L1 after record_reply**: `[###########...........|.....|...........]` 28/100 tok (28%); `|` marks low 55% / high 70%; L1 pages `[2]`, L2 pages `[0, 1]`

**Prompt sent to the model**

> **[USER]** old lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem...
> **[ASSISTANT]** lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ips...
> **[SYSTEM]** [earlier messages omitted]
> **[USER]** back lorem ipsum dolor sit amet lorem ipsum dolor si

<details><summary>Page contents (final state)</summary>

- **L1 page 2** (topic 1, 28 tok, OPEN)
  - `user`: back lorem ipsum dolor sit amet lorem ipsum dolor si
  - `assistant`: this reply is 15 tokens lorem ipsum dolor sit amet lorem ips
- **L2 page 0** (topic 1, 76 tok)
  - `user`: old lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lo...
  - `assistant`: lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ...
- **L2 page 1** (topic 2, 22 tok)
  - `user`: other lorem ipsum dolor sit amet lorem ipsum dol
  - `assistant`: lorem ipsum dolor sit amet lorem ipsum d

</details>

- ✅ record_reply did not raise (got no error) — otherwise the reply is lost
- ✅ the reply is stored in the open page
- ✅ any forced eviction of a needed page is visible in the events

**Result: ✅ PASS**  (3 checks, 0 failed, 3 turns, 0.00s)

---

## T4 — reply reserve makes room before the model call

> With reply_reserve=N, prepare_context frees N tokens by demoting unprotected pages.

### Turn 1 [reply_reserve=40]: "a lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit am"

- **Reply (assistant)**: lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet
- **Events in prepare_context**: `new topic 1`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🟢 open | `a lorem ipsum dolor sit amet lorem ip...` | - | - | `[0]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L1** | 1 | 40 | yes | a lorem ipsum dolor sit amet lorem ipsum dolor ... |

**L1 after prepare_context**: `[########....................|.....|.....]` 20/100 tok (20%); `|` marks low 70% / high 85%; L1 pages `[0]`, L2 pages `[]`

**L1 after record_reply**: `[################............|.....|.....]` 40/100 tok (40%); `|` marks low 70% / high 85%; L1 pages `[0]`, L2 pages `[]`

**Prompt sent to the model**

> **[USER]** a lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit am

<details><summary>Page contents (final state)</summary>

- **L1 page 0** (topic 1, 40 tok, OPEN)
  - `user`: a lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit am
  - `assistant`: lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet

</details>

### Turn 2 [reply_reserve=40]: "b lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit am..."

- **Reply (assistant)**: lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet...
- **Events in prepare_context**: `closed topic 1, card: dolor / sit / lorem`, `new topic 2`, `move page 0: L1 -> L2`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🔴 closed | `dolor / sit / lorem` | a lorem ipsum dolor sit amet lorem ipsum dolor sit amet l... | dolor, sit, lorem, amet, ipsum | `[0]` | 0 |
| 2 | 🟢 open | `b lorem ipsum dolor sit amet lorem ip...` | - | - | `[1]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L2** | 1 | 40 |  | a lorem ipsum dolor sit amet lorem ipsum dolor ... |
| 1 | **L1** | 2 | 70 | yes | b lorem ipsum dolor sit amet lorem ipsum dolor ... |

**L1 after prepare_context**: `[############................|.....|.....]` 30/100 tok (30%); `|` marks low 70% / high 85%; L1 pages `[1]`, L2 pages `[0]`

**L1 after record_reply**: `[############################|.....|.....]` 70/100 tok (70%); `|` marks low 70% / high 85%; L1 pages `[1]`, L2 pages `[0]`

**Prompt sent to the model**

> **[SYSTEM]** [earlier messages omitted]
> **[USER]** b lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsu

<details><summary>Page contents (final state)</summary>

- **L1 page 1** (topic 2, 70 tok, OPEN)
  - `user`: b lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lore...
  - `assistant`: lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ...
- **L2 page 0** (topic 1, 40 tok)
  - `user`: a lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit am
  - `assistant`: lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet

</details>

- ✅ page 0 was demoted during prepare_context to reserve room — got `[(0, 'L1', 'L2')]`, expected `[(0, 'L1', 'L2')]`
- ✅ free tokens after prepare_context: 70 (>= 40)
- ✅ the 40-token reply then fitted without any eviction — got `[]`, expected `[]`
### Turn 1 [reply_reserve=0]: "a lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit am"

- **Reply (assistant)**: lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet
- **Events in prepare_context**: `new topic 1`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🟢 open | `a lorem ipsum dolor sit amet lorem ip...` | - | - | `[0]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L1** | 1 | 40 | yes | a lorem ipsum dolor sit amet lorem ipsum dolor ... |

**L1 after prepare_context**: `[########....................|.....|.....]` 20/100 tok (20%); `|` marks low 70% / high 85%; L1 pages `[0]`, L2 pages `[]`

**L1 after record_reply**: `[################............|.....|.....]` 40/100 tok (40%); `|` marks low 70% / high 85%; L1 pages `[0]`, L2 pages `[]`

**Prompt sent to the model**

> **[USER]** a lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit am

<details><summary>Page contents (final state)</summary>

- **L1 page 0** (topic 1, 40 tok, OPEN)
  - `user`: a lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit am
  - `assistant`: lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet

</details>

### Turn 2 [reply_reserve=0]: "b lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit am..."

- **Reply (assistant)**: lorem ipsum dolor si
- **Events in prepare_context**: `closed topic 1, card: dolor / sit / lorem`, `new topic 2`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🔴 closed | `dolor / sit / lorem` | a lorem ipsum dolor sit amet lorem ipsum dolor sit amet l... | dolor, sit, lorem, amet, ipsum | `[0]` | 0 |
| 2 | 🟢 open | `b lorem ipsum dolor sit amet lorem ip...` | - | - | `[1]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L1** | 1 | 40 |  | a lorem ipsum dolor sit amet lorem ipsum dolor ... |
| 1 | **L1** | 2 | 35 | yes | b lorem ipsum dolor sit amet lorem ipsum dolor ... |

**L1 after prepare_context**: `[############################|.....|.....]` 70/100 tok (70%); `|` marks low 70% / high 85%; L1 pages `[0, 1]`, L2 pages `[]`

**L1 after record_reply**: `[############################|#....|.....]` 75/100 tok (75%); `|` marks low 70% / high 85%; L1 pages `[0, 1]`, L2 pages `[]`

**Prompt sent to the model**

> **[USER]** a lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit am
> **[ASSISTANT]** lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet
> **[USER]** b lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsu

<details><summary>Page contents (final state)</summary>

- **L1 page 0** (topic 1, 40 tok)
  - `user`: a lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit am
  - `assistant`: lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet
- **L1 page 1** (topic 2, 35 tok, OPEN)
  - `user`: b lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lore...
  - `assistant`: lorem ipsum dolor si

</details>

- ✅ control: with no reserve nothing was demoted — got `[]`, expected `[]`

**Result: ✅ PASS**  (4 checks, 0 failed, 4 turns, 0.00s)

---

## T5 — message larger than L1 is rejected cleanly

> A message bigger than the whole L1 raises L1FullError before anything changes.

### Turn 1: "a lorem ipsum dolor sit amet lorem ipsum"

- **Reply (assistant)**: lorem ipsum dolor sit amet lorem ipsum d
- **Events in prepare_context**: `new topic 1`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🟢 open | `a lorem ipsum dolor sit amet lorem ipsum` | - | - | `[0]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L1** | 1 | 20 | yes | a lorem ipsum dolor sit amet lorem ipsum |

**L1 after prepare_context**: `[####........................|.....|.....]` 10/100 tok (10%); `|` marks low 70% / high 85%; L1 pages `[0]`, L2 pages `[]`

**L1 after record_reply**: `[########....................|.....|.....]` 20/100 tok (20%); `|` marks low 70% / high 85%; L1 pages `[0]`, L2 pages `[]`

**Prompt sent to the model**

> **[USER]** a lorem ipsum dolor sit amet lorem ipsum

<details><summary>Page contents (final state)</summary>

- **L1 page 0** (topic 1, 20 tok, OPEN)
  - `user`: a lorem ipsum dolor sit amet lorem ipsum
  - `assistant`: lorem ipsum dolor sit amet lorem ipsum d

</details>

### Turn 2: "huge lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit..."

- ❌ **Raised** `L1FullError: User message (150 tokens) exceeds L1 max capacity (100)`
- **Events in prepare_context**: none
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🟢 open | `a lorem ipsum dolor sit amet lorem ipsum` | - | - | `[0]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L1** | 1 | 20 | yes | a lorem ipsum dolor sit amet lorem ipsum |

**L1 after prepare_context**: `[########....................|.....|.....]` 20/100 tok (20%); `|` marks low 70% / high 85%; L1 pages `[0]`, L2 pages `[]`

**L1 after record_reply**: `[########....................|.....|.....]` 20/100 tok (20%); `|` marks low 70% / high 85%; L1 pages `[0]`, L2 pages `[]`

**Prompt sent to the model**

> *(not produced)*

<details><summary>Page contents (final state)</summary>

- **L1 page 0** (topic 1, 20 tok, OPEN)
  - `user`: a lorem ipsum dolor sit amet lorem ipsum
  - `assistant`: lorem ipsum dolor sit amet lorem ipsum d

</details>

- ✅ L1FullError raised (got L1FullError)
- ✅ topics, pages and page table are exactly as before — got `'{"l1": [[0, 1, 20, true]], "l2": [], "open_seq": 0, "open_topic": 1, "table": {"0": "L1"}, "topics": [{"covered": -1, "entities": [], "facts": [], "id": 1, "label": "a lorem ipsum dolor sit amet lorem ipsum", "open": true, "pages": [0]}]}'`, expected `'{"l1": [[0, 1, 20, true]], "l2": [], "open_seq": 0, "open_topic": 1, "table": {"0": "L1"}, "topics": [{"covered": -1, "entities": [], "facts": [], "id": 1, "label": "a lorem ipsum dolor sit amet lorem ipsum", "open": true, "pages": [0]}]}'`

**Result: ✅ PASS**  (2 checks, 0 failed, 2 turns, 0.00s)

---

## T6 — a message that cannot fit leaves state untouched

> If a message fits the window but not the free space, the failed call must not leave a half-applied turn.

### Turn 1 [continue]: "a lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor"

- **Reply (assistant)**: lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor s
- **Events in prepare_context**: `new topic 1`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🟢 open | `a lorem ipsum dolor sit amet lorem ip...` | - | - | `[0]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L1** | 1 | 50 | yes | a lorem ipsum dolor sit amet lorem ipsum dolor ... |

**L1 after prepare_context**: `[#################...........|.....|.....]` 25/60 tok (42%); `|` marks low 70% / high 85%; L1 pages `[0]`, L2 pages `[]`

**L1 after record_reply**: `[############################|####.|.....]` 50/60 tok (83%); `|` marks low 70% / high 85%; L1 pages `[0]`, L2 pages `[]`

**Prompt sent to the model**

> **[USER]** a lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor

<details><summary>Page contents (final state)</summary>

- **L1 page 0** (topic 1, 50 tok, OPEN)
  - `user`: a lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lore...
  - `assistant`: lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ...

</details>

### Turn 2 [continue]: "b lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit am..."

- ❌ **Raised** `L1FullError: User message (30 tokens) cannot fit in L1`
- **Events in prepare_context**: none
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🟢 open | `a lorem ipsum dolor sit amet lorem ip...` | - | - | `[0]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L1** | 1 | 50 | yes | a lorem ipsum dolor sit amet lorem ipsum dolor ... |

**L1 after prepare_context**: `[############################|####.|.....]` 50/60 tok (83%); `|` marks low 70% / high 85%; L1 pages `[0]`, L2 pages `[]`

**L1 after record_reply**: `[############################|####.|.....]` 50/60 tok (83%); `|` marks low 70% / high 85%; L1 pages `[0]`, L2 pages `[]`

**Prompt sent to the model**

> *(not produced)*

<details><summary>Page contents (final state)</summary>

- **L1 page 0** (topic 1, 50 tok, OPEN)
  - `user`: a lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lore...
  - `assistant`: lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ...

</details>

- ✅ continue variant: L1FullError raised (nothing can be evicted)
- ✅ continue variant: state unchanged after the failure — got `'{"l1": [[0, 1, 50, true]], "l2": [], "open_seq": 0, "open_topic": 1, "table": {"0": "L1"}, "topics": [{"covered": -1, "entities": [], "facts": [], "id": 1, "label": "a lorem ipsum dolor sit amet lorem ipsum dolor sit amet lore", "open": true, "pages": [0]}]}'`, expected `'{"l1": [[0, 1, 50, true]], "l2": [], "open_seq": 0, "open_topic": 1, "table": {"0": "L1"}, "topics": [{"covered": -1, "entities": [], "facts": [], "id": 1, "label": "a lorem ipsum dolor sit amet lorem ipsum dolor sit amet lore", "open": true, "pages": [0]}]}'`
### Turn 1 [new topic]: "a lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor"

- **Reply (assistant)**: lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor s
- **Events in prepare_context**: `new topic 1`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🟢 open | `a lorem ipsum dolor sit amet lorem ip...` | - | - | `[0]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L1** | 1 | 50 | yes | a lorem ipsum dolor sit amet lorem ipsum dolor ... |

**L1 after prepare_context**: `[#################...........|.....|.....]` 25/60 tok (42%); `|` marks low 70% / high 85%; L1 pages `[0]`, L2 pages `[]`

**L1 after record_reply**: `[############################|####.|.....]` 50/60 tok (83%); `|` marks low 70% / high 85%; L1 pages `[0]`, L2 pages `[]`

**Prompt sent to the model**

> **[USER]** a lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor

<details><summary>Page contents (final state)</summary>

- **L1 page 0** (topic 1, 50 tok, OPEN)
  - `user`: a lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lore...
  - `assistant`: lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ...

</details>

### Turn 2 [new topic]: "b lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit am..."

- ❌ **Raised** `L1FullError: User message (30 tokens) cannot fit in L1`
- **Events in prepare_context**: none
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🟢 open | `a lorem ipsum dolor sit amet lorem ip...` | - | - | `[0]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L1** | 1 | 50 | yes | a lorem ipsum dolor sit amet lorem ipsum dolor ... |

**L1 after prepare_context**: `[############################|####.|.....]` 50/60 tok (83%); `|` marks low 70% / high 85%; L1 pages `[0]`, L2 pages `[]`

**L1 after record_reply**: `[############################|####.|.....]` 50/60 tok (83%); `|` marks low 70% / high 85%; L1 pages `[0]`, L2 pages `[]`

**Prompt sent to the model**

> *(not produced)*

<details><summary>Page contents (final state)</summary>

- **L1 page 0** (topic 1, 50 tok, OPEN)
  - `user`: a lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lore...
  - `assistant`: lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ...

</details>

- ✅ new-topic variant: L1FullError raised (both pages are protected)
- ✅ new-topic variant: state unchanged (the old topic must not be closed and an empty page opened by a call that failed) — got `'{"l1": [[0, 1, 50, true]], "l2": [], "open_seq": 0, "open_topic": 1, "table": {"0": "L1"}, "topics": [{"covered": -1, "entities": [], "facts": [], "id": 1, "label": "a lorem ipsum dolor sit amet lorem ipsum dolor sit amet lore", "open": true, "pages": [0]}]}'`, expected `'{"l1": [[0, 1, 50, true]], "l2": [], "open_seq": 0, "open_topic": 1, "table": {"0": "L1"}, "topics": [{"covered": -1, "entities": [], "facts": [], "id": 1, "label": "a lorem ipsum dolor sit amet lorem ipsum dolor sit amet lore", "open": true, "pages": [0]}]}'`

**Result: ✅ PASS**  (4 checks, 0 failed, 4 turns, 0.00s)

---

## C1 — second close updates the card with only new pages

> On a second close the card writer gets only pages newer than covered_through, and facts accumulate.

### Turn 1: "docker containers lorem ipsum dolor sit amet lor"

- **Reply (assistant)**: lorem ipsum dolor sit am
- **Events in prepare_context**: `new topic 1`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🟢 open | `docker containers lorem ipsum dolor s...` | - | - | `[0]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L1** | 1 | 18 | yes | docker containers lorem ipsum dolor sit amet lor |

**L1 after prepare_context**: `[#...........................|.....|.....]` 12/500 tok (2%); `|` marks low 70% / high 85%; L1 pages `[0]`, L2 pages `[]`

**L1 after record_reply**: `[#...........................|.....|.....]` 18/500 tok (4%); `|` marks low 70% / high 85%; L1 pages `[0]`, L2 pages `[]`

**Prompt sent to the model**

> **[USER]** docker containers lorem ipsum dolor sit amet lor

<details><summary>Page contents (final state)</summary>

- **L1 page 0** (topic 1, 18 tok, OPEN)
  - `user`: docker containers lorem ipsum dolor sit amet lor
  - `assistant`: lorem ipsum dolor sit am

</details>

### Turn 2: "carbonara lorem ipsum dolor sit amet lorem ipsum"

- **Reply (assistant)**: lorem ipsum dolor sit am
- **Events in prepare_context**: `closed topic 1, card: container / dolor / sit`, `new topic 2`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🔴 closed | `container / dolor / sit` | docker containers lorem ipsum dolor sit amet lor | container, dolor, sit, lorem, docker | `[0]` | 0 |
| 2 | 🟢 open | `carbonara lorem ipsum dolor sit amet ...` | - | - | `[1]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L1** | 1 | 18 |  | docker containers lorem ipsum dolor sit amet lor |
| 1 | **L1** | 2 | 18 | yes | carbonara lorem ipsum dolor sit amet lorem ipsum |

**L1 after prepare_context**: `[##..........................|.....|.....]` 30/500 tok (6%); `|` marks low 70% / high 85%; L1 pages `[0, 1]`, L2 pages `[]`

**L1 after record_reply**: `[###.........................|.....|.....]` 36/500 tok (7%); `|` marks low 70% / high 85%; L1 pages `[0, 1]`, L2 pages `[]`

**Prompt sent to the model**

> **[USER]** docker containers lorem ipsum dolor sit amet lor
> **[ASSISTANT]** lorem ipsum dolor sit am
> **[USER]** carbonara lorem ipsum dolor sit amet lorem ipsum

<details><summary>Page contents (final state)</summary>

- **L1 page 0** (topic 1, 18 tok)
  - `user`: docker containers lorem ipsum dolor sit amet lor
  - `assistant`: lorem ipsum dolor sit am
- **L1 page 1** (topic 2, 18 tok, OPEN)
  - `user`: carbonara lorem ipsum dolor sit amet lorem ipsum
  - `assistant`: lorem ipsum dolor sit am

</details>

### Turn 3: "docker compose networks lorem ipsum dolor sit am"

- **Reply (assistant)**: lorem ipsum dolor sit am
- **Events in prepare_context**: `closed topic 2, card: dolor / sit / lorem`, `return to topic 1 (container / dolor / sit)`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🟢 open | `container / dolor / sit` | docker containers lorem ipsum dolor sit amet lor | container, dolor, sit, lorem, docker | `[0, 2]` | 0 |
| 2 | 🔴 closed | `dolor / sit / lorem` | carbonara lorem ipsum dolor sit amet lorem ipsum | dolor, sit, lorem, carbonara, amet | `[1]` | 1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L1** | 1 | 18 |  | docker containers lorem ipsum dolor sit amet lor |
| 1 | **L1** | 2 | 18 |  | carbonara lorem ipsum dolor sit amet lorem ipsum |
| 2 | **L1** | 1 | 18 | yes | docker compose networks lorem ipsum dolor sit am |

**L1 after prepare_context**: `[####........................|.....|.....]` 48/500 tok (10%); `|` marks low 70% / high 85%; L1 pages `[0, 1, 2]`, L2 pages `[]`

**L1 after record_reply**: `[####........................|.....|.....]` 54/500 tok (11%); `|` marks low 70% / high 85%; L1 pages `[0, 1, 2]`, L2 pages `[]`

**Prompt sent to the model**

> **[USER]** docker containers lorem ipsum dolor sit amet lor
> **[ASSISTANT]** lorem ipsum dolor sit am
> **[USER]** carbonara lorem ipsum dolor sit amet lorem ipsum
> **[ASSISTANT]** lorem ipsum dolor sit am
> **[USER]** docker compose networks lorem ipsum dolor sit am

<details><summary>Page contents (final state)</summary>

- **L1 page 0** (topic 1, 18 tok)
  - `user`: docker containers lorem ipsum dolor sit amet lor
  - `assistant`: lorem ipsum dolor sit am
- **L1 page 1** (topic 2, 18 tok)
  - `user`: carbonara lorem ipsum dolor sit amet lorem ipsum
  - `assistant`: lorem ipsum dolor sit am
- **L1 page 2** (topic 1, 18 tok, OPEN)
  - `user`: docker compose networks lorem ipsum dolor sit am
  - `assistant`: lorem ipsum dolor sit am

</details>

### Turn 4: "stocks lorem ipsum dolor sit amet lorem ipsum do"

- **Reply (assistant)**: lorem ipsum dolor sit am
- **Events in prepare_context**: `closed topic 1, card: container / dolor / sit`, `new topic 3`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🔴 closed | `container / dolor / sit` | docker containers lorem ipsum dolor sit amet lor; docker ... | container, dolor, sit, lorem, docker | `[0, 2]` | 2 |
| 2 | 🔴 closed | `dolor / sit / lorem` | carbonara lorem ipsum dolor sit amet lorem ipsum | dolor, sit, lorem, carbonara, amet | `[1]` | 1 |
| 3 | 🟢 open | `stocks lorem ipsum dolor sit amet lor...` | - | - | `[3]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L1** | 1 | 18 |  | docker containers lorem ipsum dolor sit amet lor |
| 1 | **L1** | 2 | 18 |  | carbonara lorem ipsum dolor sit amet lorem ipsum |
| 2 | **L1** | 1 | 18 |  | docker compose networks lorem ipsum dolor sit am |
| 3 | **L1** | 3 | 18 | yes | stocks lorem ipsum dolor sit amet lorem ipsum do |

**L1 after prepare_context**: `[#####.......................|.....|.....]` 66/500 tok (13%); `|` marks low 70% / high 85%; L1 pages `[0, 1, 2, 3]`, L2 pages `[]`

**L1 after record_reply**: `[######......................|.....|.....]` 72/500 tok (14%); `|` marks low 70% / high 85%; L1 pages `[0, 1, 2, 3]`, L2 pages `[]`

**Prompt sent to the model**

> **[USER]** docker containers lorem ipsum dolor sit amet lor
> **[ASSISTANT]** lorem ipsum dolor sit am
> **[USER]** carbonara lorem ipsum dolor sit amet lorem ipsum
> **[ASSISTANT]** lorem ipsum dolor sit am
> **[USER]** docker compose networks lorem ipsum dolor sit am
> **[ASSISTANT]** lorem ipsum dolor sit am
> **[USER]** stocks lorem ipsum dolor sit amet lorem ipsum do

<details><summary>Page contents (final state)</summary>

- **L1 page 0** (topic 1, 18 tok)
  - `user`: docker containers lorem ipsum dolor sit amet lor
  - `assistant`: lorem ipsum dolor sit am
- **L1 page 1** (topic 2, 18 tok)
  - `user`: carbonara lorem ipsum dolor sit amet lorem ipsum
  - `assistant`: lorem ipsum dolor sit am
- **L1 page 2** (topic 1, 18 tok)
  - `user`: docker compose networks lorem ipsum dolor sit am
  - `assistant`: lorem ipsum dolor sit am
- **L1 page 3** (topic 3, 18 tok, OPEN)
  - `user`: stocks lorem ipsum dolor sit amet lorem ipsum do
  - `assistant`: lorem ipsum dolor sit am

</details>

- ✅ card writer received page [0] (topic 1), [1] (topic 2), then only [2] for topic 1's second close — got `[[0], [1], [2]]`, expected `[[0], [1], [2]]`
- ✅ the second call was given the previous card (covered_through 0) — got `0`, expected `0`
- ✅ key_facts grew 1 -> 2
- ✅ old and new facts are both present
- ✅ covered_through advanced from 0 to 2 — got `(0, 2)`, expected `(0, 2)`

**Result: ✅ PASS**  (5 checks, 0 failed, 4 turns, 0.00s)

---

## C2 — closing a topic with pages in L2 still works

> A topic's earlier pages may sit in L2 when it closes; the card writer must still receive them.

### Turn 1: "x lorem ipsum dolor sit amet lorem ipsum"

- **Reply (assistant)**: lorem ipsum dolor sit amet lorem ipsum d
- **Events in prepare_context**: `new topic 1`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🟢 open | `x lorem ipsum dolor sit amet lorem ipsum` | - | - | `[0]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L1** | 1 | 20 | yes | x lorem ipsum dolor sit amet lorem ipsum |

**L1 after prepare_context**: `[####........|.......|...................]` 10/100 tok (10%); `|` marks low 30% / high 50%; L1 pages `[0]`, L2 pages `[]`

**L1 after record_reply**: `[########....|.......|...................]` 20/100 tok (20%); `|` marks low 30% / high 50%; L1 pages `[0]`, L2 pages `[]`

**Prompt sent to the model**

> **[USER]** x lorem ipsum dolor sit amet lorem ipsum

<details><summary>Page contents (final state)</summary>

- **L1 page 0** (topic 1, 20 tok, OPEN)
  - `user`: x lorem ipsum dolor sit amet lorem ipsum
  - `assistant`: lorem ipsum dolor sit amet lorem ipsum d

</details>

### Turn 2: "y lorem ipsum dolor sit amet lorem ipsum"

- **Reply (assistant)**: lorem ipsum dolor sit amet lorem ipsum d
- **Events in prepare_context**: none
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🟢 open | `x lorem ipsum dolor sit amet lorem ipsum` | - | - | `[0, 1]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L1** | 1 | 20 |  | x lorem ipsum dolor sit amet lorem ipsum |
| 1 | **L1** | 1 | 20 | yes | y lorem ipsum dolor sit amet lorem ipsum |

**L1 after prepare_context**: `[############|.......|...................]` 30/100 tok (30%); `|` marks low 30% / high 50%; L1 pages `[0, 1]`, L2 pages `[]`

**L1 after record_reply**: `[############|###....|...................]` 40/100 tok (40%); `|` marks low 30% / high 50%; L1 pages `[0, 1]`, L2 pages `[]`

**Prompt sent to the model**

> **[USER]** x lorem ipsum dolor sit amet lorem ipsum
> **[ASSISTANT]** lorem ipsum dolor sit amet lorem ipsum d
> **[USER]** y lorem ipsum dolor sit amet lorem ipsum

<details><summary>Page contents (final state)</summary>

- **L1 page 0** (topic 1, 20 tok)
  - `user`: x lorem ipsum dolor sit amet lorem ipsum
  - `assistant`: lorem ipsum dolor sit amet lorem ipsum d
- **L1 page 1** (topic 1, 20 tok, OPEN)
  - `user`: y lorem ipsum dolor sit amet lorem ipsum
  - `assistant`: lorem ipsum dolor sit amet lorem ipsum d

</details>

### Turn 3: "z lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit am..."

- **Reply (assistant)**: lorem ipsum dolor sit amet lorem ipsum d
- **Events in prepare_context**: `closed topic 1, card: dolor / sit / lorem`, `new topic 2`, `move page 0: L1 -> L2`, `move page 1: L1 -> L2`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🔴 closed | `dolor / sit / lorem` | x lorem ipsum dolor sit amet lorem ipsum; y lorem ipsum d... | dolor, sit, lorem, amet, ipsum | `[0, 1]` | 1 |
| 2 | 🟢 open | `z lorem ipsum dolor sit amet lorem ip...` | - | - | `[2]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L2** | 1 | 20 |  | x lorem ipsum dolor sit amet lorem ipsum |
| 1 | **L2** | 1 | 20 |  | y lorem ipsum dolor sit amet lorem ipsum |
| 2 | **L1** | 2 | 40 | yes | z lorem ipsum dolor sit amet lorem ipsum dolor ... |

**L1 after prepare_context**: `[############|.......|...................]` 30/100 tok (30%); `|` marks low 30% / high 50%; L1 pages `[2]`, L2 pages `[0, 1]`

**L1 after record_reply**: `[############|###....|...................]` 40/100 tok (40%); `|` marks low 30% / high 50%; L1 pages `[2]`, L2 pages `[0, 1]`

**Prompt sent to the model**

> **[SYSTEM]** [earlier messages omitted]
> **[USER]** z lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsu

<details><summary>Page contents (final state)</summary>

- **L1 page 2** (topic 2, 40 tok, OPEN)
  - `user`: z lorem ipsum dolor sit amet lorem ipsum dolor sit amet lorem ipsum dolor sit amet lore...
  - `assistant`: lorem ipsum dolor sit amet lorem ipsum d
- **L2 page 0** (topic 1, 20 tok)
  - `user`: x lorem ipsum dolor sit amet lorem ipsum
  - `assistant`: lorem ipsum dolor sit amet lorem ipsum d
- **L2 page 1** (topic 1, 20 tok)
  - `user`: y lorem ipsum dolor sit amet lorem ipsum
  - `assistant`: lorem ipsum dolor sit amet lorem ipsum d

</details>

- ✅ the card writer got both pages of topic 1 at close — got `[0, 1]`, expected `[0, 1]`
- ✅ covered_through is the last page of the topic

**Result: ✅ PASS**  (2 checks, 0 failed, 3 turns, 0.00s)

---

## D1 — KeywordSegmenter rules

> The offline segmenter continues on overlap, returns on a better old-topic match, and starts new otherwise.

- ✅ no open topic: new — got `'new'`, expected `'new'`
- ✅ message overlapping the open topic: continue — got `'continue'`, expected `'continue'`
- ✅ message matching a closed topic better than the open one: return to it — got `('return', 1)`, expected `('return', 1)`
- ✅ unrelated message: new — got `'new'`, expected `'new'`
- ✅ very short message with no overlap: continue — got `'continue'`, expected `'continue'`

**Result: ✅ PASS**  (5 checks, 0 failed, 0 turns, 0.00s)

---

## D2 — KeywordRouter scores

> Router score is min(1, 2 x word overlap), 0 for unrelated topics.

- ✅ no shared words: 0.0 — got `0.0`, expected `0.0`
- ✅ 1 of 4 words shared: 0.5 — got `0.5`, expected `0.5`
- ✅ everything shared: capped at 1.0 — got `1.0`, expected `1.0`
- ✅ no topics: empty result — got `{}`, expected `{}`

**Result: ✅ PASS**  (4 checks, 0 failed, 0 turns, 0.00s)

---

## D3 — FakeCardWriter edge cases

> The offline card writer handles empty input, dedupes facts and caps entities.

- ✅ no pages and no old card: default card — got `'Empty topic'`, expected `'Empty topic'`
- ✅ no pages: the old card is returned unchanged
- ✅ duplicate facts are removed — got `['Alpha beta gamma']`, expected `['Alpha beta gamma']`
- ✅ covered_through is the highest page seq — got `5`, expected `5`
- ✅ entities are capped at 10

**Result: ✅ PASS**  (5 checks, 0 failed, 0 turns, 0.00s)

---

## D4 — JevSegmenter decision rules

> JevSegmenter turns Jev's answer into a decision: confidence floor, strict return threshold, question shape.

- ✅ asks one Choice question with id 'segment'
- ✅ options: continue, new and one return:<id> per closed topic — got `['continue', 'new', 'return:1', 'return:2']`, expected `['continue', 'new', 'return:1', 'return:2']`
- ✅ state contains the recent messages and the newest one
- ✅ choice 'continue' -> continue — got `'continue'`, expected `'continue'`
- ✅ choice 'new' -> new — got `'new'`, expected `'new'`
- ✅ confident return:2 -> return to topic 2 — got `2`, expected `2`
- ✅ return with probability 0.7 < 0.8: treated as new (strict merge) — got `'new'`, expected `'new'`
- ✅ confidence 0.5 < 0.6: falls back to continue — got `'continue'`, expected `'continue'`
- ✅ return without a probability: treated as new, no crash — got `'new'`, expected `'new'`
- ✅ no open topic: new — got `'new'`, expected `'new'`
- ✅ and Jev is not called at all in that case — got `[]`, expected `[]`

**Result: ✅ PASS**  (11 checks, 0 failed, 0 turns, 0.00s)

---

## D5 — JevRouter builds one question per topic

> JevRouter asks one Noul question per closed topic and returns their probabilities.

- ✅ returns {topic_id: probability} — got `{1: 0.9, 4: 0.1}`, expected `{1: 0.9, 4: 0.1}`
- ✅ one Noul question per topic with id topic_<id> — got `[('noul', 'topic_1'), ('noul', 'topic_4')]`, expected `[('noul', 'topic_1'), ('noul', 'topic_4')]`
- ✅ the statement includes the topic card text
- ✅ all topics are asked in ONE call — got `1`, expected `1`
- ✅ no topics: empty result — got `{}`, expected `{}`
- ✅ and Jev is not called — got `[]`, expected `[]`
- ✅ the placeholder JevClient.ask raises NotImplementedError (raised NotImplementedError)

**Result: ✅ PASS**  (7 checks, 0 failed, 0 turns, 0.00s)

---

## D6 — LLMCardWriter prompt and parsing

> LLMCardWriter builds the prompt from the old card and new pages and parses the JSON reply.

- ✅ card fields come from the JSON; covered_through is the max page seq — got `('Food', ['likes mango'], ['mango'], 6)`, expected `('Food', ['likes mango'], ['mango'], 6)`
- ✅ prompt contains the previous card and the new messages
- ✅ prompt starts with the card-writing rules
- ✅ no pages and no card: default card, no LLM call — got `'Empty topic'`, expected `'Empty topic'`
- ✅ no pages: old card returned unchanged
- ✅ invalid JSON from the LLM raises JSONDecodeError (raised JSONDecodeError)
- ✅ a reply missing fields raises KeyError (raised KeyError)
- ✅ the placeholder _call_llm raises NotImplementedError (raised NotImplementedError)

**Result: ✅ PASS**  (8 checks, 0 failed, 0 turns, 0.00s)

---

## E1 — realistic conversation with the keyword deciders

> Six turns across four subjects with a small L1: invariants hold every turn and old context returns when asked for.

### Turn 1: "Tell me about Goa beaches Anjuna nightlife and Baga water sports"

- **Reply (assistant)**: Anjuna has trance parties. Baga offers parasailing.
- **Events in prepare_context**: `new topic 1`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🟢 open | `Tell me about Goa beaches Anjuna nigh...` | - | - | `[0]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L1** | 1 | 28 | yes | Tell me about Goa beaches Anjuna nightlife and ... |

**L1 after prepare_context**: `[#####...............|.......|...........]` 16/130 tok (12%); `|` marks low 50% / high 70%; L1 pages `[0]`, L2 pages `[]`

**L1 after record_reply**: `[#########...........|.......|...........]` 28/130 tok (22%); `|` marks low 50% / high 70%; L1 pages `[0]`, L2 pages `[]`

**Prompt sent to the model**

> **[USER]** Tell me about Goa beaches Anjuna nightlife and Baga water sports

<details><summary>Page contents (final state)</summary>

- **L1 page 0** (topic 1, 28 tok, OPEN)
  - `user`: Tell me about Goa beaches Anjuna nightlife and Baga water sports
  - `assistant`: Anjuna has trance parties. Baga offers parasailing.

</details>

### Turn 2: "Explain quantum computing qubits superposition entanglement"

- **Reply (assistant)**: Qubits use superposition and entanglement.
- **Events in prepare_context**: `closed topic 1, card: beach / nightlife / trance`, `new topic 2`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🔴 closed | `beach / nightlife / trance` | Tell me about Goa beaches Anjuna nightlife and Baga water... | beach, nightlife, trance, parasailing... | `[0]` | 0 |
| 2 | 🟢 open | `Explain quantum computing qubits supe...` | - | - | `[1]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L1** | 1 | 28 |  | Tell me about Goa beaches Anjuna nightlife and ... |
| 1 | **L1** | 2 | 24 | yes | Explain quantum computing qubits superposition ... |

**L1 after prepare_context**: `[#############.......|.......|...........]` 42/130 tok (32%); `|` marks low 50% / high 70%; L1 pages `[0, 1]`, L2 pages `[]`

**L1 after record_reply**: `[################....|.......|...........]` 52/130 tok (40%); `|` marks low 50% / high 70%; L1 pages `[0, 1]`, L2 pages `[]`

**Prompt sent to the model**

> **[USER]** Tell me about Goa beaches Anjuna nightlife and Baga water sports
> **[ASSISTANT]** Anjuna has trance parties. Baga offers parasailing.
> **[USER]** Explain quantum computing qubits superposition entanglement

<details><summary>Page contents (final state)</summary>

- **L1 page 0** (topic 1, 28 tok)
  - `user`: Tell me about Goa beaches Anjuna nightlife and Baga water sports
  - `assistant`: Anjuna has trance parties. Baga offers parasailing.
- **L1 page 1** (topic 2, 24 tok, OPEN)
  - `user`: Explain quantum computing qubits superposition entanglement
  - `assistant`: Qubits use superposition and entanglement.

</details>

### Turn 3: "How do Docker containers and Kubernetes orchestration work"

- **Reply (assistant)**: Docker packages apps. Kubernetes schedules containers.
- **Events in prepare_context**: `closed topic 2, card: entanglement / explain / qubit`, `new topic 3`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🔴 closed | `beach / nightlife / trance` | Tell me about Goa beaches Anjuna nightlife and Baga water... | beach, nightlife, trance, parasailing... | `[0]` | 0 |
| 2 | 🔴 closed | `entanglement / explain / qubit` | Explain quantum computing qubits superposition entanglement | entanglement, explain, qubit, computi... | `[1]` | 1 |
| 3 | 🟢 open | `How do Docker containers and Kubernet...` | - | - | `[2]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L1** | 1 | 28 |  | Tell me about Goa beaches Anjuna nightlife and ... |
| 1 | **L1** | 2 | 24 |  | Explain quantum computing qubits superposition ... |
| 2 | **L1** | 3 | 27 | yes | How do Docker containers and Kubernetes orchest... |

**L1 after prepare_context**: `[####################|.......|...........]` 66/130 tok (51%); `|` marks low 50% / high 70%; L1 pages `[0, 1, 2]`, L2 pages `[]`

**L1 after record_reply**: `[####################|###....|...........]` 79/130 tok (61%); `|` marks low 50% / high 70%; L1 pages `[0, 1, 2]`, L2 pages `[]`

**Prompt sent to the model**

> **[USER]** Tell me about Goa beaches Anjuna nightlife and Baga water sports
> **[ASSISTANT]** Anjuna has trance parties. Baga offers parasailing.
> **[USER]** Explain quantum computing qubits superposition entanglement
> **[ASSISTANT]** Qubits use superposition and entanglement.
> **[USER]** How do Docker containers and Kubernetes orchestration work

<details><summary>Page contents (final state)</summary>

- **L1 page 0** (topic 1, 28 tok)
  - `user`: Tell me about Goa beaches Anjuna nightlife and Baga water sports
  - `assistant`: Anjuna has trance parties. Baga offers parasailing.
- **L1 page 1** (topic 2, 24 tok)
  - `user`: Explain quantum computing qubits superposition entanglement
  - `assistant`: Qubits use superposition and entanglement.
- **L1 page 2** (topic 3, 27 tok, OPEN)
  - `user`: How do Docker containers and Kubernetes orchestration work
  - `assistant`: Docker packages apps. Kubernetes schedules containers.

</details>

### Turn 4: "Which Goa beach has the best Anjuna nightlife"

- **Reply (assistant)**: Anjuna is the nightlife hub.
- **Events in prepare_context**: `closed topic 3, card: container / kubernete / orchestration`, `return to topic 1 (beach / nightlife / trance)`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🟢 open | `beach / nightlife / trance` | Tell me about Goa beaches Anjuna nightlife and Baga water... | beach, nightlife, trance, parasailing... | `[0, 3]` | 0 |
| 2 | 🔴 closed | `entanglement / explain / qubit` | Explain quantum computing qubits superposition entanglement | entanglement, explain, qubit, computi... | `[1]` | 1 |
| 3 | 🔴 closed | `container / kubernete / orchestration` | How do Docker containers and Kubernetes orchestration work | container, kubernete, orchestration, ... | `[2]` | 2 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L1** | 1 | 28 |  | Tell me about Goa beaches Anjuna nightlife and ... |
| 1 | **L1** | 2 | 24 |  | Explain quantum computing qubits superposition ... |
| 2 | **L1** | 3 | 27 |  | How do Docker containers and Kubernetes orchest... |
| 3 | **L1** | 1 | 18 | yes | Which Goa beach has the best Anjuna nightlife |

**L1 after prepare_context**: `[####################|#######|...........]` 90/130 tok (69%); `|` marks low 50% / high 70%; L1 pages `[0, 1, 2, 3]`, L2 pages `[]`

**L1 after record_reply**: `[####################|#######|#..........]` 97/130 tok (75%); `|` marks low 50% / high 70%; L1 pages `[0, 1, 2, 3]`, L2 pages `[]`

**Prompt sent to the model**

> **[USER]** Tell me about Goa beaches Anjuna nightlife and Baga water sports
> **[ASSISTANT]** Anjuna has trance parties. Baga offers parasailing.
> **[USER]** Explain quantum computing qubits superposition entanglement
> **[ASSISTANT]** Qubits use superposition and entanglement.
> **[USER]** How do Docker containers and Kubernetes orchestration work
> **[ASSISTANT]** Docker packages apps. Kubernetes schedules containers.
> **[USER]** Which Goa beach has the best Anjuna nightlife

<details><summary>Page contents (final state)</summary>

- **L1 page 0** (topic 1, 28 tok)
  - `user`: Tell me about Goa beaches Anjuna nightlife and Baga water sports
  - `assistant`: Anjuna has trance parties. Baga offers parasailing.
- **L1 page 1** (topic 2, 24 tok)
  - `user`: Explain quantum computing qubits superposition entanglement
  - `assistant`: Qubits use superposition and entanglement.
- **L1 page 2** (topic 3, 27 tok)
  - `user`: How do Docker containers and Kubernetes orchestration work
  - `assistant`: Docker packages apps. Kubernetes schedules containers.
- **L1 page 3** (topic 1, 18 tok, OPEN)
  - `user`: Which Goa beach has the best Anjuna nightlife
  - `assistant`: Anjuna is the nightlife hub.

</details>

### Turn 5: "Can Kubernetes scale Docker containers automatically"

- **Reply (assistant)**: Yes, with autoscaling.
- **Events in prepare_context**: `closed topic 1, card: beach / nightlife / trance`, `return to topic 3 (container / kubernete / orchestration)`, `move page 0: L1 -> L2`, `move page 1: L1 -> L2`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🔴 closed | `beach / nightlife / trance` | Tell me about Goa beaches Anjuna nightlife and Baga water... | beach, nightlife, trance, parasailing... | `[0, 3]` | 3 |
| 2 | 🔴 closed | `entanglement / explain / qubit` | Explain quantum computing qubits superposition entanglement | entanglement, explain, qubit, computi... | `[1]` | 1 |
| 3 | 🟢 open | `container / kubernete / orchestration` | How do Docker containers and Kubernetes orchestration work | container, kubernete, orchestration, ... | `[2, 4]` | 2 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L2** | 1 | 28 |  | Tell me about Goa beaches Anjuna nightlife and ... |
| 1 | **L2** | 2 | 24 |  | Explain quantum computing qubits superposition ... |
| 2 | **L1** | 3 | 27 |  | How do Docker containers and Kubernetes orchest... |
| 3 | **L1** | 1 | 18 |  | Which Goa beach has the best Anjuna nightlife |
| 4 | **L1** | 3 | 18 | yes | Can Kubernetes scale Docker containers automati... |

**L1 after prepare_context**: `[##################..|.......|...........]` 58/130 tok (45%); `|` marks low 50% / high 70%; L1 pages `[2, 3, 4]`, L2 pages `[0, 1]`

**L1 after record_reply**: `[###################.|.......|...........]` 63/130 tok (48%); `|` marks low 50% / high 70%; L1 pages `[2, 3, 4]`, L2 pages `[0, 1]`

**Prompt sent to the model**

> **[SYSTEM]** [earlier messages omitted]
> **[USER]** How do Docker containers and Kubernetes orchestration work
> **[ASSISTANT]** Docker packages apps. Kubernetes schedules containers.
> **[USER]** Which Goa beach has the best Anjuna nightlife
> **[ASSISTANT]** Anjuna is the nightlife hub.
> **[USER]** Can Kubernetes scale Docker containers automatically

<details><summary>Page contents (final state)</summary>

- **L1 page 2** (topic 3, 27 tok)
  - `user`: How do Docker containers and Kubernetes orchestration work
  - `assistant`: Docker packages apps. Kubernetes schedules containers.
- **L1 page 3** (topic 1, 18 tok)
  - `user`: Which Goa beach has the best Anjuna nightlife
  - `assistant`: Anjuna is the nightlife hub.
- **L1 page 4** (topic 3, 18 tok, OPEN)
  - `user`: Can Kubernetes scale Docker containers automatically
  - `assistant`: Yes, with autoscaling.
- **L2 page 0** (topic 1, 28 tok)
  - `user`: Tell me about Goa beaches Anjuna nightlife and Baga water sports
  - `assistant`: Anjuna has trance parties. Baga offers parasailing.
- **L2 page 1** (topic 2, 24 tok)
  - `user`: Explain quantum computing qubits superposition entanglement
  - `assistant`: Qubits use superposition and entanglement.

</details>

### Turn 6: "What is the GDP of India and its growth rate"

- **Reply (assistant)**: About 3.7 trillion dollars.
- **Events in prepare_context**: `closed topic 3, card: container / kubernete / orchestration`, `new topic 4`
- **Events in record_reply**: none
- ✅ **Invariants**: all 11 hold

**Topic table**

| ID | Status | Label | Key facts | Entities | Pages | Covered |
|:-:|:-:|:--|:--|:--|:-:|:-:|
| 1 | 🔴 closed | `beach / nightlife / trance` | Tell me about Goa beaches Anjuna nightlife and Baga water... | beach, nightlife, trance, parasailing... | `[0, 3]` | 3 |
| 2 | 🔴 closed | `entanglement / explain / qubit` | Explain quantum computing qubits superposition entanglement | entanglement, explain, qubit, computi... | `[1]` | 1 |
| 3 | 🔴 closed | `container / kubernete / orchestration` | How do Docker containers and Kubernetes orchestration wor... | container, kubernete, orchestration, ... | `[2, 4]` | 4 |
| 4 | 🟢 open | `What is the GDP of India and its grow...` | - | - | `[5]` | -1 |

**Page table**

| Page | Layer | Topic | Tokens | Open | First message |
|:-:|:-:|:-:|:-:|:-:|:--|
| 0 | **L2** | 1 | 28 |  | Tell me about Goa beaches Anjuna nightlife and ... |
| 1 | **L2** | 2 | 24 |  | Explain quantum computing qubits superposition ... |
| 2 | **L1** | 3 | 27 |  | How do Docker containers and Kubernetes orchest... |
| 3 | **L1** | 1 | 18 |  | Which Goa beach has the best Anjuna nightlife |
| 4 | **L1** | 3 | 18 |  | Can Kubernetes scale Docker containers automati... |
| 5 | **L1** | 4 | 17 | yes | What is the GDP of India and its growth rate |

**L1 after prepare_context**: `[####################|##.....|...........]` 74/130 tok (57%); `|` marks low 50% / high 70%; L1 pages `[2, 3, 4, 5]`, L2 pages `[0, 1]`

**L1 after record_reply**: `[####################|####...|...........]` 80/130 tok (62%); `|` marks low 50% / high 70%; L1 pages `[2, 3, 4, 5]`, L2 pages `[0, 1]`

**Prompt sent to the model**

> **[SYSTEM]** [earlier messages omitted]
> **[USER]** How do Docker containers and Kubernetes orchestration work
> **[ASSISTANT]** Docker packages apps. Kubernetes schedules containers.
> **[USER]** Which Goa beach has the best Anjuna nightlife
> **[ASSISTANT]** Anjuna is the nightlife hub.
> **[USER]** Can Kubernetes scale Docker containers automatically
> **[ASSISTANT]** Yes, with autoscaling.
> **[USER]** What is the GDP of India and its growth rate

<details><summary>Page contents (final state)</summary>

- **L1 page 2** (topic 3, 27 tok)
  - `user`: How do Docker containers and Kubernetes orchestration work
  - `assistant`: Docker packages apps. Kubernetes schedules containers.
- **L1 page 3** (topic 1, 18 tok)
  - `user`: Which Goa beach has the best Anjuna nightlife
  - `assistant`: Anjuna is the nightlife hub.
- **L1 page 4** (topic 3, 18 tok)
  - `user`: Can Kubernetes scale Docker containers automatically
  - `assistant`: Yes, with autoscaling.
- **L1 page 5** (topic 4, 17 tok, OPEN)
  - `user`: What is the GDP of India and its growth rate
  - `assistant`: About 3.7 trillion dollars.
- **L2 page 0** (topic 1, 28 tok)
  - `user`: Tell me about Goa beaches Anjuna nightlife and Baga water sports
  - `assistant`: Anjuna has trance parties. Baga offers parasailing.
- **L2 page 1** (topic 2, 24 tok)
  - `user`: Explain quantum computing qubits superposition entanglement
  - `assistant`: Qubits use superposition and entanglement.

</details>

- ✅ four subjects became four topics (Goa, quantum, Docker, GDP); the returns reused old topics — got `4`, expected `4`
- ✅ turn 4 (back to Goa): the old Goa answer is in the prompt again
- ✅ turn 5 (back to Docker): the old Docker answer is in the prompt again
- ✅ L1 never exceeded its maximum
*If the two 'old answer is in the prompt' checks fail, look at that turn's topic table: the keyword fakes may have mis-segmented, which points at the fakes rather than the manager.*


**Result: ✅ PASS**  (4 checks, 0 failed, 6 turns, 0.00s)

---

## E2 — random conversations never break the invariants

> Fuzz: random topics, returns, scores and message sizes over 8 seeds x 120 turns. Invariants must hold after every step.

- ✅ seed 0: 120 turns, invariants held
- ✅ seed 1: 120 turns, invariants held
- ✅ seed 2: 120 turns, invariants held
- ✅ seed 3: 120 turns, invariants held
- ✅ seed 4: 120 turns, invariants held
- ✅ seed 5: 120 turns, invariants held
- ✅ seed 6: 120 turns, invariants held
- ✅ seed 7: 120 turns, invariants held
*960 random turns; 124 of them raised L1FullError (allowed, but see T3/T6: a raised error must not lose the reply or half-apply a turn).*


**Result: ✅ PASS**  (8 checks, 0 failed, 0 turns, 0.74s)
