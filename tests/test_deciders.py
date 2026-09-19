"""Tests for deciders: Jev mock tests and offline fakes."""
import unittest

from prism.deciders import (
    FakeCardWriter,
    JevClient,
    JevRouter,
    JevSegmenter,
    KeywordRouter,
    KeywordSegmenter,
)
from prism.models import Message, PageBlock, Topic, TopicCard


class MockJevClient(JevClient):
    """Mock JevClient returning predefined answers."""
    def __init__(self, responses: dict):
        super().__init__()
        self.responses = responses
        self.last_asked = None

    def ask(self, state: str, questions: list[dict]) -> dict:
        self.last_asked = (state, questions)
        return self.responses


class TestDeciders(unittest.TestCase):
    def test_jev_segmenter_low_confidence_gives_continue(self):
        client = MockJevClient({
            "segment": {"choice": "new", "confidence": 0.45, "probabilities": {"new": 0.45}}
        })
        segmenter = JevSegmenter(client, min_confidence=0.6)
        open_topic = Topic(id=1, card=TopicCard(label="Active Topic"))

        decision = segmenter.decide(open_topic, [], [], Message("user", "Something random"))
        self.assertEqual(decision.action, "continue")
        self.assertEqual(decision.confidence, 0.45)

    def test_jev_segmenter_return_below_threshold_gives_new(self):
        client = MockJevClient({
            "segment": {
                "choice": "return:2",
                "confidence": 0.75,
                "probabilities": {"return:2": 0.75, "new": 0.25},
            }
        })
        segmenter = JevSegmenter(client, min_confidence=0.6, return_threshold=0.8)
        open_topic = Topic(id=1, card=TopicCard(label="Active Topic"))
        closed_topic = Topic(id=2, card=TopicCard(label="Old Topic"))

        decision = segmenter.decide(open_topic, [closed_topic], [], Message("user", "Old stuff"))
        self.assertEqual(decision.action, "new")

    def test_jev_segmenter_return_above_threshold_succeeds(self):
        client = MockJevClient({
            "segment": {
                "choice": "return:2",
                "confidence": 0.90,
                "probabilities": {"return:2": 0.90, "new": 0.10},
            }
        })
        segmenter = JevSegmenter(client, min_confidence=0.6, return_threshold=0.8)
        open_topic = Topic(id=1, card=TopicCard(label="Active Topic"))
        closed_topic = Topic(id=2, card=TopicCard(label="Old Topic"))

        decision = segmenter.decide(open_topic, [closed_topic], [], Message("user", "Old stuff"))
        self.assertEqual(decision.action, "return")
        self.assertEqual(decision.topic_id, 2)

    def test_jev_router_scores_closed_topics(self):
        client = MockJevClient({
            "topic_1": {"noul": 0.85},
            "topic_2": {"noul": 0.15},
        })
        router = JevRouter(client)
        topics = [
            Topic(id=1, card=TopicCard(label="Topic 1")),
            Topic(id=2, card=TopicCard(label="Topic 2")),
        ]
        scores = router.score(topics, [], Message("user", "Need topic 1 info"))
        self.assertEqual(scores, {1: 0.85, 2: 0.15})

    def test_fake_card_writer(self):
        writer = FakeCardWriter()
        pages = [
            PageBlock(
                seq=0,
                topic_id=1,
                data=[
                    Message("user", "Apples and mangoes are delicious fruits."),
                    Message("assistant", "I agree!"),
                ],
            )
        ]
        card = writer.write(None, pages)
        self.assertIsNotNone(card)
        self.assertEqual(card.covered_through, 0)
        self.assertTrue(len(card.entities) > 0)

    def test_keyword_segmenter_and_router(self):
        segmenter = KeywordSegmenter()
        router = KeywordRouter()

        t1 = Topic(id=1, card=TopicCard(label="fruit apples oranges"))
        decision = segmenter.decide(t1, [], [], Message("user", "more apples please"))
        self.assertEqual(decision.action, "continue")

        scores = router.score([t1], [], Message("user", "I want oranges"))
        self.assertTrue(scores[1] > 0.0)


if __name__ == "__main__":
    unittest.main()
