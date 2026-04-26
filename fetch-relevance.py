#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Score event-to-view relevance via Claude Haiku 4.5.

For each topic-style view (where canvas axes are intentionally broad to give
historical context), ask Claude which events are directly relevant to the
view's topic — not just present in the same era. Tag matched events with
`relevant_views: [view_id, ...]`. The generator uses this to filter agg pages.

Run with API key in env, never hardcoded:
  ANTHROPIC_API_KEY="..." python fetch-relevance.py
"""
import json, os, sys, time
from pathlib import Path

try:
    import anthropic
except ImportError:
    print("ERROR: pip install anthropic", file=sys.stderr); sys.exit(1)

PATH = Path(__file__).parent / 'data' / 'events.json'
MODEL = 'claude-haiku-4-5'
BATCH = 60   # events per LLM call

# Topic views needing semantic relevance filter (canvas axes are too broad)
TOPIC_VIEWS = [
    # Topics group
    'pandemics', 'art-history', 'music-history', 'medical',
    'thm-science', 'thm-trade', 'thm-religion', 'space-exploration',
    'exploration', 'revolutions', 'disasters',
    # Nature-cosmos group with broad earth/climate/life axes
    'nat-earth', 'thm-climate', 'thm-migration',
    'dinosaurs', 'cenozoic', 'nat-human',
    # Note: nat-iceages uses manual core_event_ids (5 大冰河期), not LLM
    # Countries — cross axis brings in unrelated events
    'china', 'egypt', 'france', 'germany', 'greece', 'india', 'iran',
    'italy', 'japan', 'korea', 'russia', 'taiwan', 'turkey', 'uk', 'usa',
    'reg-africa', 'reg-americas', 'reg-centralas', 'reg-eastasia',
    'reg-europe', 'reg-mideast', 'reg-oceania', 'reg-polar',
    'reg-sea', 'reg-southasia',
    # Wars — same drift problem
    'american-civil', 'american-revolution', 'cold-war', 'crusades',
    'korean-war', 'mongol-conquests', 'napoleonic', 'peloponnesian',
    'punic-wars', 'seven-years', 'thirty-years', 'vietnam-war',
    'ww1', 'ww2',
    # Empires
    'akkadian', 'alexander-empire', 'ancient-egypt-empire',
    'arab-caliphate', 'british-empire', 'byzantine', 'japanese-empire',
    'mongol-empire', 'mughal-empire', 'ottoman-empire', 'persian-empire',
    'qing-dynasty', 'roman-empire', 'russian-empire', 'spanish-empire',
    'tang-dynasty',
    # Civilization
    'civ-africa', 'civ-all', 'civ-americas', 'civ-east', 'civ-west',
]

SYSTEM_PROMPT = """你是歷史內容編輯助手，協助一個叫 Cosmic History Timeline 的網站把事件分類到主題頁。

任務：給你一個「主題」(例如「藝術史」「瘟疫史」) 和一組候選歷史事件，回傳哪些事件**直接屬於該主題**。

判斷原則：
1. 直接屬於該主題的範疇 ✓ 例如：藝術史頁應該收 達文西、畢卡索、文藝復興；不收 牛頓、絲路、瘟疫
2. 「同時代」「相關脈絡」 ✗ 不要選。例如：絲路開通對藝術史是脈絡，不是直接相關
3. 標準：如果一個受過教育的讀者打開這個主題的時間軸頁，會期待看到這個事件嗎？
4. 寧可保守（少選）也不要過寬

回傳 JSON：{"relevant_event_ids": ["id1", "id2", ...]}"""


def event_axes(e):
    if 'axes' in e and isinstance(e['axes'], list):
        return e['axes']
    if 'axis' in e:
        return [e['axis']]
    return []


def candidates_for_view(events, view):
    """Events touching any of view.axes within the view's year range."""
    axset = set(view.get('axes') or [])
    ys = view.get('yearStart', -1e18)
    ye = view.get('yearEnd', 1e18)
    out = []
    for e in events:
        y = e.get('year')
        if y is None: continue
        if not (ys <= y <= ye): continue
        if any(a in axset for a in event_axes(e)):
            out.append(e)
    return out


def chunk(seq, size):
    for i in range(0, len(seq), size):
        yield seq[i:i + size]


