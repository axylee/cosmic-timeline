#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Generate Guardian-style punchy lead paragraphs (intro_zh + intro_en) for
each view that doesn't already have one.

Style: 1-2 sentences, paratactic, ending with consequence. Same voice as
the curated ww2 example:
  zh: "從希特勒上台到原子彈落下。13 年，兩個戰場，世界從此不同。"
  en: "From Hitler's rise to the atomic bomb. 13 years, two theatres, a world remade."

Skips views that already have BOTH intro_zh and intro_en set (idempotent).

Run:
  ANTHROPIC_API_KEY="..." python fetch-intros.py             # all eligible
  ANTHROPIC_API_KEY="..." python fetch-intros.py japan greece  # specific
  ANTHROPIC_API_KEY="..." python fetch-intros.py --redo       # overwrite existing
"""
import json, os, sys
from pathlib import Path

try:
    import anthropic
except ImportError:
    print("ERROR: pip install anthropic", file=sys.stderr); sys.exit(1)

PATH = Path(__file__).parent / 'data' / 'events.json'
MODEL = 'claude-haiku-4-5'

SYSTEM_PROMPT = """You are a magazine editor writing two-sentence intro leads for historical timeline pages, in the punchy paratactic style of the Guardian or The Atlantic.

Your output must follow these rules exactly:
1. Output a JSON object: {"intro_zh": "<traditional Chinese>", "intro_en": "<English>"}.
2. Each intro is ONE or TWO short sentences. Maximum about 30 words English / 40 字 Chinese.
3. Style: short, declarative, no hedging, no academic tone. End with a consequence or shift, not a summary.
4. The Chinese version should use Traditional Chinese (繁體) and feel natural — not a translation of the English.
5. NO date ranges in parentheses. NO "this view covers..." NO "explore..." NO "discover..." NO listy structure.

GOOD examples (study the rhythm):
  ww2 (1933-1946):
    zh: "從希特勒上台到原子彈落下。13 年，兩個戰場,世界從此不同。"
    en: "From Hitler's rise to the atomic bomb. 13 years, two theatres, a world remade."

  napoleonic (1799-1815):
    zh: "一個炮兵軍官重畫了歐洲的版圖。直到滑鐵盧,他輸給了所有人。"
    en: "An artillery officer redrew Europe's map. Until Waterloo, when he lost to everyone."

  pandemics:
    zh: "從雅典瘟疫到 COVID。每一次大流行都改寫了世界,也都被遺忘了一次。"
    en: "From the Plague of Athens to COVID. Every pandemic rewrote the world, then was forgotten."

BAD examples (do not write like this):
  - "本 view 涵蓋..." / "This view covers..."
  - "Explore the rich history of..."
  - "From X to Y, this timeline shows..."
  - lists or bullet phrasing
  - generic openings like "Throughout history..." or "Across centuries..."
"""


def event_axes(e):
    if 'axes' in e and isinstance(e['axes'], list): return e['axes']
    if 'axis' in e: return [e['axis']]
    return []


def filter_for_view(events, view):
    """Same logic as generate-pages: prefer LLM-curated relevant_views, fall back to axes."""
    vid = view['id']
    yr_s = view.get('yearStart', -1e18); yr_e = view.get('yearEnd', 1e18)
    llm_tagged = [e for e in events if vid in (e.get('relevant_views') or [])]
    if llm_tagged:
        return [e for e in llm_tagged if e.get('year') is not None and yr_s <= e['year'] <= yr_e]
    axset = set(view.get('core_axes') or view.get('axes') or [])
    return [e for e in events
            if e.get('year') is not None and yr_s <= e['year'] <= yr_e
            and any(a in axset for a in event_axes(e))]


def build_user_prompt(view, events):
    """Compact event listing — top events sorted by level then year."""
    label_zh = view.get('label', view['id'])
    label_en = view.get('label_en', view['id'])
    ys = view.get('yearStart', '')
    ye = view.get('yearEnd', '')

    # Pick up to 12 representative events: prefer level=1, then by year coverage
    sorted_events = sorted(events, key=lambda e: (e.get('level', 9), e.get('year', 0)))
    sample = sorted_events[:12]

    lines = []
    for e in sample:
        y = e.get('year', '?')
        zh = (e.get('zh', '') or '')[:50]
        en = (e.get('en', '') or '')[:60]
        lines.append(f"  {y}: {zh} / {en}")

    return f"""View topic:
  zh: {label_zh}
  en: {label_en}
  year range: {ys} to {ye}
  total events: {len(events)}

