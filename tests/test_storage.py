"""Tests for storage layer: L1, L2, LocationBook, and TopicTable."""
import unittest

from prism.models import Message, PageBlock
from prism.storage import L1, L1FullError, L2, LocationBook, PageTable, TopicTable


class TestStorage(unittest.TestCase):
    def test_l1_put_and_overflow(self):
        l1 = L1(max_tokens=50, high_water=0.85, low_water=0.70)
        page1 = PageBlock(seq=0, topic_id=1, data=[Message("user", "Hello world")])
        l1.put(page1)
        self.assertTrue(l1.has(0))
        self.assertEqual(l1.used_tokens, page1.tokens)

        # Duplicate seq raises ValueError
        with self.assertRaises(ValueError):
            l1.put(page1)

        # Overflow raises L1FullError
        big_page = PageBlock(seq=1, topic_id=1, data=[Message("user", "x" * 250)])
        with self.assertRaises(L1FullError):
            l1.put(big_page)

    def test_l1_take_refuses_open_page(self):
        l1 = L1(max_tokens=100)
        open_page = PageBlock(seq=0, topic_id=1, is_open=True)
        l1.put(open_page)

        with self.assertRaises(ValueError):
            l1.take(0)

        open_page.is_open = False
        taken = l1.take(0)
        self.assertEqual(taken.seq, 0)
        self.assertFalse(l1.has(0))

    def test_l1_render_sorted_with_gaps(self):
        l1 = L1(max_tokens=200)
        # Put non-consecutive pages: seq 0 and seq 2
        p0 = PageBlock(seq=0, topic_id=1, data=[Message("user", "First message")])
        p2 = PageBlock(seq=2, topic_id=1, data=[Message("user", "Third message")])
        l1.put(p2)
        l1.put(p0)  # Insert out of order

        rendered = l1.render(mark_gaps=True)
        self.assertEqual(len(rendered), 3)
        self.assertEqual(rendered[0].content, "First message")
        self.assertEqual(rendered[1].role, "system")
        self.assertEqual(rendered[1].content, "[earlier messages omitted]")
        self.assertEqual(rendered[2].content, "Third message")

    def test_l1_render_initial_gap(self):
        l1 = L1(max_tokens=200)
        # First page in L1 is not seq 0
        p1 = PageBlock(seq=1, topic_id=1, data=[Message("user", "Second message")])
        l1.put(p1)

        rendered = l1.render(mark_gaps=True)
        self.assertEqual(len(rendered), 2)
        self.assertEqual(rendered[0].role, "system")
        self.assertEqual(rendered[0].content, "[earlier messages omitted]")
        self.assertEqual(rendered[1].content, "Second message")

    def test_l1_watermark_hysteresis(self):
        # 100 max tokens: low_water=70, high_water=85
        l1 = L1(max_tokens=100, high_water=0.85, low_water=0.70)
        # Add page with 80 tokens (320 chars) -> 80% utilization
        p0 = PageBlock(seq=0, topic_id=1, data=[Message("user", "a" * 320)])
        l1.put(p0)
        self.assertEqual(l1.utilization(), 0.80)
        self.assertFalse(l1.over_high_water())
        self.assertTrue(l1.above_low_water())

        # Add 10 more tokens (40 chars) -> 90% utilization
        l1.append_message(0, Message("user", "b" * 40))
        self.assertEqual(l1.utilization(), 0.90)
        self.assertTrue(l1.over_high_water())

    def test_l2_basic_operations(self):
        l2 = L2()
        p = PageBlock(seq=5, topic_id=2)
        l2.put(p)
        self.assertTrue(l2.has(5))
        self.assertEqual(len(l2), 1)
        self.assertEqual(l2.get(5).seq, 5)
        self.assertEqual(l2.pages()[0].seq, 5)
        taken = l2.take(5)
        self.assertEqual(taken.seq, 5)
        self.assertEqual(len(l2), 0)

    def test_page_table(self):
        pt = PageTable()
        pt.set(0, "L1")
        pt.set(1, "L2")
        pt.set(2, "L1")

        self.assertEqual(pt.where(0), "L1")
        self.assertEqual(pt.where(1), "L2")
        self.assertEqual(pt.pages_in("L1"), [0, 2])
        self.assertEqual(pt.pages_in("L2"), [1])

        # Test LocationBook alias compatibility
        self.assertIs(LocationBook, PageTable)

    def test_topic_table_one_open_topic_invariant(self):
        tt = TopicTable()
        t1 = tt.new_topic("Topic 1")
        self.assertEqual(t1.id, 1)
        self.assertEqual(tt.open_topic.id, 1)

        # Cannot open another topic while one is already open
        with self.assertRaises(RuntimeError):
            tt.new_topic("Topic 2")

        tt.close(1)
        self.assertIsNone(tt.open_topic)
        self.assertEqual(len(tt.closed_topics()), 1)

        # Reopening
        tt.reopen(1)
        self.assertEqual(tt.open_topic.id, 1)

        with self.assertRaises(RuntimeError):
            tt.new_topic("Topic 2")


if __name__ == "__main__":
    unittest.main()
