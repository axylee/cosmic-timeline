"""
═══════════════════════════════════════════════════════
  Cosmic Timeline — events.json 修改腳本樣板
  
  使用方式：
  1. 複製此檔案，命名為 add-events-YYYYMMDDHHMI.py
  2. 修改下方 NEW_EVENTS / NEW_AXES / UPDATES 等區塊
  3. 在專案根目錄 PowerShell 執行：python add-events-YYYYMMDDHHMI.py
  4. 執行 python check.py 驗證
  5. 用 cosmic-tools.html 補圖片（可之後再補）
  6. GitHub Desktop 上傳
═══════════════════════════════════════════════════════
"""
import json

with open('data/events.json', encoding='utf-8') as f:
    d = json.load(f)

existing_ids = {e['id'] for e in d['events']}
axes_map     = {a['id']: a for a in d['axes']}

added   = 0
skipped = 0
updated = 0

# ════════════════════════════════════════════
# 1. 新增事件（有重複 ID 保護）
# ════════════════════════════════════════════
NEW_EVENTS = [
    # 每個事件一個 dict，欄位說明：
    # id        : 唯一識別碼（英文小寫+連字號），必填
    # year      : 年份（負數=BC），必填
    # zh        : 中文名稱，必填
    # en        : 英文名稱
    # axis      : 所在軸線 id，必填（需在 axes 裡存在）
    # level     : 重要程度 1=大 2=中 3=小，必填
    # endYear   : 結束年份（有=pill，沒有=點）
    # crossRef  : 縱線連接目標軸線，字串或陣列（最多3條）
    # category  : civilization/politics/war/science/religion/culture/
    #             exploration/medicine/astronomy/geology/biology/
    #             philosophy/migration/trade/nature
    # desc_zh   : 中文描述
    # desc_en   : 英文描述
    # wiki_zh   : 中文 Wikipedia URL
    # wiki_en   : 英文 Wikipedia URL
    # image     : 圖片 URL（通常由 cosmic-tools.html 補，不手填）
    #
    # 範例：
    # {
    #     "id": "example-event",
    #     "year": 1969,
    #     "zh": "阿波羅11號登月",
    #     "en": "Apollo 11 Moon Landing",
    #     "axis": "science",
    #     "level": 1,
    #     "category": "science",
    #     "desc_zh": "人類首次踏上月球",
    #     "desc_en": "First humans land on the Moon",
    #     "wiki_zh": "https://zh.wikipedia.org/wiki/阿波罗11号",
    #     "wiki_en": "https://en.wikipedia.org/wiki/Apollo_11",
    #     "crossRef": ["cross", "usa"]
    # },
]

for ev in NEW_EVENTS:
    if ev['id'] in existing_ids:
        print(f"⊘ 跳過（ID 已存在）: {ev['zh']}")
        skipped += 1
        continue
    # 檢查軸線是否存在
    if ev['axis'] not in axes_map:
        print(f"⚠ 軸線不存在: {ev['axis']}（事件: {ev['zh']}）")
        skipped += 1
        continue
    d['events'].append(ev)
    existing_ids.add(ev['id'])
    print(f"✓ 新增: {ev['zh']}")
    added += 1


# ════════════════════════════════════════════
# 2. 新增軸線（有重複 ID 保護）
# ════════════════════════════════════════════
NEW_AXES = [
    # 欄位說明：
    # id        : 唯一識別碼（英文小寫+連字號），必填
    # label     : 中文顯示名稱，必填
    # label_en  : 英文顯示名稱，必填
    # color     : 顏色 hex，必填
    # order     : 排列順序，必填
    # parent    : 父軸 id（null=頂層）
    # startYear : 分支線起始年份，必填
    # endYear   : 消亡年份（null=至今）
    # zoomMin   : 顯示門檻（0=全局，0.30=zoom in 才出現），必填
    # group     : natural/global/region/civilization/religion/human/nation，必填
    #
    # 範例：
    # {
    #     "id": "korea",
    #     "label": "韓國",
    #     "label_en": "Korea",
    #     "color": "#fb923c",
    #     "order": 46,
    #     "parent": "east",
    #     "startYear": -2333,
    #     "endYear": None,
    #     "zoomMin": 0.30,
    #     "group": "civilization"
    # },
]

ax_added = 0
for ax in NEW_AXES:
    if ax['id'] in axes_map:
        print(f"⊘ 跳過軸線（ID 已存在）: {ax['id']}")
        continue
    d['axes'].append(ax)
    axes_map[ax['id']] = ax
    print(f"✓ 新增軸線: {ax['label']} ({ax['id']})")
    ax_added += 1


# ════════════════════════════════════════════
# 3. 修改現有事件（用 id 查找，更新指定欄位）
# ════════════════════════════════════════════
EVENT_UPDATES = {
    # 格式：'event-id': { 'field': new_value, ... }
    # 範例：
    # 'sept-11': { 'crossRef': ['mideast', 'islam'] },
    # 'columbus': { 'desc_en': 'Columbus arrives in the Americas' },
}

ev_by_id = {e['id']: e for e in d['events']}
for eid, fields in EVENT_UPDATES.items():
    ev = ev_by_id.get(eid)
    if not ev:
        print(f"⚠ 找不到事件: {eid}")
        continue
    for k, v in fields.items():
        old = ev.get(k, '—')
        ev[k] = v
        print(f"✓ 更新 {ev['zh']}.{k}: {old} → {v}")
    updated += 1


# ════════════════════════════════════════════
# 4. 修改軸線屬性
# ════════════════════════════════════════════
AXIS_UPDATES = {
    # 格式：'axis-id': { 'field': new_value, ... }
    # 範例：
    # 'science': { 'startYear': -10000 },
}

for aid, fields in AXIS_UPDATES.items():
    ax = axes_map.get(aid)
    if not ax:
        print(f"⚠ 找不到軸線: {aid}")
        continue
    for k, v in fields.items():
        old = ax.get(k, '—')
        ax[k] = v
        print(f"✓ 更新軸線 {aid}.{k}: {old} → {v}")


# ════════════════════════════════════════════
# 5. 儲存（保持 key 順序）
# ════════════════════════════════════════════
ordered = {}
key_order = ['meta', 'axis_groups', 'axes', 'era_bands', 'era_buttons', 'filter_cats', 'views', 'events']
for k in key_order:
    if k in d:
        ordered[k] = d[k]
for k in d:
    if k not in ordered:
        ordered[k] = d[k]

with open('data/events.json', 'w', encoding='utf-8') as f:
    json.dump(ordered, f, ensure_ascii=False, indent=2)

print(f"\n{'='*45}")
print(f"  新增事件: {added} 個（跳過 {skipped}）")
print(f"  新增軸線: {ax_added} 條")
print(f"  更新事件: {updated} 個")
print(f"  總事件數: {len(d['events'])}")
print(f"{'='*45}")
print("完成！請執行 python check.py 驗證")
