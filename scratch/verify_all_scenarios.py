import sys, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from prism import (
    ContextManager, L1, L2, PageTable, TopicTable,
    KeywordSegmenter, KeywordRouter, FakeCardWriter
)

def make_manager(max_tokens: int = 500, max_page_tokens: int = 400, protect_recent_pages: int = 2) -> ContextManager:
    return ContextManager(
        l1=L1(max_tokens=max_tokens, high_water=0.85, low_water=0.70),
        l2=L2(),
        topics=TopicTable(),
        page_table=PageTable(),
        segmenter=KeywordSegmenter(),
        router=KeywordRouter(),
        card_writer=FakeCardWriter(),
        max_page_tokens=max_page_tokens,
        protect_recent_pages=protect_recent_pages,
    )

print("--- Testing S4 ---")
mgr4 = make_manager(max_tokens=95, max_page_tokens=200, protect_recent_pages=1)
mgr4.prepare_context("Python is a great programming language for data science and machine learning applications")
mgr4.record_reply("Absolutely! Python has libraries like NumPy, Pandas, Scikit-learn, TensorFlow, and PyTorch that make it the go-to language for data science workflows and ML model training.")
mgr4.prepare_context("Tell me about JavaScript React framework and hooks for building web applications")
mgr4.record_reply("React uses components and hooks like useState and useEffect. JSX lets you write HTML-like syntax in JavaScript. Virtual DOM makes it fast for web app rendering.")
assert len(mgr4.l2.pages()) > 0, f"S4 failed: L2 pages = {len(mgr4.l2.pages())}"
print("S4 PASS! L2 pages:", [p.seq for p in mgr4.l2.pages()])

print("--- Testing S5 ---")
mgr5 = make_manager(max_tokens=120, max_page_tokens=200, protect_recent_pages=1)
u1_5 = "Explain Goa beaches Anjuna nightlife Baga water sports Calangute resorts Palolem sunset views Arambol drum circles"
r1_5 = "Anjuna is famous for its Wednesday flea market and psychedelic trance parties near the shore. Baga beach offers parasailing, jet skiing, and banana boats. Calangute has luxury five-star resorts. Palolem has the most beautiful sunset views in all of Goa."
mgr5.prepare_context(u1_5)
mgr5.record_reply(r1_5)

u2_5 = "How does quantum computing work with qubits and superposition entanglement?"
r2_5 = "Quantum computers use qubits that can exist in superposition. Entanglement links qubits."
mgr5.prepare_context(u2_5)
mgr5.record_reply(r2_5)

l2_before_t3 = [s for s in mgr5.topics.get(1).page_seqs if mgr5.page_table.where(s) == "L2"]
print("S5 before T3, Topic 1 in L2:", l2_before_t3)
assert len(l2_before_t3) > 0, f"S5 failed: Topic 1 was not demoted to L2 before T3!"

u3_5 = "Which Goa beach has the best Anjuna nightlife?"
r3_5 = "Anjuna Beach is Goa's nightlife hub."
rendered5 = mgr5.prepare_context(u3_5)
mgr5.record_reply(r3_5)

topic1_in_l1 = [s for s in mgr5.topics.get(1).page_seqs if mgr5.page_table.where(s) == "L1"]
print("S5 after T3, Topic 1 in L1:", topic1_in_l1)
assert len(topic1_in_l1) > 0, f"S5 failed: Topic 1 was not retrieved to L1!"
# Also verify that page 0 specifically was retrieved
assert 0 in topic1_in_l1, f"S5 failed: Page 0 not retrieved to L1! in L1: {topic1_in_l1}"
print("S5 PASS!")

print("--- Testing S6 ---")
mgr6 = make_manager(max_tokens=2000, max_page_tokens=40)
mgr6.prepare_context("Explain the Python GIL and how it affects threading performance")
mgr6.record_reply("The Global Interpreter Lock is a mutex that protects Python objects from concurrent access. It means only one thread executes Python bytecode at a time, limiting true parallelism.")
pages_before6 = len(mgr6.topics.get(1).page_seqs)

