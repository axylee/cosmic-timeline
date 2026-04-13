# 🌌 Cosmic History Timeline · 宇宙歷史時間軸

互動式時間軸，從宇宙誕生（138億年前）到今日。  
**線上版本：** https://axylee.github.io/cosmic-timeline/

---

## 檔案結構

```
cosmic-timeline/
├── index.html                # 主時間軸 UI
├── data/
│   └── events.json           # 所有事件、軸線、時代、UI 設定資料
├── tools/
│   └── cosmic-tools.html     # 工具箱（新增事件/軸線 + 圖片管理）
├── check.py                  # 驗證 events.json 的 Python 腳本
├── add-events-sample.py      # 修改 events.json 的 Python 腳本樣板
└── README.md
```

---

## 常見需求 → 操作步驟

### ─── 大批量新增事件（找 Claude）────────────────────

這是新增大量歷史事件的標準流程，適合一次加入10個以上事件。

#### 完整流程

```
1. 找 Claude 討論要加哪些事件
      ↓
2. 確認事件清單後，Claude 輸出 Python 腳本
      ↓
3. 本機執行腳本（見下方說明）
      ↓
4. 執行 check.py 驗證
      ↓
5. 用 cosmic-tools.html 補圖片
      ↓
6. 上傳 GitHub
```

#### 步驟3：在本機執行 Python 腳本

**開啟 PowerShell 的方法：**

1. 在檔案總管中，瀏覽到專案資料夾：
   ```
   C:\Users\aytle\OneDrive\蓁\20260409-cosmic-timeline
   ```
2. 在資料夾空白處按住 **Shift + 右鍵**
3. 選擇「**在這裡開啟 PowerShell 視窗**」
4. PowerShell 會直接在這個資料夾開啟

**執行腳本：**

把 Claude 輸出的 `.py` 腳本放到專案根目錄，然後在 PowerShell 輸入：

```powershell
python add-events-202604111951.py
```

> 💡 腳本命名規則：`add-events-YYYYMMDDHHMI`（年月日時分），例如 `add-events-202604111951.py`

**成功的輸出範例：**
```
✓ 新增 43 個事件（跳過 2 個）
✓ 總事件數：382
完成！請執行 python check.py 驗證
```

#### 步驟4：執行 check.py 驗證

同一個 PowerShell 視窗繼續輸入：

```powershell
python check.py
```

**正常輸出範例：**
```
=============================================
  事件總數   : 382
  有圖片     : 302
  缺圖片     : 80
  有 crossRef: 110
  定義軸線數 : 37
=============================================
✓ 所有事件軸線正確
✓ 無重複 ID
```

> ⚠ 如果出現「軸線不存在」或「重複 ID」的警告，回去找 Claude 修正腳本

#### 步驟5：補圖片

1. 用瀏覽器開啟 `tools/cosmic-tools.html`
2. 切換到「🖼 圖片管理」分頁
3. 載入剛才更新的 `data/events.json`
4. 點「▶ 開始更新圖片」→ 自動搜尋 Wikipedia/NASA 圖片
5. 有多張候選圖時手動選擇最佳
6. 完成後點「📋 預覽變更並輸出」→ 確認後下載

> 💡 圖片可以之後再補，先上傳讓新事件上線，缺圖會顯示佔位符

#### 步驟6：上傳 GitHub

把以下檔案上傳到 GitHub（覆蓋舊版本）：
- `data/events.json`

---

### ─── 事件 ───────────────────────────────────────

#### 📍 查看事件詳情
1. 直接點擊時間軸上的圓點或 pill
2. Popup 顯示：父軸 › 軸線 ⤴ crossRef · 年份、描述、Wikipedia 連結

#### 🔍 搜尋並跳轉到事件
1. 點擊頂部搜尋框（或按鍵盤直接輸入）
2. 輸入中文名稱、英文名稱或年份
3. 下拉選擇結果，或按 Enter 跳轉第一個
4. 自動縮放並將該事件置中

#### ✏ 修改現有事件（圖片/名稱/描述/連結）
1. 點擊事件 → Popup 開啟
2. 點「✏ 編輯」
3. 修改任意欄位（圖片URL、中英文名稱、描述、Wikipedia連結）
4. 點「✓ 儲存修改」→ 立即生效
5. 點「⬇ 匯出 JSON」→ 下載 events.json
6. 覆蓋 `data/events.json` → 上傳 GitHub
> 💡 可以先修改多個事件，最後一次匯出，一個 JSON 包含所有修改

