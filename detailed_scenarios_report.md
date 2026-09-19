# PRISM Detailed Scenario Tests Report

> **Generated**: `2026-09-19 22:59:10`  
> **Scenarios**: 1 Total | **1 Passed** | **0 Failed**

## Executive Summary

| # | Scenario Name | Turns | Status |
|:---:|:---|:---:|:---:|
| 03 | [Return to Old Topic](#return-to-old-topic) | 3 | ✅ PASS |

---

<a id="return-to-old-topic"></a>
## Scenario 3: Return to Old Topic

**Status**: `PASSED ✅`

### Turn 1: "Let's plan a trip to Goa with beaches and hotels"

> 🤖 **Assistant Reply**: *Great choice! Goa has Anjuna, Baga, and Calangute beaches. For hotels I recommend Taj Fort Aguada.*

**System Events**:
- `new topic 1`

#### Topic Table

- **Active Open Topic**: `1`

| Topic ID | Status | Card Label | Key Facts | Entities | Pages |
|:---:|:---:|:---|:---|:---|:---:|
| 1 | 🟢 OPEN | `Let's plan a trip to Goa with beaches an` | - | - | `[0]` |

#### Memory Layers (L1 / L2)

- **L1 Utilization**: `36/1200` tokens (**3%**) | Low-water: `70%` | High-water: `85%`
- **L1 Pages**: `[0]`
- **L2 Pages**: *(empty)*

<details><summary><b>View L1 Page Details</b></summary>

- **Page 0** [Topic 1, 36 tokens (OPEN)]:
  - `USER`: Let's plan a trip to Goa with beaches and hotels
  - `ASSISTANT`: Great choice! Goa has Anjuna, Baga, and Calangute beaches. For hotels I ...
</details>

#### Rendered Prompt (Sent to LLM)

> **[USER]**: Let's plan a trip to Goa with beaches and hotels

### Turn 2: "How do I make butter chicken recipe with spices?"

> 🤖 **Assistant Reply**: *Marinate chicken in yogurt and spices. Make tomato gravy with butter, cream, and kasuri methi.*

**System Events**:
- `closed topic 1, card: goa / trip / anjuna`
- `new topic 2`

#### Topic Table

- **Active Open Topic**: `2`

| Topic ID | Status | Card Label | Key Facts | Entities | Pages |
|:---:|:---:|:---|:---|:---|:---:|
| 1 | 🔴 CLOSED | `goa / trip / anjuna` | Let's plan a trip to Goa with beaches and hotels | goa, trip, anjuna, taj, recommend | `[0]` |
| 2 | 🟢 OPEN | `How do I make butter chicken recipe with` | - | - | `[1]` |

#### Memory Layers (L1 / L2)

- **L1 Utilization**: `71/1200` tokens (**6%**) | Low-water: `70%` | High-water: `85%`
- **L1 Pages**: `[0, 1]`
- **L2 Pages**: *(empty)*

<details><summary><b>View L1 Page Details</b></summary>

- **Page 0** [Topic 1, 36 tokens]:
  - `USER`: Let's plan a trip to Goa with beaches and hotels
  - `ASSISTANT`: Great choice! Goa has Anjuna, Baga, and Calangute beaches. For hotels I ...
- **Page 1** [Topic 2, 35 tokens (OPEN)]:
  - `USER`: How do I make butter chicken recipe with spices?
  - `ASSISTANT`: Marinate chicken in yogurt and spices. Make tomato gravy with butter, cr...
</details>

#### Rendered Prompt (Sent to LLM)

> **[USER]**: Let's plan a trip to Goa with beaches and hotels
> **[ASSISTANT]**: Great choice! Goa has Anjuna, Baga, and Calangute beaches. For hotels I recommend Taj Fort Aguada.
> **[USER]**: How do I make butter chicken recipe with spices?

### Turn 3: "Which hotel in Goa has the best beach view?"

> 🤖 **Assistant Reply**: *Taj Fort Aguada has a stunning beach view from every room.*

**System Events**:
- `closed topic 2, card: make / gravy / cream`
- `return to topic 1 (goa / trip / anjuna)`

#### Topic Table

- **Active Open Topic**: `1`

| Topic ID | Status | Card Label | Key Facts | Entities | Pages |
|:---:|:---:|:---|:---|:---|:---:|
| 1 | 🟢 OPEN | `goa / trip / anjuna` | Let's plan a trip to Goa with beaches and hotels | goa, trip, anjuna, taj, recommend | `[0, 2]` |
| 2 | 🔴 CLOSED | `make / gravy / cream` | How do I make butter chicken recipe with spices? | make, gravy, cream, spice, chicken | `[1]` |

#### Memory Layers (L1 / L2)

- **L1 Utilization**: `95/1200` tokens (**8%**) | Low-water: `70%` | High-water: `85%`
- **L1 Pages**: `[0, 1, 2]`
- **L2 Pages**: *(empty)*

<details><summary><b>View L1 Page Details</b></summary>

- **Page 0** [Topic 1, 36 tokens]:
  - `USER`: Let's plan a trip to Goa with beaches and hotels
  - `ASSISTANT`: Great choice! Goa has Anjuna, Baga, and Calangute beaches. For hotels I ...
- **Page 1** [Topic 2, 35 tokens]:
  - `USER`: How do I make butter chicken recipe with spices?
  - `ASSISTANT`: Marinate chicken in yogurt and spices. Make tomato gravy with butter, cr...
- **Page 2** [Topic 1, 24 tokens (OPEN)]:
  - `USER`: Which hotel in Goa has the best beach view?
  - `ASSISTANT`: Taj Fort Aguada has a stunning beach view from every room.
</details>

#### Rendered Prompt (Sent to LLM)

> **[USER]**: Let's plan a trip to Goa with beaches and hotels
> **[ASSISTANT]**: Great choice! Goa has Anjuna, Baga, and Calangute beaches. For hotels I recommend Taj Fort Aguada.
> **[USER]**: How do I make butter chicken recipe with spices?
> **[ASSISTANT]**: Marinate chicken in yogurt and spices. Make tomato gravy with butter, cream, and kasuri methi.
> **[USER]**: Which hotel in Goa has the best beach view?

#### Assertions & Verification Notes
> [!NOTE]
> **✅ PASS: Return to old topic reopens it with new page**

---
