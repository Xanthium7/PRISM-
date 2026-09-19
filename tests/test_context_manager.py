"""Tests for ContextManager and all turn-by-turn invariants."""
import unittest

from prism.context_manager import ContextManager
from prism.deciders import FakeCardWriter, KeywordRouter, KeywordSegmenter
from prism.models import Message
from prism.storage import L1, L2, PageTable, TopicTable


class TestContextManager(unittest.TestCase):
    def assert_invariants(self, manager: ContextManager):
        """Assert the 5 core invariants from Section 11 of the specification."""
        all_seqs = set(range(manager._next_seq))

        # 1. Every page seq is in exactly one of L1 or L2, and page_table.where(seq) matches
        for seq in all_seqs:
            in_l1 = manager.l1.has(seq)
            in_l2 = manager.l2.has(seq)
            self.assertNotEqual(
                in_l1, in_l2,
                f"Page {seq} must be in exactly one of L1 or L2 (in_l1={in_l1}, in_l2={in_l2})"
            )
            expected_layer = "L1" if in_l1 else "L2"
            self.assertEqual(
                manager.page_table.where(seq), expected_layer,
                f"Page table mismatch for page {seq}: says {manager.page_table.where(seq)}, actual {expected_layer}"
            )

        # 2. The open page is always in L1
        if manager._open_seq is not None:
            self.assertTrue(manager.l1.has(manager._open_seq), f"Open page {manager._open_seq} must be in L1")
            self.assertTrue(manager.l1.get(manager._open_seq).is_open, f"Open page {manager._open_seq} must be open")

        # 3. l1.render() is sorted by seq; used_tokens equals the sum of page tokens
        pages = manager.l1.pages()
        seqs = [p.seq for p in pages]
        self.assertEqual(seqs, sorted(seqs), f"L1 pages must be sorted by seq: {seqs}")
        self.assertEqual(manager.l1.used_tokens, sum(p.tokens for p in pages))

        # 5. Each topic's page_seqs is increasing and every page's topic_id matches its topic
        for topic in manager.topics.all():
            self.assertEqual(topic.page_seqs, sorted(topic.page_seqs), f"Topic {topic.id} page_seqs not sorted")
            for seq in topic.page_seqs:
                page = manager._page(seq)
                self.assertEqual(page.topic_id, topic.id, f"Page {seq} topic_id {page.topic_id} != {topic.id}")

    def test_first_message_and_continuation(self):
        manager = ContextManager(
            l1=L1(max_tokens=200),
            l2=L2(),
            topics=TopicTable(),
            page_table=PageTable(),
            segmenter=KeywordSegmenter(),
            router=KeywordRouter(),
            card_writer=FakeCardWriter(),
        )

        # 1. First message creates topic 1
        msgs = manager.prepare_context("I love red apples and mangoes")
        self.assert_invariants(manager)
        self.assertEqual(manager.topics.open_topic.id, 1)
        self.assertEqual(len(msgs), 1)

        manager.record_reply("Apples and mangoes are delicious fruits.")
        self.assert_invariants(manager)

        # 2. Short continuation like "ok" continues the topic
        msgs2 = manager.prepare_context("ok sounds great")
        self.assert_invariants(manager)
        self.assertEqual(manager.topics.open_topic.id, 1)

    def test_topic_switch_and_card_writing(self):
        manager = ContextManager(
            l1=L1(max_tokens=300),
            l2=L2(),
            topics=TopicTable(),
            page_table=PageTable(),
            segmenter=KeywordSegmenter(),
            router=KeywordRouter(),
            card_writer=FakeCardWriter(),
        )

        manager.prepare_context("We are talking about Python programming")
        manager.record_reply("Python is an interpreted language.")
        self.assertEqual(manager.topics.open_topic.id, 1)

        # Switch to something completely different
        manager.prepare_context("Plan a vacation to Switzerland and skiing")
        self.assert_invariants(manager)
        self.assertEqual(manager.topics.open_topic.id, 2)

        # Topic 1 should now be closed and have a card
        t1 = manager.topics.get(1)
        self.assertFalse(t1.is_open)
        self.assertEqual(t1.card.covered_through, 0)
        self.assertTrue(len(t1.card.entities) > 0)

    def test_return_to_old_topic(self):
        manager = ContextManager(
            l1=L1(max_tokens=400),
            l2=L2(),
            topics=TopicTable(),
            page_table=PageTable(),
            segmenter=KeywordSegmenter(),
            router=KeywordRouter(),
            card_writer=FakeCardWriter(),
        )

        # Topic 1: Fruits
        manager.prepare_context("I like mango, orange and red apples")
        manager.record_reply("Noted, you like mango, orange and red apples.")
        # Topic 2: Debug auth (2 turns so recent window of 4 messages belongs to topic 2)
        manager.prepare_context("Help me debug the login bug in auth.py, the token expires too early")
        manager.record_reply("Let us look at auth.py token expiry.")
        manager.prepare_context("The token refresh code is also in auth.py")
        manager.record_reply("Then the refresh token logic in auth.py may be resetting the expiry.")

        self.assertEqual(manager.topics.open_topic.id, 2)

        # Return to Topic 1 (high overlap with mango, orange, apples)
        manager.prepare_context("Which mango dishes can I make with apples and orange")
        self.assert_invariants(manager)
        self.assertEqual(manager.topics.open_topic.id, 1)
        # Topic 1 should now have pages [0, 2]
        t1 = manager.topics.get(1)
        self.assertEqual(t1.page_seqs, [0, 2])

    def test_demotion_under_pressure_and_recovery(self):
        # max_tokens=60, high_water=0.85 (51 tok), low_water=0.70 (42 tok)
        manager = ContextManager(
            l1=L1(max_tokens=60, high_water=0.85, low_water=0.70),
            l2=L2(),
            topics=TopicTable(),
            page_table=PageTable(),
            segmenter=KeywordSegmenter(),
            router=KeywordRouter(),
            card_writer=FakeCardWriter(),
            needed_threshold=0.3,
            protect_recent_pages=1,
        )

        # Turn 1: Topic 1 (~18 tokens)
        manager.prepare_context("alpha beta gamma delta epsilon zeta eta theta")
        manager.record_reply("reply for topic 1 with extra detailed tokens")
        self.assert_invariants(manager)

        # Turn 2: Topic 2 (~20 tokens)
        manager.prepare_context("winter snow skiing mountains snowboarding cold")
        manager.record_reply("reply for topic 2 with extra detailed tokens")
        self.assert_invariants(manager)

        # Turn 3: Topic 3 (~20 tokens) - pushes over 51 tokens (85%)
        manager.prepare_context("cooking pasta garlic olive tomato sauce basil oregano")
        manager.record_reply("reply for topic 3 with extra detailed tokens")
        self.assert_invariants(manager)

        # Some pages should now have moved to L2
        pages_in_l2 = manager.page_table.pages_in("L2")
        self.assertTrue(len(pages_in_l2) > 0, "Expected at least one page to be demoted to L2")

        # Turn 4: Ask about winter snow skiing again (Topic 2) -> router pulls Topic 2 from L2 back to L1
        manager.prepare_context("Tell me more about winter skiing and snowboarding in snow")
        self.assert_invariants(manager)
        # Check that pages for topic 2 are back in L1
        t2_pages = manager.topics.get(2).page_seqs
        for seq in t2_pages:
            self.assertEqual(manager.page_table.where(seq), "L1")


if __name__ == "__main__":
    unittest.main()