#### ✏ 修改事件的軸線 / CrossRef
1. 點擊事件 → Popup → ✏ 編輯
2. 「所在軸線」下拉：選擇要移動到的軸線
3. 「CrossRef」多選清單：按住 Ctrl/Cmd 可選最多3條軸線（縱線連接目標），不選任何項目 = 清除
4. 儲存修改 → 匯出 JSON → 覆蓋上傳

#### ➕ 新增單一事件（少量）
1. 用瀏覽器開啟 `tools/cosmic-tools.html`
2. 載入 `data/events.json`
3. 確認在「新增事件」分頁
4. 填寫表單 → 點「✓ 加入事件」
5. 點「📋 預覽變更並輸出」→ 確認後下載
6. 覆蓋 `data/events.json` → 執行 `python check.py` → 上傳 GitHub

---

### ─── 軸線 ───────────────────────────────────────

#### 🔧 修改軸線顯示門檻（zoomMin）
> 顯示門檻決定軸線在什麼縮放程度下出現：0 = 全局都看得到，0.58 = 要 zoom in 才出現

**方法A（推薦）：透過事件 Popup**
1. 點擊該軸線上任意一個事件
2. 點「✏ 編輯」
3. 「顯示門檻」滑桿拖動（正下方說明：0 = 全局，0.58 = zoom in才出現）
4. 儲存修改 → 立即生效 → 匯出 JSON → 覆蓋上傳

#### 🔧 修改軸線的父軸
1. 點擊該軸線上任意事件 → ✏ 編輯
2. 「父軸」下拉：選擇新的父軸
3. 儲存修改 → 匯出 JSON → 覆蓋上傳

#### 🔧 修改軸線起始年份 / 消亡年份
> 起始年份決定分支線從哪個時間點開始畫；有消亡年份的文明線會在那一年終止

1. 點擊該軸線上任意事件 → ✏ 編輯
2. 「軸線起始年份」：填入年份（負數 = BC）
3. 「消亡年份」：填入年份（空白 = 至今）
4. 儲存修改 → 匯出 JSON → 覆蓋上傳

#### ➕ 新增軸線
1. `cosmic-tools.html` → 載入 JSON → 切換到「新增軸線」分頁
2. 填寫：
   - **ID**：英文小寫 + 連字號，不能重複（例：`korea`）
   - **中文標籤**、**父軸**、**分類群組**、**顏色**
   - **顯示門檻**（0 = 全局，0.58 = zoom in才出現）
   - **起始年份**（必填）/ **消亡年份**（選填）
3. 點「✓ 加入軸線」→ 新軸線立即出現在事件的軸線選單
4. 繼續新增事件到這條軸線
5. 點「📋 預覽變更並輸出」→ 確認後下載
6. 覆蓋上傳 → `python check.py` 驗證

---

### ─── 圖片 ───────────────────────────────────────

#### 🖼 補上單一事件的圖片（手動）
1. 點擊事件 → Popup → ✏ 編輯
2. 「圖片 URL」貼上圖片網址
3. 儲存 → 匯出 JSON → 覆蓋上傳

#### 🖼 批量補圖（自動搜尋）
1. `cosmic-tools.html` → 載入 JSON → 切換到「🖼 圖片管理」
2. 點「列出缺圖事件」查看缺圖清單
3. 點「▶ 開始更新圖片」→ 自動從 Wikipedia / Wikidata / NASA 搜尋
   - 只找到一張 → 自動套用
   - 找到多張 → 暫停讓你手動選擇
4. 點「📋 預覽變更並輸出」→ 確認後下載 → 覆蓋上傳

#### 🔎 檢查失效圖片連結
1. `cosmic-tools.html` → 圖片管理 → 點「▶ 開始檢查」
2. 失效的可點「清除」移除
3. 點「📋 預覽變更並輸出」→ 確認後下載 → 覆蓋上傳

---

### ─── 顯示控制 ───────────────────────────────────

#### 👁 隱藏 / 顯示特定軸線
- 右側 Legend → **單擊**軸線名稱或群組：切換顯示/隱藏
- 右側 Legend → **雙擊**軸線名稱或群組：進入 Solo 模式（只顯示該項，其他淡化）
- Solo 狀態下**單擊**其他項目：加入顯示；再次單擊：移除
- Solo 狀態下**雙擊**任何項目：退出 Solo
- 右側頂部「全部顯示」按鈕：清除所有隱藏、Solo 與 Filter 狀態

