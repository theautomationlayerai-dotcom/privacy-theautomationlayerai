"""Generate hook drafts from templates using the Context / Lean / Snapback structure.

No API key needed: drafts are filled from templates, then ranked by the scorer.
"""

from __future__ import annotations

from .scorer import HookScore, score_hook

# Each template = context + lean + snapback.
# Placeholders: {topic}, {audience}, {pain}, {stat}, {belief}
TEMPLATES = {
    "shock": [
        "{topic} is about to change for {audience}. Nobody is talking about it, but here's why it matters.",
        "This {topic} trick feels illegal to know. But it's not what you think.",
        "The biggest {topic} mistake I see? It's actually the thing everyone recommends.",
    ],
    "pain_point": [
        "If you're struggling with {pain}, your {topic} isn't the problem. Here's the real reason.",
        "Tired of {pain}? Most {topic} advice makes it worse, but one change fixes it.",
        "Stop wasting time on {topic}. The problem is {belief}, and here's why.",
    ],
    "proof": [
        "I tested {topic} for {stat}. The results weren't what I expected.",
        "{stat} with {topic}, but it wasn't because of {belief}.",
        "After {stat} of {topic}, I learned everyone's wrong about {belief}.",
    ],
}

DEFAULTS = {
    "audience": "creators",
    "pain": "low views",
    "stat": "30 days",
    "belief": "posting more",
}


def generate_hooks(
    topic: str,
    audience: str | None = None,
    pain: str | None = None,
    stat: str | None = None,
    belief: str | None = None,
    lean: str | None = None,
    top: int = 5,
) -> list[HookScore]:
    """Return the top-scoring hook drafts for a topic, best first.

    `lean` restricts to one lean type: 'shock', 'pain_point' or 'proof'.
    """
    if lean and lean not in TEMPLATES:
        raise ValueError(f"lean must be one of {sorted(TEMPLATES)}")
    values = {
        "topic": topic.strip(),
        "audience": audience or DEFAULTS["audience"],
        "pain": pain or DEFAULTS["pain"],
        "stat": stat or DEFAULTS["stat"],
        "belief": belief or DEFAULTS["belief"],
    }
    groups = [lean] if lean else list(TEMPLATES)
    drafts = []
    for group in groups:
        for tpl in TEMPLATES[group]:
            text = tpl.format(**values)
            text = text[0].upper() + text[1:]
            drafts.append(score_hook(text, topic=topic))
    drafts.sort(key=lambda s: s.total, reverse=True)
    return drafts[:top]