mgr6.prepare_context("How can I work around the GIL using multiprocessing?")
mgr6.record_reply("Use the multiprocessing module which spawns separate processes, each with its own GIL. ProcessPoolExecutor makes it easy. For I/O-bound tasks, asyncio is another option.")
pages_after6 = len(mgr6.topics.get(1).page_seqs)
print(f"S6 pages before: {pages_before6}, after: {pages_after6}")
assert pages_after6 > pages_before6, f"S6 failed: Page was not split! {pages_before6} -> {pages_after6}"
print("S6 PASS!")

print("--- Testing S7 ---")
mgr7 = make_manager(max_tokens=100, max_page_tokens=200, protect_recent_pages=1)
mgr7.prepare_context("Explain PostgreSQL indexes and query optimization with EXPLAIN ANALYZE")
mgr7.record_reply("Use B-tree indexes on frequently queried columns. EXPLAIN ANALYZE shows the query plan.")

mgr7.prepare_context("How does Redis caching work with TTL expiration and eviction policies?")
mgr7.record_reply("Redis stores key-value pairs in memory. Set TTL with EXPIRE. LRU eviction when maxmemory is hit.")

mgr7.prepare_context("Explain Docker containers and Kubernetes orchestration for microservices")
mgr7.record_reply("Docker packages apps in containers. Kubernetes manages scaling, networking, and deployment.")

open_seq7 = mgr7._open_seq
assert open_seq7 is not None
assert mgr7.page_table.where(open_seq7) == "L1"
assert len(mgr7.l2.pages()) > 0, f"S7 failed: No pages in L2!"
print("S7 PASS! L2 pages:", [p.seq for p in mgr7.l2.pages()], "Open page in L1:", open_seq7)

print("--- Testing S9 ---")
mgr9 = make_manager(max_tokens=80, max_page_tokens=200, protect_recent_pages=1)
mgr9.prepare_context("Tell me about Goa beaches and resorts")
mgr9.record_reply("Goa has Palolem and Agonda beaches with great resorts.")

mgr9.prepare_context("Explain quantum physics wave duality experiments double slit setup and observations")
mgr9.record_reply("In the double slit experiment particles show wave-like interference patterns when not observed.")

rendered9 = mgr9.prepare_context("Which Goa beach resort has the best sunset view?")
mgr9.record_reply("Palolem beach resort has spectacular sunset views.")

l1_seqs9 = mgr9.l1.seqs()
print("S9 L1 seqs:", l1_seqs9, "L2 seqs:", [p.seq for p in mgr9.l2.pages()])
gaps9 = [m for m in rendered9 if m.content == "[earlier messages omitted]"]
print("S9 gap markers count:", len(gaps9))
assert len(gaps9) > 0, f"S9 failed: Gap markers missing in rendered context! L1 seqs: {l1_seqs9}"
print("S9 PASS!")

print("--- Testing S10 ---")
# Victim Selection: least needed first
mgr10 = make_manager(max_tokens=60, max_page_tokens=200, protect_recent_pages=1)
mgr10.prepare_context("Goa beaches Anjuna Baga Calangute Palolem resorts")
mgr10.record_reply("Goa is wonderful for beaches.")

mgr10.prepare_context("Python Django Flask web framework REST API development")
mgr10.record_reply("Django has ORM and admin. Flask is lightweight.")

mgr10.prepare_context("Kubernetes Docker container orchestration microservices deployment")
mgr10.record_reply("K8s manages containers at scale.")

l2_pages10 = mgr10.l2.pages()
print("S10 L2 pages:", [(p.seq, f"topic {p.topic_id}") for p in l2_pages10])
print("S10 L1 pages:", [(p.seq, f"topic {p.topic_id}") for p in mgr10.l1.pages()])
assert len(l2_pages10) > 0, "S10 failed: L2 is empty!"
# First evicted should be page 0 (Topic 1)
assert l2_pages10[0].seq == 0, f"S10 failed: Expected page 0 to be evicted first, got {l2_pages10[0].seq}"
print("S10 PASS!")
