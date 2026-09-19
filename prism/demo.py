"""Run a scripted conversation and watch pages move between layers.

Can be run as:
    python demo.py
    python -m prism.demo
    python prism/demo.py
"""
import sys
from pathlib import Path

# Prevent Python from creating __pycache__ folders
sys.dont_write_bytecode = True

# Ensure root directory is in sys.path for direct execution
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

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

SCRIPT = [
    ("I like mango, orange and red apples",
     "Noted, you like mango, orange and red apples."),
    ("I dont like vegetables and I am allergic to nuts",
     "Got it: no vegetables, and a nuts allergy."),
    ("Help me debug the login bug in auth.py, the token expires too early",
     "Let's look at how auth.py sets the token expiry."),
    ("The token refresh code is also in auth.py",
     "Then the refresh token logic in auth.py may be resetting the expiry."),
    ("Plan a trip to the Kerala backwaters in December",
     "December is a great time for the Kerala backwaters."),
    ("Which mango dishes should I avoid with my nuts allergy",
     "Avoid mango desserts made with cashews or almonds because of the nuts allergy."),
]


def main() -> None:
    manager = ContextManager(
        l1=L1(max_tokens=120, high_water=0.85, low_water=0.70),
        l2=L2(),
        topics=TopicTable(),
        page_table=PageTable(),
        segmenter=KeywordSegmenter(),
        router=KeywordRouter(),
        card_writer=FakeCardWriter(),
        needed_threshold=0.4,
        protect_recent_pages=1,
    )

    for turn, (user, reply) in enumerate(SCRIPT, 1):
        messages = manager.prepare_context(user)
        # >>> here your app would call the model with `messages` and get a reply <<<
        print(f"\n=== Turn {turn}: {user}")
        for event in manager.drain_events():
            print(f"  - {event}")
        manager.record_reply(reply)
        print(manager.snapshot())

    print("\n=== Topic cards")
    for t in manager.topics.all():
        print(f"  topic {t.id}: pages {t.page_seqs} | {t.card.label}")

    print("\n=== What the model would see on the last turn (before the reply)")
    for m in messages:
        print(f"  {m.role}: {m.content}")


if __name__ == "__main__":
    main()