def score_view(client, view, events):
    """Send candidate events to Claude in batches; collect IDs of relevant ones."""
    label_zh = view.get('label', view['id'])
    label_en = view.get('label_en', view['id'])
    topic = f"{label_zh}（{label_en}）"

    relevant = set()
    total_in_tokens = total_out_tokens = total_cache_read = 0

    for bi, batch_events in enumerate(chunk(events, BATCH), start=1):
        listing = "\n".join(
            f"- id={e['id']} | year={e.get('year','?')} | zh={(e.get('zh','') or '')[:60]} | desc={(e.get('desc_zh','') or '')[:120]}"
            for e in batch_events
        )
        user_msg = f"""主題：{topic}

候選事件 ({len(batch_events)} 條):
{listing}

請回傳此主題**直接相關**的事件 ID。"""

        try:
            resp = client.messages.create(
                model=MODEL,
                max_tokens=4000,
                system=[
                    {"type": "text", "text": SYSTEM_PROMPT,
                     "cache_control": {"type": "ephemeral"}},
                ],
                messages=[{"role": "user", "content": user_msg}],
                output_config={
                    "format": {
                        "type": "json_schema",
                        "schema": {
                            "type": "object",
                            "properties": {
                                "relevant_event_ids": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                },
                            },
                            "required": ["relevant_event_ids"],
                            "additionalProperties": False,
                        },
                    },
                },
            )
        except Exception as e:
            print(f"  ! batch {bi}: API error: {type(e).__name__}: {e}", flush=True)
            continue

        # Extract JSON from text content
        text = next((b.text for b in resp.content if b.type == "text"), "")
        try:
            data = json.loads(text)
            ids = data.get("relevant_event_ids", []) or []
            relevant.update(ids)
        except json.JSONDecodeError:
            print(f"  ! batch {bi}: parse error: {text[:120]}", flush=True)
            continue

        usage = resp.usage
        total_in_tokens += usage.input_tokens
        total_out_tokens += usage.output_tokens
        total_cache_read += getattr(usage, 'cache_read_input_tokens', 0) or 0

        cache_pct = (total_cache_read / max(1, total_in_tokens + total_cache_read)) * 100
        print(f"  batch {bi}: relevant={len(ids):>3}/{len(batch_events)}  "
              f"(usage in={usage.input_tokens} cache={getattr(usage,'cache_read_input_tokens',0)} out={usage.output_tokens})",
              flush=True)

    return relevant, total_in_tokens, total_out_tokens, total_cache_read


def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY env var not set", file=sys.stderr)
        sys.exit(1)

    # Optional: pass one or more view IDs to limit this run; default = all TOPIC_VIEWS
    extras = sys.argv[1:]
    targets = extras if extras else TOPIC_VIEWS

    client = anthropic.Anthropic(api_key=api_key)

    with open(PATH, encoding='utf-8') as f:
        d = json.load(f)

    # Reset relevant_views entries managed by this script (preserve others)
    for e in d['events']:
        rv = e.get('relevant_views')
        if isinstance(rv, list):
            e['relevant_views'] = [v for v in rv if v not in TOPIC_VIEWS]

    grand_in = grand_out = grand_cache = 0
    for vid in targets:
        view = next((v for v in d['views'] if v['id'] == vid), None)
        if not view:
            print(f"!! view '{vid}' not found"); continue

        cand = candidates_for_view(d['events'], view)
        print(f"\n=== {vid} | {view.get('label','')} | candidates={len(cand)} ===", flush=True)

        rel_ids, n_in, n_out, n_cache = score_view(client, view, cand)
        grand_in += n_in; grand_out += n_out; grand_cache += n_cache

        # Tag events
        for e in d['events']:
            if e.get('id') in rel_ids:
                rv = e.setdefault('relevant_views', [])
                if vid not in rv:
                    rv.append(vid)

        # Checkpoint save after every view (recover from crash)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(d, f, ensure_ascii=False, indent=2)
        print(f"  saved: {len(rel_ids)} events tagged with relevant_views={vid}")

    # Cost estimate (Haiku 4.5 pricing)
    cost = (grand_in * 1.0 + grand_out * 5.0 + grand_cache * 0.10) / 1_000_000
    print(f"\nDONE. tokens in={grand_in} cache={grand_cache} out={grand_out}  ~${cost:.4f}")


if __name__ == '__main__':
    main()
