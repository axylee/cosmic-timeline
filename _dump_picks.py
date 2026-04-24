import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from collections import defaultdict

with open('tools/pending-picks-202604241445.json', encoding='utf-8') as f:
    d = json.load(f)

by_axis = defaultdict(list)
for it in d['items']:
    by_axis[it['axis']].append(it)

axis_arg = sys.argv[1] if len(sys.argv) > 1 else None
if axis_arg:
    axes = [axis_arg]
else:
    axes = list(by_axis.keys())

for ax in axes:
    if ax not in by_axis: continue
    print(f'\n=== AXIS: {ax} ({len(by_axis[ax])} items) ===')
    for it in by_axis[ax]:
        print(f"\n[{it['id']}] {it['zh']} | {it['en']} ({it['year']})")
        if it.get('category'):
            print(f"  cat: {it['category']}")
        if not it['candidates']:
            print('  ** ZERO candidates **')
            print(f"  wiki_en: {it.get('wiki_en','')}")
            print(f"  wiki_zh: {it.get('wiki_zh','')}")
        for i, c in enumerate(it['candidates'][:6]):
            print(f"  [{i}] {c['source']:22s} | {c['label'][:55]}")
            print(f"      {c['url'][:110]}")