Representative events (sorted by importance):
{chr(10).join(lines)}

Write a Guardian-style two-sentence intro lead in BOTH Chinese (zh) and English (en). Output JSON only: {{"intro_zh": "...", "intro_en": "..."}}"""


def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY env var not set"); sys.exit(1)

    args = sys.argv[1:]
    redo = '--redo' in args
    args = [a for a in args if not a.startswith('--')]
    only_ids = set(args) if args else None

    client = anthropic.Anthropic(api_key=api_key)

    with open(PATH, encoding='utf-8') as f:
        d = json.load(f)

    n_done = n_skip = n_fail = 0
    grand_in = grand_out = grand_cache = 0

    for view in d['views']:
        vid = view['id']
        if only_ids and vid not in only_ids: continue

        # Skip if already curated (unless --redo)
        if not redo and view.get('intro_zh') and view.get('intro_en'):
            n_skip += 1; continue

        in_scope = filter_for_view(d['events'], view)
        if len(in_scope) < 5:
            print(f'  - skip {vid:25s} ({len(in_scope)} events < 5)')
            n_skip += 1; continue

        user_prompt = build_user_prompt(view, in_scope)
        try:
            resp = client.messages.create(
                model=MODEL,
                max_tokens=600,
                system=[
                    {"type": "text", "text": SYSTEM_PROMPT,
                     "cache_control": {"type": "ephemeral"}},
                ],
                messages=[{"role": "user", "content": user_prompt}],
                output_config={
                    "format": {
                        "type": "json_schema",
                        "schema": {
                            "type": "object",
                            "properties": {
                                "intro_zh": {"type": "string"},
                                "intro_en": {"type": "string"},
                            },
                            "required": ["intro_zh", "intro_en"],
                            "additionalProperties": False,
                        },
                    },
                },
            )
        except Exception as e:
            print(f'  ! {vid}: API error: {type(e).__name__}: {e}')
            n_fail += 1
            continue

        text = next((b.text for b in resp.content if b.type == "text"), "")
        try:
            data = json.loads(text)
            view['intro_zh'] = data['intro_zh'].strip()
            view['intro_en'] = data['intro_en'].strip()
        except (json.JSONDecodeError, KeyError):
            print(f'  ! {vid}: parse error'); n_fail += 1; continue

        usage = resp.usage
        grand_in += usage.input_tokens
        grand_out += usage.output_tokens
        grand_cache += getattr(usage, 'cache_read_input_tokens', 0) or 0

        n_done += 1
        en_preview = view['intro_en'][:60]
        # Print only ASCII-safe en preview (Windows console can't print zh)
        try:
            print(f'  + {vid:25s} en="{en_preview}..."')
        except UnicodeEncodeError:
            print(f'  + {vid}  (preview-skip)')

        # Checkpoint save every 20
        if n_done % 20 == 0:
            with open(PATH, 'w', encoding='utf-8') as f:
                json.dump(d, f, ensure_ascii=False, indent=2)

    with open(PATH, 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

    cost = (grand_in * 1.0 + grand_out * 5.0 + grand_cache * 0.10) / 1_000_000
    print(f'\nDONE. wrote={n_done}  skipped={n_skip}  failed={n_fail}  ~${cost:.4f}')


if __name__ == '__main__':
    main()
