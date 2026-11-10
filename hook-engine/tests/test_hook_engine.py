import unittest

from hook_engine import generate_hooks, score_hook
from hook_engine.__main__ import main


class ScorerTests(unittest.TestCase):
    def test_strong_hook_passes(self):
        s = score_hook(
            "YouTube automation lost me 40% of my views. But it wasn't the algorithm.",
            topic="youtube automation",
        )
        self.assertEqual(s.context, 3)
        self.assertGreaterEqual(s.lean, 2)
        self.assertEqual(s.snapback, 3)
        self.assertTrue(s.passes())

    def test_weak_hook_fails(self):
        s = score_hook(
            "Hey guys welcome back to the channel, today we are going to be talking about some stuff.",
            topic="youtube automation",
        )
        self.assertEqual(s.context, 0)
        self.assertFalse(s.passes())
        self.assertTrue(s.feedback)

    def test_late_context_penalised(self):
        early = score_hook("Email marketing is dead. But not why you think.", topic="email marketing")
        late = score_hook("Here is something I learned recently about email marketing.", topic="email marketing")
        self.assertGreater(early.context, late.context)

    def test_snapback_before_lean_scores_lower(self):
        s = score_hook("But here we go. I tested this for 30 days.")
        self.assertEqual(s.snapback, 2)

    def test_long_hook_loses_tightness(self):
        s = score_hook(" ".join(["word"] * 60))
        self.assertEqual(s.tightness, 0)

    def test_empty(self):
        self.assertEqual(score_hook("   ").total, 0)

    def test_word_boundaries(self):
        # "button" must not match "but"
        s = score_hook("Press the button now")
        self.assertEqual(s.snapback, 0)


class GeneratorTests(unittest.TestCase):
    def test_generate_ranked_and_passing(self):
        hooks = generate_hooks("youtube shorts", pain="low views", stat="90 days")
        self.assertEqual(len(hooks), 5)
        totals = [h.total for h in hooks]
        self.assertEqual(totals, sorted(totals, reverse=True))
        self.assertTrue(hooks[0].passes())

    def test_lean_filter(self):
        hooks = generate_hooks("ai voiceovers", lean="proof", top=10)
        self.assertEqual(len(hooks), 3)

    def test_bad_lean(self):
        with self.assertRaises(ValueError):
            generate_hooks("x", lean="nope")


class CliTests(unittest.TestCase):
    def test_gate_exit_codes(self):
        self.assertEqual(main(["gate", "YouTube automation lost me 40% of my views. But it wasn't the algorithm.",
                               "--topic", "youtube automation"]), 0)
        self.assertEqual(main(["gate", "hello everyone and welcome", "--topic", "youtube automation"]), 1)


if __name__ == "__main__":
    unittest.main()
