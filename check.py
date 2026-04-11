import json

with open('data/events.json', encoding='utf-8') as f:
    d = json.load(f)

axes    = {a['id']: a for a in d.get('axes', [])}
events  = d['events']

has_img  = sum(1 for e in events if e.get('image'))
no_img   = sum(1 for e in events if not e.get('image'))
has_cr   = sum(1 for e in events if e.get('crossRef'))
arts     = sum(1 for e in events if e.get('axis') == 'arts')

# 軸線錯誤
bad_axis = [e['zh'] for e in events if e.get('axis') and e['axis'] not in axes]

# 事件年份早於軸線 startYear
early = []
for e in events:
    ax = axes.get(e.get('axis'))
    if ax and e.get('year') is not None and e['year'] < ax['startYear']:
        early.append(f"  {e['zh']} (year:{e['year']}, axisStart:{ax['startYear']})")

# 重複 id
from collections import Counter
id_counts = Counter(e['id'] for e in events if e.get('id'))
dupes = [id for id, n in id_counts.items() if n > 1]

print("=" * 45)
print(f"  事件總數   : {len(events)}")
print(f"  有圖片     : {has_img}")
print(f"  缺圖片     : {no_img}")
print(f"  有 crossRef: {has_cr}")
print(f"  arts 軸事件: {arts}")
print(f"  定義軸線數 : {len(axes)}")
print("=" * 45)

if bad_axis:
    print(f"\n⚠ 軸線不存在 ({len(bad_axis)} 個):")
    for x in bad_axis: print(f"  {x}")
else:
    print("\n✓ 所有事件軸線正確")

if early:
    print(f"\n⚠ 事件年份早於軸線起點 ({len(early)} 個):")
    for x in early: print(x)
else:
    print("✓ 所有事件年份正確")

if dupes:
    print(f"\n⚠ 重複 ID ({len(dupes)} 個): {dupes}")
else:
    print("✓ 無重複 ID")

missing = [e['zh'] for e in events if not e.get('image')]
if missing:
    print(f"\n缺圖事件 ({len(missing)} 個):")
    for x in missing: print(f"  {x}")

print("\n完成！")
