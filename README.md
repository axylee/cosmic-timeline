# 🌌 Cosmic History Timeline · 宇宙歷史時間軸

互動式時間軸，從宇宙誕生（138億年前）到今日。

**🔗 Live:** [cosmichistorytimeline.com](https://cosmichistorytimeline.com)
**✏️ Editor:** [cosmichistorytimeline.com/indexedit.html](https://cosmichistorytimeline.com/indexedit.html)

---

## 概覽

| | |
|---|---|
| 事件數 | 1,561 |
| 軸線數 | 101 |
| 視圖數 | 88 |
| 群組數 | 6（自然 · 世界 · 地區 · 文明 · 宗教 · 國家） |
| 視圖群組 | 8（自然宇宙 · 文明縱覽 · 國家 · 戰爭 · 主題 · 重大事件 · 王朝與帝國 · 人物傳記） |
| 語言 | 中文 / English |
| 書籍連結 | 1,549 個事件有 Amazon affiliate 連結 |

---

## 檔案結構

```
cosmic-timeline/
├── index.html              # 公開版（無編輯 UI）
├── indexedit.html           # 編輯版（含 edit panel）
├── about.html              # About / Contact / Privacy / Copyright
├── data/
│   └── events.json         # 所有事件、軸線、時代、UI 設定資料
├── tools/
│   ├── cosmic-tools.html         # 工具箱（新增事件/軸線 + 圖片管理 + 多候選 picker）
│   ├── images-find-missing.py    # 本機補圖腳本（單候選自動 + 多/零候選產 pending-picks）
│   └── images-check-dead.py      # 圖片死連結檢查腳本
├── images/                 # 事件圖片 + og-preview.png + kofi_symbol.svg
├── check.py                # 驗證 events.json 的 Python 腳本
├── add-events-*.py         # 修改 events.json 的 Python 腳本
├── ads.txt                 # Google AdSense 授權檔
├── sitemap.xml             # SEO sitemap
├── robots.txt              # SEO 爬蟲規則
├── netlify.toml            # Netlify 部署設定（擋開發檔案）
└── README.md
```

---

## Co-work 流程（協作）

### 改 events.json → 輸出 Python 腳本

1. 討論要加/改哪些事件
2. 確認清單後， 輸出 `add-events-YYYYMMDDHHmm.py`
3. 本機執行腳本 → `python check.py` 驗證
4. 用 cosmic-tools.html 補圖片
5. 上傳 GitHub → Netlify 自動部署

**腳本命名規則：** `add-events-YYYYMMDDHHmm.py`（年月日時分），例如 `add-events-202604151925.py`。不分 affiliate/events，統一命名。

### 改 index.html → 用 str_replace

1. 改前先提供時間更新版本號（例如 `v202604151942`）
2. 用 `str_replace` 精確修改
3. 改完 `node -e` 驗證 JS 語法
4. 動工前先討論確認清單，給時間才開工

### 本機測試

在專案資料夾開 PowerShell：

```powershell
cd C:\Users\aytle\OneDrive\蓁\20260409-cosmic-timeline
python -m http.server 8080
```

瀏覽器開 `http://localhost:8080/index.html`（解決 file:// CORS 問題）

---

## 新增 / 更新事件流程

### 完整流程圖

```
1. 討論事件清單
      ↓
2. 輸出 add-events-YYYYMMDDHHmm.py
      ↓
3. 本機執行 python add-events-xxx.py
      ↓
4. python check.py 驗證結構
      ↓
5. 補圖（依量擇一）：
   ├─ 小量（< 20 個）→ cosmic-tools.html（瀏覽器）
   └─ 大量（20+ 個）→ images-find-missing.py（本機 Python，推薦）
      ↓
6. 若有 pending-picks → 上傳給 AI 挑 → 出新的 add-events-xxx.py → 回步驟 3
      ↓
7. 再 python check.py 確認
      ↓
8. git push → Netlify 自動部署
```

### 步驟 1–4：建立事件

在 PowerShell 執行：

```powershell
cd C:\Users\aytle\OneDrive\蓁\20260409-cosmic-timeline\cosmic-timeline
python add-events-YYYYMMDDHHmm.py
python check.py
```

**成功輸出範例：**
```
✓ 新增 43 個事件（跳過 2 個）
✓ 總事件數：1561
完成！請執行 python check.py 驗證
```

### 步驟 5：補圖（兩種工具）

#### 小量 → cosmic-tools.html

在本機 Edge 開 `tools/cosmic-tools.html`，拖入 `data/events.json`，按「開始更新圖片」。
適合事件少、需要視覺確認、或同時要編輯軸線/視圖的時候。

#### 大量 → images-find-missing.py（推薦）

本機 Python 腳本，**繞過瀏覽器 CORS 限制**，多一個「解析 Wikipedia 頁面 HTML 抓 infobox 圖」的能力，成功率比 cosmic-tools.html 高。

**第一次使用需裝套件：**
```powershell
pip install requests
```

**執行：**
```powershell
python tools/images-find-missing.py              # 只補缺圖（image 為空）
python tools/images-find-missing.py --overwrite  # 覆蓋所有事件圖片
```

**雙軌輸出（都放在 tools/）：**

| 情況 | 產出 | 後續 |
|------|------|------|
| 單候選 | `add-events-YYYYMMDDHHmm-fill-images.py` | 覆蓋到根目錄執行即補圖 |
| 多候選 | `pending-picks-YYYYMMDDHHmm.json`（items[].candidates）| 上傳給 AI 挑 |
| 零候選 | `pending-picks-YYYYMMDDHHmm.json`（candidates:[]）| 上傳給 AI WebSearch 補 |

**pending-picks JSON 結構：**
```json
{
  "meta": { "generated", "count", "multi_candidate", "zero_candidate", "note" },
  "items": [
    {
      "id", "zh", "en", "axis", "year", "category",
      "desc_zh", "desc_en", "current_image",
      "wiki_zh", "wiki_en",
      "candidates": [ { "url", "label", "source" }, ... ]
    }
  ]
}
```

### 步驟 6：AI 挑圖（若有 pending-picks）

1. 上傳 `tools/pending-picks-YYYYMMDDHHmm.json` 給 AI
2. AI 依規則挑圖（例：**國家建立事件優先地圖而非旗幟**）；零候選事件 AI 可 WebSearch 補 URL
3. AI 輸出新的 `add-events-YYYYMMDDHHmm-images.py`（含 `IMAGE_UPDATES` 只更新 image 欄位）
4. 回步驟 3 執行

**cosmic-tools.html 手動 picker 輔助：** 多候選 popup 顯示 Wiki 中/EN + Google 圖片連結，候選全不合用時可點連結自己找 URL 貼上。

### 步驟 7–8：驗證 + 上線

```powershell
python check.py
# 確認無錯誤後
git add -A
git commit -m "Add events and images"
git push
```

Netlify 自動部署，幾分鐘後 cosmichistorytimeline.com 更新。

---

## check.py 說明

驗證 `data/events.json` 的結構與內容完整性。

**執行：** `python check.py`

**驗證項目：**
- 事件總數、有圖/缺圖統計
- en 名稱 / desc_en / category / wiki_zh / wiki_en 完整性
- 所有事件的軸線 ID 是否存在
- 所有事件年份是否在軸線起始年份之後
- 是否有重複 ID
- 所有軸線 group 是否合法
- 所有 View 引用的軸線是否存在
- axis_groups / era_bands / era_buttons / filter_cats / views 統計

**正常輸出範例：**
```
==================================================
  事件總數     : 1561
  有圖片       : 1353
  缺圖片       : 208
  有 en 名稱   : 1561  (缺 0)
  有 desc_en   : 1561  (缺 0)
  定義軸線數   : 101
  axis_groups  : 6 組
  era_bands    : 11 段
  era_buttons  : 12 個
  filter_cats  : 15 類
  views        : 88 個
==================================================

✓ 所有事件軸線正確
✓ 所有事件年份正確
✓ 無重複 ID
✓ 所有軸線 group 正確
✓ 所有 View 軸線正確
```

---

## add-events .py 腳本結構

每個腳本的標準結構：

```python
"""
新增 XX 個事件：
- axis_a N 個（說明）
- axis_b N 個（說明）

執行：python add-events-202604151925.py
驗證：python check.py
"""
import json

with open('data/events.json', encoding='utf-8') as f:
    d = json.load(f)

existing_ids = {e['id'] for e in d['events']}
added = 0

NEW_EVENTS = [
    {
        "id": "唯一ID", "year": -221, "axis": "china", "level": 1,
        "category": "politics",
        "zh": "中文名稱", "en": "English Name",
        "desc_zh": "中文描述", "desc_en": "English description",
        "wiki_zh": "https://zh.wikipedia.org/wiki/...",
        "wiki_en": "https://en.wikipedia.org/wiki/...",
        # 可選欄位：
        # "endYear": 220,          # 有填 = pill，沒填 = 點
        # "crossRef": "cross",     # 或 ["cross","trade"]
        # "amazon_asin": "0553380168",
        # "amazon_title": "A Brief History of Time",
    },
]

for ev in NEW_EVENTS:
    if ev['id'] in existing_ids:
        print(f"⊘ 跳過（ID 已存在）: {ev['zh']}")
        continue
    d['events'].append(ev)
    existing_ids.add(ev['id'])
    print(f"✓ 新增: {ev['zh']}  [{ev['axis']}]")
    added += 1

# 儲存（保持 key 順序）
ordered = {}
key_order = ['meta', 'axis_groups', 'axes', 'era_bands', 'era_buttons', 'filter_cats', 'views', 'events']
for k in key_order:
    if k in d: ordered[k] = d[k]
for k in d:
    if k not in ordered: ordered[k] = d[k]

with open('data/events.json', 'w', encoding='utf-8') as f:
    json.dump(ordered, f, ensure_ascii=False, indent=2)

print(f"\n{'='*45}")
print(f"  新增事件: {added} 個")
print(f"  總事件數: {len(d['events'])}")
print(f"{'='*45}")
print("完成！請執行 python check.py 驗證")
```

---

## 導覽操作

| 操作 | 說明 |
|------|------|
| 滑鼠滾輪 | 水平縮放（以游標位置為中心） |
| 拖曳畫布 | 水平平移 |
| Shift + 滾輪 | 垂直捲動 |
| Ctrl + 滾輪 | 垂直縮放（軸線間距） |
| 右側垂直滑桿 | 垂直縮放 |
| 右側捲軸 | 垂直捲動 |
| ⊙ 按鈕 | 全覽（回到最小縮放） |
| 底部時代按鈕 | 快速跳到該時代 |
| 手機 pinch | 縮放 |

### Legend（右側面板）

| 操作 | 說明 |
|------|------|
| 單擊軸線/群組 | 顯示 / 隱藏 |
| 雙擊軸線/群組 | 凸顯模式（只顯示該項，其他淡化） |
| 凸顯時單擊其他 | 加入顯示 |
| 再雙擊同一條 | 退出凸顯 |
| 凸顯透明度滑桿 | 調整淡化程度 |
| 全部顯示按鈕 | 清除所有隱藏、凸顯與篩選 |

### 搜尋
- 支援中文、英文、年份搜尋
- Enter 跳轉到第一個結果並開啟 popup

### 主題視圖 / 篩選
- **主題**按鈕：自動隱藏無關軸線 + zoom 到對應時間範圍
- **篩選**按鈕：按 category 多選篩選（戰爭/科學/宗教/文化等15類）
- 可同時使用（先選視圖縮小範圍，再篩選看特定類型）

### 語言切換
- 右上角「中 / EN」按鈕，設定記憶在瀏覽器

---

## events.json 完整結構

```
events.json
├── meta              # 專案基本資訊
├── axis_groups       # 軸線群組定義（6 組）
├── axes              # 軸線定義（101 條）
├── era_bands         # Canvas 背景時代色帶（11 段）
├── era_buttons       # 底部導航按鈕（12 個）
├── filter_cats       # 篩選分類（15 類）
├── views             # 主題視圖（88 個）
└── events            # 歷史事件（1,561 個）
```

> 所有 UI 資料都從 JSON 動態載入，index.html 不寫死任何資料。

---

## events.json 欄位說明

### axes（軸線）

| 欄位 | 必填 | 說明 |
|------|------|------|
| `id` | ✓ | 唯一識別碼（英文小寫 + 連字號） |
| `label` | ✓ | 中文顯示名稱 |
| `label_en` | ✓ | 英文顯示名稱 |
| `color` | ✓ | 顏色 hex |
| `order` | ✓ | 排列順序（數字越小越上方，支援小數點） |
| `parent` | | 父軸 id（null = 頂層） |
| `startYear` | ✓ | 分支線起始年份 |
| `endYear` | | 消亡年份（null = 至今） |
| `zoomMin` | ✓ | 顯示門檻（0 = 全局，0.58 = zoom in才出現） |
| `group` | ✓ | natural / global / region / civilization / religion / nation |

**Order 區間規則：**

| group | order 區間 |
|-------|-----------|
| natural | 0 ~ 9 |
| global | 10 ~ 19 |
| region | 20 ~ 29 |
| civilization | 30 ~ 49 |
| religion | 50 ~ 59 |
| nation | 60 ~ 99 |

**「緊跟 parent」只在同 group 內適用。** 跨 group 的 scope 軸應回自己的 group 區間，不可為了挨著 parent 而越界。

範例：
- `italy-roman`(civilization) 不能用 66.21 緊跟 `italy`(nation)，應回 civilization 區間 40.5（near `greece`=38）
- `modern-greece`(nation) 不能用 42.5，應回 nation 區間 66.0
- `europe` 本質跨國，group=region order=21.5（不是 nation 66）

**戰爭 scope 軸約定（region 群組 28.1–29.0）：**

所有戰爭 scope 軸：`parent=cross`、`group=region`、order 依時代排序於 28.1–29.0：

| order | 軸 |
|-------|-----|
| 28.1 | peloponnesian-war |
| 28.2 | punic-wars |
| 28.3 | crusades |
| 28.4 | thirty-years-war |
| 28.5 | seven-years-war |
| 28.6 | american-revolution |
| 28.7 | napoleonic-wars |
| 28.8 | ww1 |
| 28.9 | ww2 |
| 29.0 | cold-war |

**原則：單一 unified scope 軸 + 必要時搭配 theater sub-scope。**
- unified 例：`korean-war` / `vietnam-war` / `american-civil-war`（一軸裝主事件）
- theater 例：`ww1-western/eastern/mideast`、`ww2-europe/pacific`（war dedicated view 的戰場細節）

### events（事件）

| 欄位 | 必填 | 說明 |
|------|------|------|
| `id` | ✓ | 唯一識別碼 |
| `year` | ✓ | 年份（負數 = BC） |
| `zh` | ✓ | 中文名稱 |
| `en` | | 英文名稱 |
| `axis` | ✓ | 所在軸線 id |
| `level` | ✓ | 重要程度（1=大 2=中 3=小） |
| `endYear` | | 結束年份（有填 = pill，沒填 = 點）。填 `"__NOW__"` 表示「至今」 |
| `parentEvent` | | 父事件 id（用於地質年代展開層級） |
| `crossRef` | | 縱線連接目標軸線，支援字串或陣列（最多3條） |
| `image` | | 圖片 URL |
| `desc_zh` | | 中文描述 |
| `desc_en` | | 英文描述 |
| `wiki_zh` | | 中文 Wikipedia URL |
| `wiki_en` | | 英文 Wikipedia URL |
| `category` | | civilization / politics / war / science / religion / culture / ... |
| `amazon_asin` | | Amazon 書籍 ASIN（affiliate 連結用） |
| `amazon_title` | | Amazon 書籍標題 |
| `books_id` | | 博客來書籍 ID（審核通過後使用） |

---

## 軸線架構

設計原則：**演化順序**（自然 → 世界 → 地區 → 文明 → 宗教 → 國家）

### 群組定義

- **自然 natural**：人類出現之前的宇宙、地球、生命演化過程
- **世界 global**：人類行為觸發、跨越多個地區影響全人類的活動與主題
- **地區 region**：地理容器，不代表特定文明，人類到達後就一直存在
- **文明 civilization**：符合「文明六特徵」中四項以上的社會體系
- **宗教 religion**：從文明中誕生的精神信仰體系
- **國家 nation**：近代政治實體

### 文明判定標準（符合 4 項以上歸入 civilization）

1. 城市（urban centers）
2. 政府/制度（centralized government）
3. 社會階層（social stratification）
4. 文字/記錄系統（writing/record keeping）
5. 專業分工（specialized labor）
6. 獨特文化表現（arts, architecture, religion）

### 文明 → 國家的接續設計

```
persia 波斯 (civilization, -559 → endYear:1501)
└─ iran 伊朗 (nation, 1501 → 至今)
```

> 以下為**主軸代表**列表（共 101 條含 scope 子軸）。戰爭/國家/文明 sub-scope 軸隨資料成長，全量請見 `data/events.json`。

### 🌌 natural 自然（12 條）

```
cosmos 宇宙
└─ galaxy 銀河系
   └─ solar-system 太陽系
      └─ earth 地球
         ├─ climate 氣候
         └─ life 生命
            └─ human-evo 人類演化
               └─ migration 人類遷徙
```

### 🌍 global 世界（4 條）

```
cross 跨文明 ← human-evo
├─ trade 貿易
├─ science 科學技術
└─ arts 藝術文化
```

### 🗺 region 地區（20 條，含 10 戰爭 scope 軸 28.1–29.0）

```
east 東方 ← human-evo
west 西方 ← human-evo
africa 非洲 ← human-evo
americas 美洲 ← human-evo
central-asia 中亞/北亞 ← migration
southeast-asia 東南亞 ← migration
oceania 大洋洲 ← migration
arctic 北極 ← migration
antarctic 南極 ← migration
```

### 🏛 civilization 文明（21 條）

```
mideast 中東 ← east
├─ mesopotamia 兩河流域 (endYear: -539)
├─ egypt 古埃及 (endYear: 641)
├─ persia 波斯/伊朗 (endYear: 1501)
└─ ottoman 鄂圖曼帝國 (endYear: 1922)
kush 庫什/努比亞 ← africa (endYear: 350)
india 印度 ← east
korea 韓國 ← east
china 中國 ← human-evo
japan 日本 ← east
greece 希臘羅馬 ← west (endYear: 476)
└─ byzantine 拜占庭帝國 (endYear: 1453)
latin-america 拉丁美洲 ← americas
siam 暹羅 ← southeast-asia (endYear: 1932)
mongol 蒙古帝國 ← central-asia (endYear: 1368)
```

### ✝ religion 宗教（6 條）

```
judaism 猶太教 ← mideast
└─ christianity 基督教
islam 伊斯蘭教 ← mideast
hinduism 印度教 ← india
└─ buddhism 佛教
taoism 道教 ← china
```

### 🏳 nation 國家（38 條，含 country-scope 子軸）

```
iran 伊朗 ← persia              ← 文明→國家接續
iraq 伊拉克 ← mesopotamia        ← 文明→國家接續
modern-egypt 現代埃及 ← egypt     ← 文明→國家接續
turkey 土耳其 ← ottoman          ← 文明→國家接續
thailand 泰國 ← siam             ← 文明→國家接續
mongolia 蒙古國 ← mongol         ← 文明→國家接續
north-africa 北非 ← africa
west-africa 西非 ← africa
east-africa 東非 ← africa
south-africa 南非 ← africa
taiwan 臺灣 ← human-evo
europe 歐洲 ← west
north-america 北美 ← americas
south-america 南美 ← americas
usa 美國 ← north-america
australia 澳洲 ← oceania
brazil 巴西 ← south-america
```

---

## 色系規則

每 group 5 個色階 A→E 循環套用：

| group | 色系 |
|-------|------|
| natural | 紫→藍→綠漸層 `#a78bfa` `#c4b5fd` `#818cf8` `#60a5fa` `#7dd3fc` |
| global | 灰白/淺黃/淺藍/藍 `#e2e8f0` `#fcd34d` `#67e8f9` `#3b82f6` |
| region | 粉紫玫瑰系 `#f472b6` `#a78bfa` `#ec4899` `#fb7185` `#c084fc` |
| civilization | 橘紅金 `#fbbf24` `#f97316` `#ef4444` `#d97706` `#fb923c` |
| religion | 綠色系 `#86efac` `#059669` `#2dd4bf` `#15803d` `#5eead4` |
| nation | 全藍 `#93c5fd` `#3b82f6` `#1d4ed8` `#60a5fa` `#1e40af` |

---

## 關鍵參數

| 參數 | 值 | 說明 |
|------|-----|------|
| `LANE_GAP_BASE` | 54 | 軸線間距 |
| `EXPAND_ROW_H` | 14 | 展開 pill 間距 |
| bottom-bar 高度 | 90px | 左 300px ad-slot + 右 controls |
| search-wrap | max-width 240px | 搜尋框寬度 |
| search-results | min-width 360px | 搜尋結果下拉寬度 |

---

## 專題頁規劃

### 架構設計

**一個 `index.html` + 一個 `events.json`，不拆檔。** 用 URL 參數 `?v=<view-id>` 決定要顯示哪個專題，由 `view_groups` 定義分類，由軸線的 `scope` 欄位控制該軸線在哪些頁面出現。

**核心邏輯：**
- 主頁（`/`）= 全景，顯示沒標 `scope` 的軸線
- 專題頁（`/?v=china`）= 顯示 `scope` 含 `"china"` 的軸線 + 沒標 scope 的軸線
- 沒標 `scope` 的軸線 = 到處都顯示（預設行為，向下相容）
- 空 view（axes: []）不顯示在主題選單
- 空 group（底下沒有任何有內容的 view）不顯示在主題選單

### view_groups（8 個分類）

```
nature-cosmos   自然與宇宙      Nature & Cosmos       （宇宙、地球、生命、演化）
civilization    文明縱覽        Civilizations         （古代文明、文明對比）
countries       國家           Countries             （地區總覽 + 各國歷史）
wars            戰爭           Wars                  （各場戰爭專題）
topics          主題           Topics                （跨時代主題）
events          重大事件        Major Events          （瘟疫、航海、革命、災害）
empires         王朝與帝國      Dynasties & Empires   （羅馬、蒙古、大英帝國…）
biographies     人物傳記        Biographies           （重要人物一生）
```

### 軸線設計

每個專題頁的結構：

```
主軸（例：china）              ← 沒有 scope，主頁+專題頁都看到
├── 子軸（china-emperor）       ← scope: ["china"]，只在中國頁看到
├── 子軸（china-war）           ← scope: ["china"]
├── 子軸（china-literature）    ← scope: ["china"]
└── 子軸（china-science）       ← scope: ["china"]
```

規則：
- 主軸**沒有 scope**（主頁全局 + 專題頁都看到）
- 子軸**標 scope**（只在對應專題頁看到，主頁隱藏）
- 子軸的 parent = 主軸
- 子軸 label 帶國家前綴（「中國戰爭」而非「戰爭」，避免未來跟「日本戰爭」混淆）
- 子軸的 color 跟主軸同色系但有區隔

### 事件分配核心原則

**大事件放全局軸 + crossRef 到主題軸，小事件放主題軸。**

| 事件重要性 | axis 放哪 | crossRef | 全局看得到？ | 主題頁看得到？ |
|-----------|----------|----------|------------|-------------|
| 大事件（POINT） | 全局軸（life, earth, china...） | 主題子軸 | ✅ 實心圓 | ✅ 全局軸實心圓 + 子軸空心圓 |
| 大事件（PILL） | 主題子軸（需要長條） | — | ✅ 全局軸加 mark point | ✅ 子軸 pill + 全局軸 mark point |
| 小事件 | 主題子軸 | — | ❌ | ✅ 子軸實心圓 |

這個規則適用於所有主題：中國、台灣、恐龍、新生代、未來的日本/二戰/任何主題。

**不重複原則：** 一個事件只能有一個 `axis`。如果兩條軸線（例如 `human-evo` 和 `cenozoic-life`）都跟同一個事件相關，事件放在**更全局的那條軸線**上，用 `crossRef` 連到另一條。**絕不在兩條軸線上各放一個同名事件。**

### 事件分配規則（三種情況）

#### 情況 1：重要的 POINT 事件

**放在主軸，crossRef 到子軸線。一個事件，不重複。**

```json
{
  "id": "emperor-qin-shi",
  "year": -221,
  "zh": "秦始皇統一六國",
  "axis": "china",
  "crossRef": ["china-emperor"]
}
```

- 主頁 china 線：**實心圓** ✅
- 中國頁 china-emperor 線：**空心圓** ✅

crossRef 可以同時連全域軸線和子軸線，例如都江堰：

```json
{
  "id": "dujiangyan",
  "axis": "china",
  "crossRef": ["science", "china-science"]
}
```

- 主頁 china 線：實心圓 ✅
- 主頁 science 線：空心圓 ✅
- 中國頁 china-science 線：空心圓 ✅

#### 情況 2：重要的 PILL 事件（有 endYear）

**PILL 留在子軸線（顯示時間跨度），另在主軸加一個同名 point 標記。兩個事件。**

```json
// 子軸線上的 PILL
{
  "id": "war-sino-japanese1",
  "year": 1894, "endYear": 1895,
  "zh": "甲午戰爭",
  "axis": "china-war"
}

// 主軸上的 mark point
{
  "id": "mark-war-sino-japanese1",
  "year": 1894,
  "zh": "甲午戰爭",
  "axis": "china",
  "crossRef": ["china-war"]
}
```

- 主頁 china 線：**實心圓**「甲午戰爭」 ✅
- 中國頁 china-war 線：**pill 長條** 1894-1895 ✅ + 空心圓 ✅

#### 情況 3：不重要的事件

**只放在子軸線，不放主軸。全局看不到，專題頁才看到。**

```json
{
  "id": "war-feishui",
  "year": 383,
  "zh": "淝水之戰",
  "axis": "china-war"
}
```

- 主頁：看不到（設計如此，不是 bug）
- 中國頁 china-war 線：**實心圓** ✅

### 判斷「重要」的標準

| 重要（放主軸） | 不重要（只放子軸） |
|---|---|
| 改變國家走向的事件 | 地方性戰役 |
| 全球知名的人物/事件 | 地區性人物 |
| 教科書一定會提的 | 專家才知道的 |
| 影響其他文明的（有 crossRef 價值） | 只影響本國的 |
| 每條子軸線挑 4-6 個最重要 | 其餘放子軸 |

### crossRef 語義

| 畫面 | 語義 |
|---|---|
| 實心圓 | 事件的**主體/起因**發生在這條軸線 |
| 空心圓 | 事件**影響了/有關於**這條軸線，但主體不在這裡 |

crossRef 最多 3 條，可同時連全域軸線和專題子軸線。

### 實作階段

| Round | 內容 | 狀態 |
|-------|------|------|
| Round 1 | view_groups 架構重構（10→8 groups） | ✅ 已完成 |
| Round 2 | URL 路由 `?v=xxx` + scope 軸線過濾 | ✅ 已完成 |
| Round 3 | crossRef 空心圓不依賴本體軸線可見性 | ✅ 已完成 |
| Round 4 | 專題頁「全部顯示」→ 跳主頁帶 zoom 參數 | ✅ 已完成 |
| Round 5 | 中國/台灣/恐龍/新生代範例（軸線 + 事件 + 驗證） | ✅ 已完成 |
| Phase I | 戰爭 scope 軸架構（10 unified）+ 10 Phase 1 國家 view（france/germany/uk/italy/russia/egypt/greece/iran/turkey/usa）| ✅ 已完成（04-24）|
| Phase II | 15 country-war 關係（歐美 6 REPLACE、亞洲 4 ADD、補齊歐洲中東覆蓋）| ✅ 已完成（04-24）|
| Phase III | War dedicated view 事件細化（korean-war → cold-war 依短→長）| 🚧 進行中 |
| Phase IV | Regional views（reg-europe / reg-mideast / reg-eastasia ...）戰爭覆蓋 | ⏳ 待做 |
| Phase V | Empire views（16 個，依事件密度低→高）| ⏳ 待做 |
| Phase VI | Biographies（8 人物起，依生命短→長；見「人物傳記 view SOP」section）| 🚧 進行中 |
| Phase VII | 其他補強（pandemics / music-history / ancient-civ / exploration bug）| ⏳ 待做 |

### 新增其他國家的流程

例如「加日本史」：

1. 建子軸線（都標 `scope: ["japan"]`）
2. 分配事件（三種情況規則）
3. 建 view（group: countries, axes 包含主軸+子軸+相關共用軸線）
4. 出 `add-events-YYYYMMDDHHmm.py` 腳本
5. 本機執行 → check.py 驗證 → 測試

### 未來擴充判斷

新增專題頁時，先蒐集網路資料評估，再個別討論：
- 需要哪些獨有軸線
- 哪些事件是共用的（用 crossRef 標記）
- 約 40+ 事件才值得做獨立頁

---

## Affiliate 欄位

### Popup 顯示邏輯

- 有 `amazon_asin` → 顯示金色 📚 亞馬遜/Amazon 連結（帶 affiliate tag `cosmictimelin-20`）
- 有 `books_id` → 顯示金色 📚 博客來/Books 連結
- 沒有 → 不顯示
- 跟隨中/EN 語言切換
- CSS: `.popup-link-affiliate` 金色邊框 `#fbbf24`

---

## 賺錢管道

| 管道 | 狀態 |
|------|------|
| Google AdSense | 審核中 |
| Amazon Associates | 已通過（ID: cosmictimelin-20） |
| 博客來 AP | 審核中 |
| Ko-fi | [ko-fi.com/universetimeline](https://ko-fi.com/universetimeline) |

---

## SEO

- `<meta>` description + canonical URL
- Open Graph + Twitter Card 標籤
- JSON-LD 結構化資料（WebApplication / Education）
- `sitemap.xml` + `robots.txt`
- Google Search Console 已註冊 + sitemap 已提交

---

## 人物傳記 view (Phase VI) SOP

### Order 區段（biographies 專屬）

人物 bio-* 軸全 scope（全景看不到、legend 不被人物塞爆），order 配置在 emp-* 結束後（56-59 區段）。

19 人按時序排：

```
56.00-56.19  alexander       (-356~-323)
56.20-56.39  qin-shihuang    (-259~-210)
56.40-56.59  napoleon        (1769~1821)
56.60-56.79  caesar          (-100~-44)
56.80-56.99  columbus        (1451~1506)
57.00-57.19  genghis-khan    (1162~1227)
57.20-57.39  confucius       (-551~-479)
57.40-57.59  einstein        (1879~1955)
57.60-57.79  da-vinci        (1452~1519)
57.80-57.99  darwin          (1809~1882)
58.00-58.19  tesla           (1856~1943)
58.20-58.39  michelangelo    (1475~1564)
58.40-58.59  galileo         (1564~1642)
58.60-58.79  curie           (1867~1934)
58.80-58.99  joan-of-arc     (1412~1431)
59.00-59.19  mozart          (1756~1791)
59.20-59.39  beethoven       (1770~1827)
59.40-59.59  cleopatra       (-69~-30)
59.60-59.79  hannibal        (-247~-183)
```

每人 0.20 區段：主軸 .x0、sub-scope .x05/.x10/.x15。

### 軸結構（每個 bio view 的 axes 列表）

| 軸類型 | scope | group | 數量 |
|---|---|---|---|
| 1. bio 主軸 `bio-<id>` | `[<bio-id>]` | civ | **必 1 條**（pill 生卒年 + 主要事件 marker）|
| 2. bio sub-scope `bio-<id>-<sub>` | `[<bio-id>]` | civ | **0-3 條彈性**（依人物特性切；事件少可不切）|
| 3. cross 軸 | — | global | **必 1 條**（同時代世界對比）|
| 4. 相關 global 軸（trade/science/arts）| — | global | 0-2 條彈性 |
| 5. 相關 civ/nation/帝國軸 | — | civ/nation | 0-5 條彈性（**只用既有不新建**）|

**何時切 sub-scope（決策樹）**：
- 事件 < 8 → 不切
- 事件 8-12 主題集中 → 不切
- 事件 8-12 主題分明 → 切 1-2 條（如 alexander conquest/aftermath）
- 事件 12+ 或跨領域 → 切 2-3 條（如 einstein physics/pacifism；達文西 art/science）

### 事件規格（人物 view 不限事件數，越精彩越好，最少 8 條）

| 類型 | 軸 |
|---|---|
| 出生 point | bio-主軸 |
| 生卒 pill | bio-主軸 |
| 早年/教育 point | bio-主軸 |
| 關鍵時期 pill | bio-主軸或 sub-scope |
| 高峰時刻 point | bio-主軸或 sub-scope / 既有時代軸 |
| 死亡 point | bio-主軸 |
| 後世影響 point | bio-主軸或 sub-scope |

**重用既有事件**：先在 events.json 找已有的人物相關事件（如 julius-caesar、emp-alex-conquest 區段事件），直接 `crossRef` 加 `bio-<name>` 即可，**不重建**。bio-only 事件才新建（出生/教育/死亡場景/私人軼事）。

### CrossRef 規則
- bio-only 事件 → crossRef 到時代主軸（greece, persia, cross 等）
- 既有重大事件 → 在原本軸上新增 `crossRef: ["bio-<name>"]`，雙向連動

### Agg 頁過濾邏輯（generate-pages.py 已支援）

bio view 用 `view.core_axes = ["bio-<id>", "bio-<id>-<sub>", ...]`。
generate-pages.py 的 manual focus 模式會抓兩種事件：
1. `event.axis ∈ core_axes`（直接放在 bio 軸的事件）
2. `event.crossRef ∩ core_axes ≠ ∅`（其他軸 crossRef 回 bio 軸的既有歷史事件）

→ Agg 頁含完整人物相關事件全集（不限事件數）。

### 配套元件

| 元件 | 工具 |
|---|---|
| `view.intro_zh / intro_en` | `fetch-intros.py` LLM 跑 |
| `view.yearStart / yearEnd` | 手寫（生卒 ±20 年）|
| `event.desc_zh / desc_en` | 手寫（必要時 LLM 草稿輔助）|
| `event.amazon_asin` | 1-3 本高銷量傳記書 |
| `event.image` | `fetch-images-best.py` LLM scoring |
| `event.image_credit` | `fetch-image-credits.py` |
| `view.core_axes` | 寫 patch 時設 |
| sitemap | `generate-pages.py --all` 自動 |

bio view **不跑** `fetch-relevance.py`（用 core_axes 擴充過濾即可，比 LLM 精準）。

### 命名規則

| 元件 | 格式 | 範例 |
|---|---|---|
| bio 主軸 id | `bio-<lowercase-name>` | `bio-alexander` |
| bio 主軸 label | 中文人名 | `亞歷山大` |
| bio sub-scope id | `bio-<name>-<topic>` | `bio-alexander-conquest` |
| bio sub-scope label | 中文人名·主題 | `亞歷山大·征服` |
| bio 事件 id | `bio-<name>-<eventslug>` | `bio-alexander-birth` |
| patch 檔名 | `add-events-YYYYMMDDHHmm-bio-<name>.py` | — |

### 每人物執行流程

```bash
python add-events-YYYYMMDDHHmm-bio-<name>.py
python check.py
ANTHROPIC_API_KEY="..." python fetch-intros.py <bio-id>
python fetch-images-best.py
python fetch-image-credits.py
python generate-pages.py <bio-id>
# review → 進下一人
```

8 人全做完後一次性：
```bash
python generate-pages.py --all
```

---

## 部署

- **Hosting:** Netlify（GitHub push 後自動部署）
- **Domain:** [cosmichistorytimeline.com](https://cosmichistorytimeline.com)
- **SSL:** Let's Encrypt（自動更新）
- **netlify.toml** 擋開發檔案：check.py, tools/, README.md, add-events-* 回傳 404

### Netlify 注意事項

- Free plan 每月 300 credits，計費週期每月 15 號
- **每次部署消耗約 15 credits**，累積改動一批再 push
- 用戶瀏覽幾乎不花 credits（945 次 = 0.2 credits）
- 暫停部署：Site settings → Build & deploy → Stop builds

---

## 開發記錄

| 日期 | 內容 |
|------|------|
| 2026-04-09 | 專案建立，Canvas 時間軸基礎 |
| 2026-04-10 | 動態軸線系統、事件資料架構 |
| 2026-04-11 | Legend、Solo 模式、中英切換、搜尋、Popup 編輯、cosmic-tools.html |
| 2026-04-12 | crossRef 多軸、Events 視圖、Filter 篩選、era bands |
| 2026-04-13 | JSON 集中化、完整英文化、57 新事件、群組重整（7→6 組） |
| 2026-04-14 | 色系統一、地質年代層級、__NOW__ endYear、6 文明 + 7 國家軸線 |
| 2026-04-14 | 90 新事件（cosmos/galaxy/solar-system/science），802 事件 |
| 2026-04-15 | Ko-fi、AdSense、about.html、SEO 全套 |
| 2026-04-15 | Netlify 部署 + 域名 cosmichistorytimeline.com + SSL |
| 2026-04-15 | Amazon Associates 通過、30 本書籍連結、popup affiliate UI |
| 2026-04-15 | index.html / indexedit.html 分離 |
| 2026-04-16 | Google Search Console 註冊 + sitemap 提交 |
| 2026-04-16 | indexedit 加書籍編輯欄位（amazon_asin/title、books_id/title），cosmic-tools 加「書籍管理」分頁 |
| 2026-04-16 | 架構重構 Round 1：新增 view_groups（10 個分類）、views 的 `category` 改 `group`、空 group 不顯示 |
| 2026-04-16 | Round 2-4：URL 路由 `?v=xxx`、scope 軸線過濾、crossRef 空心圓跨頁、跨頁導航 |
| 2026-04-16 | Round 5a+b：中國史專題軸線（帝王/戰爭/文學/科技）+ china view + cosmos 早期事件修正 |
| 2026-04-17 | scope bug fix：buildAxes 改為全部載入、scope 在顯示階段過濾、pill 間距 14px |
| 2026-04-17 | view_groups 10→8（刪 periods/dynasties，empires 改「王朝與帝國」）、87 個 view 骨架全部建立 |
| 2026-04-17 | Round 5c：中國事件第 1 批（帝王 16 + 戰爭 14 + 文學 12 + 朝代補 2 = 44 新事件）+ 事件分配規則確立 |
| 2026-04-17 | 中國事件第 2 批：補 crossRef 29 個 + wiki 67 個 + 新增 21 個事件（孫子兵法、甲骨文、瓷器...） |
| 2026-04-17 | 台灣主題：2 子軸（colonial/culture）+ 32 事件（日治/民主化/原住民/鳥居龍藏/森丑之助/鹿野忠雄） |
| 2026-04-17 | 恐龍主題：2 軸（dinosaurs/dino-species）+ 33 事件（暴龍/三角龍/棘龍...24 物種 + 9 里程碑） |
| 2026-04-17 | applyView zoom 改用 view yearStart/yearEnd（有定義優先，無定義用 axes 自動算，向下相容） |
| 2026-04-17 | 新生代生命演化主題：2 軸（cenozoic-epochs/cenozoic-life）+ 35 事件（7 世 pill + 28 生命事件） |
| 2026-04-17 | 人類演化補 4 個早期物種（查德沙赫人/千年始祖/始祖地猿 Ardi/巧人）|
| 2026-04-18~21 | 國家 view pilot（Phase 1）：france/germany/uk/italy/russia 5 國歐洲試點，建立 country-view 升級通用流程（sub-scope 軸 + pills + crossRef 三管齊下）|
| 2026-04-22~23 | Phase 1 續：egypt/greece/iran 加入；修正 Ottoman/Byzantine 覆蓋；Amazon ASIN 書庫累積至 10 國 100+ 本 |
| 2026-04-24 | ★ 戰爭架構大重構：建 10 條 unified war scope 軸（region 28.1–29.0，parent=cross）、WW1/WW2 事件由 home/europe 遷移至 unified、刪空軸 |
| 2026-04-24 | Phase 1 收尾：turkey/usa 完成（建 korean-war / vietnam-war 軸）；Phase 2：15 country view 加戰爭 scope 軸，歐美 6 國 REPLACE sub-scope→unified、亞洲 4 國 ADD unified |
| 2026-04-24 | Order 規則釐清：「緊跟 parent」僅同 group 內；修正 italy-roman / modern-greece / europe 違規 order；events 達 1,561、axes 達 101、Amazon ASIN 1,549 |
| 2026-04-24 | Tool 強化：cosmic-tools.html picker popup 加 Wiki 中/EN + Google 圖片連結；images-find-missing.py 改雙軌輸出（單候選 .py + 多/零候選 pending-picks.json）|
