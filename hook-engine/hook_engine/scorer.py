"""Score a short-form video hook against the Context / Lean / Snapback framework.

Score breakdown (total 10):
  Context   0-3  Is the topic clear in the first half of the first sentence?
  Lean      0-3  Does it use shock, a pain point, or proof to pull the viewer in?
  Snapback  0-3  Does it then flip direction (contrast / reveal)?
  Tightness 0-1  Is the whole hook short enough to say in a few seconds?
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

SHOCK_WORDS = [
    "insane", "crazy", "shocking", "nobody", "no one", "secret", "never",
    "banned", "illegal", "unbelievable", "wild", "terrifying", "impossible",
    "everyone", "biggest", "worst", "best", "only",
]
PAIN_WORDS = [
    "struggling", "struggle", "tired of", "wasting", "waste", "losing", "lose",
    "stuck", "failing", "fail", "mistake", "problem", "hate", "can't", "cannot",
    "frustrated", "broke", "burned out", "why your", "why you're", "stop",
]
PROOF_PATTERNS = [
    r"\d", r"\bpercent\b", r"\bmillion\b", r"\bbillion\b", r"\bthousand\b",
    r"\bstudy\b", r"\bresearch\b", r"\bdata\b", r"\bi tested\b", r"\bafter\b",
    r"\bproven\b", r"\bresults?\b",
]
SNAPBACK_MARKERS = [
    "but", "however", "actually", "instead", "turns out", "the truth",
    "wrong", "myth", "isn't", "is not", "aren't", "not because", "here's why",
    "the real reason", "opposite", "except", "until", "yet", "the problem is",
    "what nobody", "what no one", "doesn't", "don't",
]

MAX_WORDS = 40


@dataclass
class HookScore:
    text: str
    context: int = 0
    lean: int = 0
    snapback: int = 0
    tightness: int = 0
    lean_types: list[str] = field(default_factory=list)
    feedback: list[str] = field(default_factory=list)

    @property
    def total(self) -> int:
        return self.context + self.lean + self.snapback + self.tightness

    def passes(self, threshold: int = 7) -> bool:
        return self.total >= threshold

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "total": self.total,
            "context": self.context,
            "lean": self.lean,
            "lean_types": self.lean_types,
            "snapback": self.snapback,
            "tightness": self.tightness,
            "feedback": self.feedback,
        }


def _words(text: str) -> list[str]:
    return re.findall(r"[a-z0-9'%$]+", text.lower())


def _first_sentence(text: str) -> str:
    parts = re.split(r"(?<=[.!?])\s+", text.strip(), maxsplit=1)
    return parts[0]


def _find(phrase: str, text: str) -> int:
    """Position of a whole-word/phrase match in lowercased text, or -1."""
    m = re.search(r"(?<![a-z])" + re.escape(phrase) + r"(?![a-z])", text)
    return m.start() if m else -1


def _score_context(text: str, topic: str | None, fb: list[str]) -> int:
    first = _first_sentence(text)
    first_words = _words(first)
    if topic:
        topic_words = [w for w in _words(topic) if len(w) > 2]
        if not topic_words:
            topic_words = _words(topic)
        half = first_words[: max(1, (len(first_words) + 1) // 2)]
        if any(w in half for w in topic_words):
            return 3
        if any(w in first_words for w in topic_words):
            fb.append("Context: move the topic into the first half of the first sentence.")
            return 2
        if any(w in _words(text) for w in topic_words):
            fb.append("Context: the topic only shows up after the first sentence. Put it up front.")
            return 1
        fb.append("Context: the topic is never stated. Say what the video is about immediately.")
        return 0
    # No topic given: judge by how quickly the first sentence lands.
    n = len(first_words)
    if n <= 12:
        return 3 if n >= 4 else 2
    if n <= 20:
        fb.append("Context: the first sentence is long. Get to the topic faster.")
        return 2
    fb.append("Context: the first sentence is too long. The topic gets buried.")
    return 1


def _score_lean(lower: str, fb: list[str]) -> tuple[int, list[str], int]:
    types: list[str] = []
    positions: list[int] = []
    for label, words in (("shock", SHOCK_WORDS), ("pain_point", PAIN_WORDS)):
        hits = [p for p in (_find(w, lower) for w in words) if p >= 0]
        if hits:
            types.append(label)
            positions.append(min(hits))
    proof_hits = [m.start() for p in PROOF_PATTERNS if (m := re.search(p, lower))]
    if proof_hits:
        types.append("proof")
        positions.append(min(proof_hits))

    if not types:
        fb.append("Lean: add a shock, a pain point, or proof (a number/stat) so the viewer leans in.")
        return 0, types, -1
    score = 2 if len(types) == 1 else 3
    if score == 2:
        fb.append("Lean: good. Stacking a second lever (e.g. a stat on top of a pain point) makes it stronger.")
    return score, types, min(positions)


def _score_snapback(lower: str, lean_pos: int, fb: list[str]) -> int:
    hits = [p for p in (_find(m, lower) for m in SNAPBACK_MARKERS) if p >= 0]
    if not hits:
        fb.append("Snapback: no direction change. Add a twist ('but', 'actually', 'here's why'...).")
        return 0
    if lean_pos >= 0 and max(hits) > lean_pos:
        return 3
    fb.append("Snapback: the twist should come after the lean, not before it.")
    return 2


def score_hook(text: str, topic: str | None = None) -> HookScore:
    """Score a hook. `topic` is optional keywords for what the video is about."""
    text = text.strip()
    result = HookScore(text=text)
    if not text:
        result.feedback.append("Empty hook.")
        return result

    lower = text.lower()
    result.context = _score_context(text, topic, result.feedback)
    result.lean, result.lean_types, lean_pos = _score_lean(lower, result.feedback)
    result.snapback = _score_snapback(lower, lean_pos, result.feedback)

    n_words = len(_words(text))
    if n_words <= MAX_WORDS:
        result.tightness = 1
    else:
        result.feedback.append(
            f"Tightness: {n_words} words. Keep the hook under {MAX_WORDS} words (about 3 seconds)."
        )
    return result