#### 🎯 Events 視圖（主題快速切換）
- 點擊頂部「**Events**」按鈕 → 彈出分類選單
- 選單分四類：自然與宇宙 / 文明縱覽 / 主題 / 地區
- 點選任一項目：自動隱藏無關軸線，並 zoom 到對應時間範圍
- 取消：點右側「**全部顯示**」按鈕恢復

#### 🔍 Filter（事件層級篩選）
- 點擊頂部「**Filter**」按鈕 → 彈出 category 選單（戰爭/科學/宗教/文化等15個分類）
- 可多選：選中的 category 事件正常顯示，其他事件淡化至幾乎不可見
- 按鈕顯示目前選中數量（例：`Filter (2)`）
- 可與 Events 視圖同時使用（先選視圖縮小範圍，再 Filter 看特定類型）
- 取消：點 popup 內「清除篩選」或點「**全部顯示**」按鈕

#### 🌐 中英文切換
- 右上角「中 / EN」按鈕
- 設定記憶在瀏覽器

---

### ─── 驗證與上傳 ──────────────────────────────────

#### ✅ 驗證 events.json

在專案資料夾開啟 PowerShell（Shift + 右鍵 → 在這裡開啟 PowerShell）：

```powershell
python check.py
```

#### ⬆ 上傳到 GitHub
修改後的檔案放回對應位置後 commit + push：
- `data/events.json` → 主要資料
- `index.html` → UI 更新
- `tools/cosmic-tools.html` → 工具更新

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

---

## events.json 完整結構

```
events.json
├── meta              # 專案基本資訊
├── axis_groups       # 軸線群組定義（7 組：label/label_en/color）
├── axes              # 軸線定義（47 條）
├── era_bands         # Canvas 背景時代色帶（11 段）
├── era_buttons       # 底部導航按鈕（12 個）
├── filter_cats       # 篩選分類（15 類）
├── views             # 主題視圖（24 個）
└── events            # 歷史事件（561+ 個）
```

> 所有 UI 資料（群組、時代色帶、導航按鈕、篩選分類）都從 JSON 動態載入，index.html 不寫死任何資料。

---

## events.json 欄位說明

### axes（軸線）

| 欄位 | 必填 | 說明 |
|------|------|------|
| `id` | ✓ | 唯一識別碼（英文小寫 + 連字號） |
| `label` | ✓ | 中文顯示名稱 |
| `label_en` | ✓ | 英文顯示名稱 |
| `color` | ✓ | 顏色 hex |
| `order` | ✓ | 排列順序 |
| `parent` | | 父軸 id（null = 頂層） |
| `startYear` | ✓ | 分支線起始年份 |
| `endYear` | | 消亡年份（null = 至今） |
| `zoomMin` | ✓ | 顯示門檻（0 = 全局，0.58 = zoom in才出現） |
| `group` | ✓ | natural / global / region / civilization / religion / human / nation |

### events（事件）

| 欄位 | 必填 | 說明 |
|------|------|------|
| `id` | ✓ | 唯一識別碼 |
| `year` | ✓ | 年份（負數 = BC） |
| `zh` | ✓ | 中文名稱 |
| `en` | | 英文名稱 |
| `axis` | ✓ | 所在軸線 id |
| `level` | ✓ | 重要程度（1=大 2=中 3=小） |
| `endYear` | | 結束年份（有填 = pill，沒填 = 點） |
| `crossRef` | | 縱線連接目標軸線 id，支援單一字串或陣列（最多3條），例：`"cross"` 或 `["mideast","islam","cross"]` |
| `image` | | 圖片 URL |
| `desc_zh` | | 中文描述 |
| `desc_en` | | 英文描述 |
| `wiki_zh` | | 中文 Wikipedia URL |
| `wiki_en` | | 英文 Wikipedia URL |
| `category` | | civilization / politics / war / science / religion / culture / ... |

---

## 軸線分類群組

群組定義的設計原則：**演化順序**（自然 → 世界 → 地區 → 文明 → 宗教 → 人文 → 國家），父子關係反映「某地區先有文明，文明之後才有國家」的邏輯層次。

