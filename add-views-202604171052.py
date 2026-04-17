"""
新增完整主題清單 + 更新 view_groups
版本：v202604171052

變更：
1. view_groups 10→8（刪 periods + dynasties，empires 改名「王朝與帝國」）
2. 新增 62 個規劃中的 views（空的不顯示，結構先建好）
   - Group 1 自然與宇宙: +1 (dinosaurs)
   - Group 2 文明縱覽: +1 (ancient-civ)
   - Group 3 國家: +14 (taiwan, japan, korea, india, usa, uk, france, germany, russia, egypt, turkey, iran, italy, greece)
   - Group 4 戰爭: +14
   - Group 5 主題: +4
   - Group 6 重大事件: +4
   - Group 7 王朝與帝國: +16
   - Group 8 人物傳記: +8

執行：python add-views-202604171052.py
"""
import json

with open('data/events.json', encoding='utf-8') as f:
    d = json.load(f)

# ═══════════════════════════════════════════
# 1. 更新 view_groups: 10 → 8
# ═══════════════════════════════════════════
NEW_VIEW_GROUPS = [
    {"id": "nature-cosmos", "label": "自然與宇宙",   "label_en": "Nature & Cosmos",     "order": 1},
    {"id": "civilization",  "label": "文明縱覽",     "label_en": "Civilizations",       "order": 2},
    {"id": "countries",     "label": "國家",         "label_en": "Countries",           "order": 3},
    {"id": "wars",          "label": "戰爭",         "label_en": "Wars",                "order": 4},
    {"id": "topics",        "label": "主題",         "label_en": "Topics",              "order": 5},
    {"id": "events",        "label": "重大事件",     "label_en": "Major Events",        "order": 6},
    {"id": "empires",       "label": "王朝與帝國",   "label_en": "Dynasties & Empires", "order": 7},
    {"id": "biographies",   "label": "人物傳記",     "label_en": "Biographies",         "order": 8},
]

d['view_groups'] = NEW_VIEW_GROUPS

# ═══════════════════════════════════════════
# 2. 新增 62 個規劃中的 views
# ═══════════════════════════════════════════
# 注意：只加 view 定義，不加軸線和事件
# axes 欄位先放空陣列（未來填入時再加）
# 已存在的 view 不重複加

existing_view_ids = {v['id'] for v in d.get('views', [])}

