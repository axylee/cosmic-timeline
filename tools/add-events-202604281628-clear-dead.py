"""
═══════════════════════════════════════════════════════
  add-events-202604281628-clear-dead.py

  清空死連結事件的 image 欄位（由 images-check-dead.py --fix 產生）

  包含 13 個事件
  執行後這些事件的 image="" ，使用者可以到 cosmic-tools.html
  篩「缺圖事件」手動補圖，或跑 images-find-missing.py 自動補

  執行：
    python add-events-202604281628-clear-dead.py
    python check.py
═══════════════════════════════════════════════════════
"""
import json

with open('data/events.json', encoding='utf-8') as f:
    d = json.load(f)

ev_by_id = {e['id']: e for e in d['events']}

# ═══ 要清空 image 的事件清單 ═══
EVENT_IDS_TO_CLEAR = [
    # 武則天稱帝  (HTTP 404)  ← 原:%E5%94%90%E6%9C%9D%E5%90%8D%E8%87%A3%E6%9C%83%E7%B
    'emperor-wu-zetian',
    # 《三國演義》  (HTTP 404)  ← 原:%E4%B8%89%E5%9C%8B%E6%BC%94%E7%BE%A9%E6%98%8E%E5%9
    'lit-sanguoyanyi',
    # 台灣光復  (HTTP 404)  ← 原:1280px-After_Surrender_Ceremony_of_Japan_in_Taiwan
    'tw-1945-retro',
    # 第三次政黨輪替  (HTTP 404)  ← 原:%E8%94%A1%E8%8B%B1%E6%96%87%E5%85%83%E9%A6%96%E8%8
    'tw-party-rotate3',
    # 縱貫鐵路全線通車  (HTTP 404)  ← 原:1280px-12_Cars_EMU500_through_Fengshan_River_Bridg
    'tw-col-rail',
    # 台灣文化協會成立  (HTTP 404)  ← 原:1280px-thumbnail.jpg
    'tw-col-bunka',
    # 南島語族擴散起點  (HTTP 404)  ← 原:1280px-Map_of_the_prehistoric_Austronesian_migrati
    'tw-cul-austronesian',
    # 原住民正名運動  (HTTP 404)  ← 原:1280px-thumbnail.jpg
    'tw-cul-indigenous-name',
    # 侯孝賢《悲情城市》  (HTTP 404)  ← 原:1280px-thumbnail.jpg
    'tw-cul-houhsiao',
    # 王莽篡漢・新朝  (HTTP 404)  ← 原:%E6%9D%B1%E8%A5%BF%E6%BC%A2%E5%85%A8%E5%82%B3_01_%
    'emperor-wang-mang',
    # 孫子《兵法》  (HTTP 404)  ← 原:1280px-Inscribed_bamboo-slips_of_Art_of_War.jpg
    'lit-sunzi',
    # 縱貫鐵路全線通車  (HTTP 404)  ← 原:1280px-12_Cars_EMU500_through_Fengshan_River_Bridg
    'tw-col-rail-emp',
    # 台灣文化協會成立  (HTTP 404)  ← 原:1280px-thumbnail.jpg
    'tw-col-bunka-emp',
]

cleared = 0
missing = 0

for eid in EVENT_IDS_TO_CLEAR:
    ev = ev_by_id.get(eid)
    if not ev:
        print(f"⚠ 找不到事件: {eid}")
        missing += 1
        continue
    ev["image"] = ""
    print(f"⊘ 清空 {ev['zh']:25s} (待手動補圖)")
    cleared += 1

# 儲存（保持 key 順序）
ordered = {}
key_order = ['meta', 'axis_groups', 'axes', 'era_bands', 'era_buttons',
             'filter_cats', 'views', 'view_groups', 'events']
for k in key_order:
    if k in d:
        ordered[k] = d[k]
for k in d:
    if k not in ordered:
        ordered[k] = d[k]

with open('data/events.json', 'w', encoding='utf-8') as f:
    json.dump(ordered, f, ensure_ascii=False, indent=2)

print()
print("=" * 55)
print(f"  清空: {cleared} 個事件")
if missing:
    print(f"  找不到事件: {missing}")
print("=" * 55)
print("清空完成！現在可以：")
print("  1. 打開 cosmic-tools.html 篩「缺圖事件」手動補")
print("  2. 或跑 python tools/images-find-missing.py 自動補")
