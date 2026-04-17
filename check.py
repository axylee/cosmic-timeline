import json
from collections import Counter

with open('data/events.json', encoding='utf-8') as f:
    d = json.load(f)

axes    = {a['id']: a for a in d.get('axes', [])}
events  = d['events']
views   = d.get('views', [])

has_img  = sum(1 for e in events if e.get('image'))
no_img   = sum(1 for e in events if not e.get('image'))
has_cr   = sum(1 for e in events if e.get('crossRef'))
has_en   = sum(1 for e in events if e.get('en'))
has_desc_en = sum(1 for e in events if e.get('desc_en'))
has_cat  = sum(1 for e in events if e.get('category'))
has_wiki_zh = sum(1 for e in events if e.get('wiki_zh'))
has_wiki_en = sum(1 for e in events if e.get('wiki_en'))

# 軸線錯誤
bad_axis = [e['zh'] for e in events if e.get('axis') and e['axis'] not in axes]

# 事件年份早於軸線 startYear
early = []
for e in events:
    ax = axes.get(e.get('axis'))
    if ax and e.get('year') is not None and e['year'] < ax['startYear']:
        early.append(f"  {e['zh']} (year:{e['year']}, axisStart:{ax['startYear']})")

# 重複 id
id_counts = Counter(e['id'] for e in events if e.get('id'))
dupes = [id for id, n in id_counts.items() if n > 1]

# 新欄位檢查
axis_groups = d.get('axis_groups', {})
view_groups = d.get('view_groups', [])
era_bands   = d.get('era_bands', [])
era_buttons = d.get('era_buttons', [])
filter_cats = d.get('filter_cats', [])

# 軸線 label_en 檢查
ax_no_label_en = [a['id'] for a in d.get('axes', []) if not a.get('label_en')]

# 軸線 group 引用不存在的 axis_groups
ax_bad_group = [a['id'] for a in d.get('axes', []) if a.get('group') and a['group'] not in axis_groups]

# view 引用不存在的軸線
view_bad_axes = []
for v in views:
    bad = [a for a in v.get('axes', []) if a not in axes]
    if bad:
        view_bad_axes.append(f"  {v.get('id','?')}: {bad}")

# ═══════════════════════════════════════════
# view_groups 檢查
# ═══════════════════════════════════════════
vg_ids = {g['id'] for g in view_groups}

# view 使用舊 category 欄位（應改為 group）
view_old_category = [v.get('id','?') for v in views if 'category' in v]

# view 缺 group
view_no_group = [v.get('id','?') for v in views if not v.get('group')]

# view 的 group 不在 view_groups 定義中
view_bad_group = [f"  {v.get('id','?')}: '{v.get('group')}'" for v in views
                  if v.get('group') and v.get('group') not in vg_ids]

# view_groups 統計每個 group 下的 view 數量（用於「空 group 不顯示」規則）
vg_usage = Counter(v.get('group') for v in views if v.get('group'))
vg_empty = [g['id'] for g in view_groups if g['id'] not in vg_usage]

print("=" * 50)
print(f"  事件總數     : {len(events)}")
print(f"  有圖片       : {has_img}")
print(f"  缺圖片       : {no_img}")
print(f"  有 en 名稱   : {has_en}  (缺 {len(events)-has_en})")
print(f"  有 desc_en   : {has_desc_en}  (缺 {len(events)-has_desc_en})")
print(f"  有 category  : {has_cat}  (缺 {len(events)-has_cat})")
print(f"  有 wiki_zh   : {has_wiki_zh}  (缺 {len(events)-has_wiki_zh})")
print(f"  有 wiki_en   : {has_wiki_en}  (缺 {len(events)-has_wiki_en})")
print(f"  有 crossRef  : {has_cr}")
print(f"  定義軸線數   : {len(axes)}")
print(f"  axis_groups  : {len(axis_groups)} 組")
print(f"  view_groups  : {len(view_groups)} 組")
print(f"  era_bands    : {len(era_bands)} 段")
print(f"  era_buttons  : {len(era_buttons)} 個")
print(f"  filter_cats  : {len(filter_cats)} 類")
print(f"  views        : {len(views)} 個")
print("=" * 50)

# 結構性錯誤
errors = 0

if bad_axis:
    print(f"\n⚠ 事件引用不存在的軸線 ({len(bad_axis)} 個):")
    for x in bad_axis: print(f"  {x}")
    errors += 1
else:
    print("\n✓ 所有事件軸線正確")

if early:
    print(f"\n⚠ 事件年份早於軸線起點 ({len(early)} 個):")
    for x in early: print(x)
    errors += 1
else:
    print("✓ 所有事件年份正確")

if dupes:
    print(f"\n⚠ 重複 ID ({len(dupes)} 個): {dupes}")
    errors += 1
else:
    print("✓ 無重複 ID")

if ax_bad_group:
    print(f"\n⚠ 軸線 group 引用不存在的 axis_groups ({len(ax_bad_group)} 個): {ax_bad_group}")
    errors += 1
else:
    print("✓ 所有軸線 group 正確")

if view_bad_axes:
    print(f"\n⚠ View 引用不存在的軸線:")
    for x in view_bad_axes: print(x)
    errors += 1
else:
    print("✓ 所有 View 軸線正確")

# view_groups 檢查
if view_old_category:
    print(f"\n⚠ View 仍使用舊 category 欄位（應改為 group）: {view_old_category}")
    errors += 1
else:
    print("✓ 無 views 使用舊 category 欄位")

if view_no_group:
    print(f"\n⚠ View 缺 group 欄位: {view_no_group}")
    errors += 1
else:
    print("✓ 所有 views 有 group 欄位")

if view_bad_group:
    print(f"\n⚠ View 的 group 引用不存在的 view_groups:")
    for x in view_bad_group: print(x)
    errors += 1
else:
    print("✓ 所有 views 的 group 正確")

if not axis_groups:
    print("\n⚠ 缺少 axis_groups")
    errors += 1

if not view_groups:
    print("\n⚠ 缺少 view_groups")
    errors += 1

if not era_bands:
    print("\n⚠ 缺少 era_bands")
    errors += 1

if not era_buttons:
    print("\n⚠ 缺少 era_buttons")
    errors += 1

if not filter_cats:
    print("\n⚠ 缺少 filter_cats")
    errors += 1

# 內容缺失摘要
print("\n─── 內容缺失摘要 ───")
if ax_no_label_en:
    print(f"  軸線缺 label_en: {len(ax_no_label_en)} 條 → {ax_no_label_en[:5]}{'...' if len(ax_no_label_en)>5 else ''}")

missing_img = [e['zh'] for e in events if not e.get('image')]
if missing_img:
    print(f"  缺圖事件: {len(missing_img)} 個")
    for x in missing_img: print(f"    {x}")

missing_en = [e['zh'] for e in events if not e.get('en')]
if missing_en:
    print(f"  缺 en 名稱: {len(missing_en)} 個")

missing_cat = [e['zh'] for e in events if not e.get('category')]
if missing_cat:
    print(f"  缺 category: {len(missing_cat)} 個")

# view_groups 使用狀況
print("\n─── view_groups 使用狀況 ───")
for g in view_groups:
    count = vg_usage.get(g['id'], 0)
    status = f"{count} 個 view" if count > 0 else "（空，不顯示）"
    print(f"  {g['id']:18s} {g['label']:8s} {status}")

if errors == 0 and not missing_img and not missing_en:
    print("\n  ✓ 全部完整！")

print(f"\n完成！{'⚠ 有 ' + str(errors) + ' 個結構性錯誤' if errors else '✓ 無結構性錯誤'}")
