# Hook Engine

Scores and generates short-form video hooks using the **Context → Lean → Snapback** structure.
It's pure Python (3.9+), has no dependencies and needs no API key.

| Part | Points | Checks |
|---|---|---|
| Context | 0–3 | Is the topic stated in the first half of the first sentence? |
| Lean | 0–3 | Does the hook use shock, a pain point or proof (a stat)? Using two of them earns full points. |
| Snapback | 0–3 | Does a twist ("but", "actually", "here's why"...) come *after* the lean? |
| Tightness | 0–1 | Is it 40 words or fewer (about 3 seconds)? |

## Use

Run these from the `hook-engine/` folder:

```bash
# Score a hook
python3 -m hook_engine score "YouTube automation lost me 40% of my views. But it wasn't the algorithm." --topic "youtube automation"

# Generate ranked drafts
python3 -m hook_engine generate --topic "faceless youtube channels" \
  --pain "videos stuck at 200 views" --stat "100 uploads" --belief "posting every day"

# Gate before upload: exits with code 1 if the score is below 7, so a pipeline can block the upload
python3 -m hook_engine gate "$HOOK_TEXT" --topic "$TOPIC" --threshold 7
```

Add `--json` to `score` or `generate` to get machine-readable output.

In Python:

```python
from hook_engine import score_hook, generate_hooks
if not score_hook(hook, topic=topic).passes(7):
    raise SystemExit("Hook too weak, skipping upload")
```

## Tests

```bash
python3 -m unittest discover -s tests -t .
```

## Limits

The scorer uses keyword heuristics, not an AI judge. It checks that the hook has the right
structure. It can't tell whether the hook is actually interesting. Use it as a floor,
not a replacement for taste.