| 群組 | 定義 | 包含軸線 | 未來擴充 |
|------|------|---------|---------|
| natural 自然 | 宇宙誕生至人類出現，純自然演化過程 | cosmos, galaxy, solar-system, earth, climate, life, human-evo, migration | 無 |
| global 世界 | 與人類行為直接相關、跨越多地區影響全人類，不屬於單一地區或文明 | cross, trade | 可擴充全球性主題軸 |
| region 地區 | 人類活動的地理容器，早於文明與國家存在 | east, west, africa, americas, central-asia, southeast-asia, oceania, arctic, antarctic | 可加中亞細分等 |
| civilization 文明 | 各地理區域內發展的文明，部分延續至今，早於近代國家 | mideast, mesopotamia, egypt, persia, india, china, greece, latin-america | 撒哈拉以南、東南亞文明等 |
| religion 宗教 | 各宗教體系的起源與發展 | judaism, christianity, islam, hinduism, buddhism, taoism | 未來可加其他宗教 |
| human 人文 | 跨越地區與文明的人類文化活動 | science, arts | 未來可擴充 |
| nation 國家 | 近代以後有明確政治實體的重要國家或地區 | iran, north/west/east/south-africa, china-b, taiwan, japan, europe, north-america, south-america, usa | 重要國家陸續補充 |

### 群組設計說明

- **自然 vs 世界**：自然事件與人類行為無關（宇宙大爆炸、生命演化）；世界事件由人類行為觸發但影響跨越地區（世界大戰、黑死病、蒙古帝國）
- **地區 vs 文明**：地區是地理容器（東方、西方），文明是在該地理區域內發展的具體文明（中國、希臘羅馬）；地區的 zoomMin = 0.30，與文明同步出現
- **文明 vs 國家**：文明早於國家存在，部分文明延續至今；國家是近代政治實體，為文明的子軸
- **科學技術與藝術文化**歸入人文群組，不單獨成群組，因為 legend 群組與軸線名稱重複

---

## 開發記錄

| 日期 | 內容 |
|------|------|
| 2026-04-09 | 專案建立，Canvas 時間軸基礎 |
| 2026-04-10 | 動態軸線系統、事件資料架構 |
| 2026-04-11 | 非洲、美洲、科技、波斯、古埃及、銀河系軸線 |
| 2026-04-11 | Legend 群組折疊 + 群組 Solo 模式 |
| 2026-04-11 | 中英文切換、Popup 編輯完整功能 |
| 2026-04-11 | cosmic-tools.html 工具箱（新增/圖片/確認輸出）|
| 2026-04-11 | 兩河流域、宇宙、中東戰火、青銅鐵器 大批事件 |
| 2026-04-12 | UI 改版：比例尺移至 header、Legend 寬度優化、Solo 邏輯統一 |
| 2026-04-12 | 群組架構重整：7個 group（natural/global/region/civilization/religion/human/nation） |
| 2026-04-12 | east/west label 改為東方/西方，zoomMin 改為 0.30，文明軸線全部 0.30 |
| 2026-04-12 | 新增軸線：climate, migration, oceania, central-asia, southeast-asia, trade, arctic, antarctic |
| 2026-04-12 | 大批事件補充：india, egypt, africa, americas, latin-america, cross, east, west, migration, 自然群組 |
| 2026-04-12 | Events 視圖選單：header 按鈕 → popup 分類選單，點選後自動 hide/show + zoom 到對應時間範圍 |
| 2026-04-12 | cosmic-tools.html 新增「視圖管理」分頁：新增/修改/刪除 view，axes 多選，ID 自動產生 |
| 2026-04-12 | Filter 功能：header 按鈕 → category 多選篩選，選中類別事件亮起其他淡化，可與 Events 同時使用 |
| 2026-04-12 | crossRef 多軸支援：最多3條，陣列格式向下相容舊字串，縱線/hit test/popup 全部更新 |
| 2026-04-12 | crossRef 批量更新：ISIS移至mideast軸、波灣戰爭/十字軍/911等14個事件補充多軸crossRef |
| 2026-04-12 | 冰河期5次補 endYear 變 pill，Events 選單加「五次大冰河期」視圖 |
| 2026-04-12 | crossRef 縱線跑位 bug 修正：目標軸線不在 yMap 時不畫縱線 |
| 2026-04-12 | 軸線 startYear 修正：science/east/europe/americas/latin-america |
| 2026-04-13 | 資料集中化：ERA_BANDS/FILTER_CATS/AXIS_GROUP_DEFS/era_buttons 全部移到 JSON |
| 2026-04-13 | buildAxes() 加入 label_en 讀取、刪除 Fallback 寫死資料、刪除重複函數 |
| 2026-04-13 | 完整英文化：UI/Popup/Tooltip/Search/Legend/Era/Filter 全部支援 T() 中英切換 |
| 2026-04-13 | Solo 模式 click/dblclick 跑位修正（延遲 click 避免衝突） |
| 2026-04-13 | check.py 擴充：驗證 axis_groups/era_bands/era_buttons/filter_cats + 內容缺失摘要 |
| 2026-04-13 | 新增 add-events-sample.py 腳本樣板 |