NEW_VIEWS = [
    # ── Group 1: nature-cosmos ──
    {"id": "dinosaurs",         "label": "恐龍",           "label_en": "Dinosaurs",                    "group": "nature-cosmos", "axes": [], "yearStart": -252000000, "yearEnd": -66000000},

    # ── Group 2: civilization ──
    {"id": "ancient-civ",       "label": "古文明",         "label_en": "Ancient Civilizations",        "group": "civilization",  "axes": [], "yearStart": -4000, "yearEnd": 500},

    # ── Group 3: countries（個別國家）──
    {"id": "taiwan",            "label": "台灣歷史",       "label_en": "Taiwan History",               "group": "countries",     "axes": [], "yearStart": -30000, "yearEnd": 2026},
    {"id": "japan",             "label": "日本歷史",       "label_en": "Japanese History",             "group": "countries",     "axes": [], "yearStart": -14000, "yearEnd": 2026},
    {"id": "korea",             "label": "韓國歷史",       "label_en": "Korean History",               "group": "countries",     "axes": [], "yearStart": -2333, "yearEnd": 2026},
    {"id": "india",             "label": "印度歷史",       "label_en": "Indian History",               "group": "countries",     "axes": [], "yearStart": -3300, "yearEnd": 2026},
    {"id": "usa",               "label": "美國歷史",       "label_en": "American History",             "group": "countries",     "axes": [], "yearStart": 1492, "yearEnd": 2026},
    {"id": "uk",                "label": "英國歷史",       "label_en": "British History",              "group": "countries",     "axes": [], "yearStart": -3000, "yearEnd": 2026},
    {"id": "france",            "label": "法國歷史",       "label_en": "French History",               "group": "countries",     "axes": [], "yearStart": -600, "yearEnd": 2026},
    {"id": "germany",           "label": "德國歷史",       "label_en": "German History",               "group": "countries",     "axes": [], "yearStart": -100, "yearEnd": 2026},
    {"id": "russia",            "label": "俄羅斯歷史",     "label_en": "Russian History",              "group": "countries",     "axes": [], "yearStart": 862, "yearEnd": 2026},
    {"id": "egypt",             "label": "埃及歷史",       "label_en": "Egyptian History",             "group": "countries",     "axes": [], "yearStart": -3100, "yearEnd": 2026},
    {"id": "turkey",            "label": "土耳其歷史",     "label_en": "Turkish History",              "group": "countries",     "axes": [], "yearStart": -2000, "yearEnd": 2026},
    {"id": "iran",              "label": "伊朗/波斯歷史",  "label_en": "Iranian/Persian History",      "group": "countries",     "axes": [], "yearStart": -3200, "yearEnd": 2026},
    {"id": "italy",             "label": "義大利歷史",     "label_en": "Italian History",              "group": "countries",     "axes": [], "yearStart": -800, "yearEnd": 2026},
    {"id": "greece",            "label": "希臘歷史",       "label_en": "Greek History",                "group": "countries",     "axes": [], "yearStart": -3000, "yearEnd": 2026},

    # ── Group 4: wars ──
    {"id": "peloponnesian",     "label": "伯羅奔尼撒戰爭", "label_en": "Peloponnesian War",           "group": "wars",          "axes": [], "yearStart": -431, "yearEnd": -404},
    {"id": "punic-wars",        "label": "布匿戰爭",       "label_en": "Punic Wars",                  "group": "wars",          "axes": [], "yearStart": -264, "yearEnd": -146},
    {"id": "crusades",          "label": "十字軍東征",     "label_en": "Crusades",                    "group": "wars",          "axes": [], "yearStart": 1096, "yearEnd": 1291},
    {"id": "mongol-conquests",  "label": "蒙古征服",       "label_en": "Mongol Conquests",            "group": "wars",          "axes": [], "yearStart": 1206, "yearEnd": 1368},
    {"id": "thirty-years",      "label": "三十年戰爭",     "label_en": "Thirty Years' War",           "group": "wars",          "axes": [], "yearStart": 1618, "yearEnd": 1648},
    {"id": "seven-years",       "label": "七年戰爭",       "label_en": "Seven Years' War",            "group": "wars",          "axes": [], "yearStart": 1756, "yearEnd": 1763},
    {"id": "american-revolution","label": "美國獨立戰爭",  "label_en": "American Revolution",         "group": "wars",          "axes": [], "yearStart": 1775, "yearEnd": 1783},
    {"id": "napoleonic",        "label": "拿破崙戰爭",     "label_en": "Napoleonic Wars",             "group": "wars",          "axes": [], "yearStart": 1803, "yearEnd": 1815},
    {"id": "american-civil",    "label": "美國南北戰爭",   "label_en": "American Civil War",          "group": "wars",          "axes": [], "yearStart": 1861, "yearEnd": 1865},
    {"id": "ww1",               "label": "第一次世界大戰", "label_en": "World War I",                 "group": "wars",          "axes": [], "yearStart": 1914, "yearEnd": 1918},
    {"id": "ww2",               "label": "第二次世界大戰", "label_en": "World War II",                "group": "wars",          "axes": [], "yearStart": 1939, "yearEnd": 1945},
    {"id": "cold-war",          "label": "冷戰",           "label_en": "Cold War",                    "group": "wars",          "axes": [], "yearStart": 1947, "yearEnd": 1991},
    {"id": "korean-war",        "label": "韓戰",           "label_en": "Korean War",                  "group": "wars",          "axes": [], "yearStart": 1950, "yearEnd": 1953},
    {"id": "vietnam-war",       "label": "越戰",           "label_en": "Vietnam War",                 "group": "wars",          "axes": [], "yearStart": 1955, "yearEnd": 1975},

    # ── Group 5: topics ──
    {"id": "art-history",       "label": "藝術史",         "label_en": "Art History",                 "group": "topics",        "axes": [], "yearStart": -30000, "yearEnd": 2026},
    {"id": "music-history",     "label": "音樂史",         "label_en": "Music History",               "group": "topics",        "axes": [], "yearStart": -3000, "yearEnd": 2026},
    {"id": "medical",           "label": "醫學史",         "label_en": "History of Medicine",          "group": "topics",        "axes": [], "yearStart": -2600, "yearEnd": 2026},
    {"id": "space-exploration", "label": "太空探索",       "label_en": "Space Exploration",           "group": "topics",        "axes": [], "yearStart": 1942, "yearEnd": 2026},

    # ── Group 6: events ──
    {"id": "pandemics",         "label": "瘟疫與流行病",   "label_en": "Pandemics & Epidemics",       "group": "events",        "axes": [], "yearStart": -430, "yearEnd": 2026},
    {"id": "exploration",       "label": "大航海時代",     "label_en": "Age of Exploration",          "group": "events",        "axes": [], "yearStart": 1400, "yearEnd": 1600},
    {"id": "revolutions",       "label": "革命浪潮",       "label_en": "Revolutions",                 "group": "events",        "axes": [], "yearStart": 1640, "yearEnd": 2026},
    {"id": "disasters",         "label": "重大災害",       "label_en": "Major Disasters",             "group": "events",        "axes": [], "yearStart": -1600, "yearEnd": 2026},

    # ── Group 7: empires（王朝與帝國）──
    {"id": "akkadian",          "label": "阿卡德帝國",     "label_en": "Akkadian Empire",             "group": "empires",       "axes": [], "yearStart": -2334, "yearEnd": -2154},
    {"id": "ancient-egypt-empire","label":"古埃及帝國",     "label_en": "Ancient Egyptian Empire",     "group": "empires",       "axes": [], "yearStart": -3100, "yearEnd": -30},
    {"id": "persian-empire",    "label": "波斯帝國",       "label_en": "Persian Empire",              "group": "empires",       "axes": [], "yearStart": -550, "yearEnd": -330},
    {"id": "alexander-empire",  "label": "亞歷山大帝國",   "label_en": "Alexander's Empire",          "group": "empires",       "axes": [], "yearStart": -336, "yearEnd": -323},
    {"id": "roman-empire",      "label": "羅馬帝國",       "label_en": "Roman Empire",                "group": "empires",       "axes": [], "yearStart": -27, "yearEnd": 476},
    {"id": "byzantine",         "label": "拜占庭帝國",     "label_en": "Byzantine Empire",            "group": "empires",       "axes": [], "yearStart": 330, "yearEnd": 1453},
    {"id": "tang-dynasty",      "label": "唐朝",           "label_en": "Tang Dynasty",                "group": "empires",       "axes": [], "yearStart": 618, "yearEnd": 907},
    {"id": "arab-caliphate",    "label": "阿拉伯帝國",     "label_en": "Arab Caliphate",              "group": "empires",       "axes": [], "yearStart": 632, "yearEnd": 1258},
    {"id": "mongol-empire",     "label": "蒙古帝國",       "label_en": "Mongol Empire",               "group": "empires",       "axes": [], "yearStart": 1206, "yearEnd": 1368},
    {"id": "ottoman-empire",    "label": "鄂圖曼帝國",     "label_en": "Ottoman Empire",              "group": "empires",       "axes": [], "yearStart": 1299, "yearEnd": 1922},
    {"id": "mughal-empire",     "label": "莫臥兒帝國",     "label_en": "Mughal Empire",               "group": "empires",       "axes": [], "yearStart": 1526, "yearEnd": 1857},
    {"id": "spanish-empire",    "label": "西班牙帝國",     "label_en": "Spanish Empire",              "group": "empires",       "axes": [], "yearStart": 1492, "yearEnd": 1975},
    {"id": "british-empire",    "label": "大英帝國",       "label_en": "British Empire",              "group": "empires",       "axes": [], "yearStart": 1583, "yearEnd": 1997},
    {"id": "russian-empire",    "label": "俄羅斯帝國/蘇聯","label_en": "Russian Empire / USSR",       "group": "empires",       "axes": [], "yearStart": 1721, "yearEnd": 1991},
    {"id": "qing-dynasty",      "label": "清朝",           "label_en": "Qing Dynasty",                "group": "empires",       "axes": [], "yearStart": 1636, "yearEnd": 1912},
    {"id": "japanese-empire",   "label": "大日本帝國",     "label_en": "Empire of Japan",             "group": "empires",       "axes": [], "yearStart": 1868, "yearEnd": 1947},

    # ── Group 8: biographies ──
    {"id": "confucius",         "label": "孔子",           "label_en": "Confucius",                   "group": "biographies",   "axes": [], "yearStart": -551, "yearEnd": -479},
    {"id": "alexander",         "label": "亞歷山大大帝",   "label_en": "Alexander the Great",         "group": "biographies",   "axes": [], "yearStart": -356, "yearEnd": -323},
    {"id": "qin-shihuang",      "label": "秦始皇",         "label_en": "Qin Shi Huang",               "group": "biographies",   "axes": [], "yearStart": -259, "yearEnd": -210},
    {"id": "caesar",            "label": "凱撒",           "label_en": "Julius Caesar",               "group": "biographies",   "axes": [], "yearStart": -100, "yearEnd": -44},
    {"id": "genghis-khan",      "label": "成吉思汗",       "label_en": "Genghis Khan",                "group": "biographies",   "axes": [], "yearStart": 1162, "yearEnd": 1227},
    {"id": "columbus",          "label": "哥倫布",         "label_en": "Christopher Columbus",        "group": "biographies",   "axes": [], "yearStart": 1451, "yearEnd": 1506},
    {"id": "napoleon",          "label": "拿破崙",         "label_en": "Napoleon Bonaparte",          "group": "biographies",   "axes": [], "yearStart": 1769, "yearEnd": 1821},
    {"id": "einstein",          "label": "愛因斯坦",       "label_en": "Albert Einstein",             "group": "biographies",   "axes": [], "yearStart": 1879, "yearEnd": 1955},
]

