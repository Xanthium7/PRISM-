import sys, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ["PYTHONUTF8"] = "1"
if hasattr(sys.stdout, "reconfigure"):
    try: sys.stdout.reconfigure(encoding="utf-8")
    except: pass

from prism import ContextManager, L1, L2, PageTable, TopicTable, KeywordSegmenter, KeywordRouter, FakeCardWriter

def make(mt, mpt=200):
    return ContextManager(
        l1=L1(max_tokens=mt, high_water=0.85, low_water=0.70),
        l2=L2(), topics=TopicTable(), page_table=PageTable(),
        segmenter=KeywordSegmenter(), router=KeywordRouter(),
        card_writer=FakeCardWriter(), max_page_tokens=mpt)

def l2s(m): return [p.seq for p in m.l2.pages()]

# ── S5 full trace ──
print("=== S5 full trace max_tokens=120 ===")
m = make(120)
u1 = "Explain Goa beaches Anjuna nightlife Baga water sports Calangute resorts Palolem sunset views Arambol drum circles"
r1 = "Anjuna is famous for its Wednesday flea market and psychedelic trance parties near the shore. Baga beach offers parasailing, jet skiing, and banana boats. Calangute has luxury five-star resorts. Palolem has the most beautiful sunset views in all of Goa."

m.prepare_context(u1); m.record_reply(r1)
print(f"T1: events={m.drain_events()}")
print(f"  L1={m.l1.used_tokens}/120, L2={l2s(m)}")

u2 = "How does quantum computing work with qubits and superposition entanglement?"
r2 = "Quantum computers use qubits that can exist in superposition. Entanglement links qubits."
m.prepare_context(u2); m.record_reply(r2)
print(f"T2: events={m.drain_events()}")
print(f"  L1 seqs={m.l1.seqs()}, L2={l2s(m)}, L1={m.l1.used_tokens}/120")
for p in m.l1.pages():
    print(f"    Page {p.seq}: topic={p.topic_id}, tokens={p.tokens}, open={p.is_open}")

# Topic state before Turn 3
print(f"\nBefore T3:")
for t in m.topics.all():
    print(f"  Topic {t.id}: open={t.is_open}, pages={t.page_seqs}, card.label={t.card.label}")
print(f"  open_topic={m.topics.open_topic}")

u3 = "Which Goa beach has the best Anjuna nightlife?"
r3 = "Anjuna Beach is Goa's nightlife hub."
rendered = m.prepare_context(u3)
print(f"\nT3 prep: events={m.drain_events()}")
print(f"  L1 seqs={m.l1.seqs()}, L2={l2s(m)}, L1={m.l1.used_tokens}/120")
for p in m.l1.pages():
    print(f"    Page {p.seq}: topic={p.topic_id}, tokens={p.tokens}, open={p.is_open}")
for t in m.topics.all():
    print(f"  Topic {t.id}: open={t.is_open}, pages={t.page_seqs}")

m.record_reply(r3)
print(f"\nT3 reply: events={m.drain_events()}")
print(f"  L1 seqs={m.l1.seqs()}, L2={l2s(m)}, L1={m.l1.used_tokens}/120")
for t in m.topics.all():
    print(f"  Topic {t.id}: open={t.is_open}, pages={t.page_seqs}")
    for s in t.page_seqs:
        loc = m.page_table.where(s)
        print(f"    Page {s} in {loc}")

# ── S9 full trace ──
print("\n\n=== S9 full trace max_tokens=80 ===")
m9 = make(80)
m9.prepare_context("Tell me about Goa beaches and resorts")
m9.record_reply("Goa has Palolem and Agonda beaches with great resorts.")
print(f"T1: events={m9.drain_events()}, L1={m9.l1.used_tokens}/80")

u2_9 = "Explain quantum physics wave duality experiments double slit setup and observations"
r2_9 = "In the double slit experiment particles show wave-like interference patterns when not observed."
m9.prepare_context(u2_9); m9.record_reply(r2_9)
print(f"T2: events={m9.drain_events()}, L1={m9.l1.used_tokens}/80, L2={l2s(m9)}")

u3_9 = "Which Goa beach resort has the best sunset view?"
rendered9 = m9.prepare_context(u3_9)
print(f"T3 prep: events={m9.drain_events()}")
print(f"  L1 seqs={m9.l1.seqs()}, L2={l2s(m9)}, L1={m9.l1.used_tokens}/80")
for t in m9.topics.all():
    print(f"  Topic {t.id}: open={t.is_open}, pages={t.page_seqs}")
gaps = [msg for msg in rendered9 if msg.content == "[earlier messages omitted]"]
print(f"  Gap markers in rendered: {len(gaps)}")
