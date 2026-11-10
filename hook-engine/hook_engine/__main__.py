"""Command line: python -m hook_engine {score,generate,gate} ..."""

from __future__ import annotations

import argparse
import json
import sys

from .generator import generate_hooks
from .scorer import HookScore, score_hook


def _print(score: HookScore, as_json: bool) -> None:
    if as_json:
        print(json.dumps(score.to_dict(), indent=2))
        return
    print(f"[{score.total}/10] {score.text}")
    print(
        f"  context {score.context}/3 | lean {score.lean}/3 "
        f"({', '.join(score.lean_types) or 'none'}) | snapback {score.snapback}/3 "
        f"| tightness {score.tightness}/1"
    )
    for tip in score.feedback:
        print(f"  - {tip}")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="hook_engine", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("score", help="Score a hook")
    s.add_argument("text")
    s.add_argument("--topic")
    s.add_argument("--json", action="store_true")

    g = sub.add_parser("generate", help="Generate ranked hook drafts")
    g.add_argument("--topic", required=True)
    g.add_argument("--audience")
    g.add_argument("--pain")
    g.add_argument("--stat")
    g.add_argument("--belief", help="The common belief the snapback overturns")
    g.add_argument("--lean", choices=["shock", "pain_point", "proof"])
    g.add_argument("--top", type=int, default=5)
    g.add_argument("--json", action="store_true")

    gt = sub.add_parser("gate", help="Exit 1 if the hook scores below the threshold (use before upload)")
    gt.add_argument("text")
    gt.add_argument("--topic")
    gt.add_argument("--threshold", type=int, default=7)

    a = p.parse_args(argv)

    if a.cmd == "score":
        _print(score_hook(a.text, a.topic), a.json)
        return 0
    if a.cmd == "generate":
        hooks = generate_hooks(a.topic, a.audience, a.pain, a.stat, a.belief, a.lean, a.top)
        if a.json:
            print(json.dumps([h.to_dict() for h in hooks], indent=2))
        else:
            for h in hooks:
                _print(h, False)
                print()
        return 0
    # gate
    result = score_hook(a.text, a.topic)
    _print(result, False)
    ok = result.passes(a.threshold)
    print("PASS" if ok else f"FAIL: below {a.threshold}/10, rewrite the hook before uploading")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