added = 0
skipped = 0
for v in NEW_VIEWS:
    if v['id'] in existing_view_ids:
        skipped += 1
        continue
    d['views'].append(v)
    existing_view_ids.add(v['id'])
    added += 1

# ═══════════════════════════════════════════
# 3. 修正現有 views 的 group（dynasties → empires）
# ═══════════════════════════════════════════
# 如果有 view 指向已刪除的 group，改成對應的新 group
GROUP_MIGRATION = {
    "periods": "empires",      # periods 被刪，歸入 empires
    "dynasties": "empires",    # dynasties 被刪，歸入 empires
}
migrated = 0
for v in d['views']:
    old_group = v.get('group', '')
    if old_group in GROUP_MIGRATION:
        v['group'] = GROUP_MIGRATION[old_group]
        migrated += 1

# ═══════════════════════════════════════════
# 4. 儲存
# ═══════════════════════════════════════════
with open('data/events.json', 'w', encoding='utf-8') as f:
    json.dump(d, f, ensure_ascii=False, indent=2)

# ═══════════════════════════════════════════
# 報告
# ═══════════════════════════════════════════
print("=" * 60)
print("主題清單更新完成 v202604171052")
print("=" * 60)

print(f"\nview_groups: 10 → {len(d['view_groups'])} 個")
for g in d['view_groups']:
    count = sum(1 for v in d['views'] if v.get('group') == g['id'])
    print(f"  {g['id']:18s} {g['label']:10s} {count} 個 view")

print(f"\nviews: 新增 {added}、跳過(已存在) {skipped}、group 遷移 {migrated}")
print(f"views 總數: {len(d['views'])}")

print(f"\n請執行 python check.py 驗證")
