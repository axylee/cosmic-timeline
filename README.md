# 🌌 Cosmic Timeline · 宇宙歷史時間軸

一個互動式時間軸，從宇宙誕生（138億年前）到今日，涵蓋自然史、人類演化、文明發展、科學技術、宗教藝術等多條並列軸線。

**線上版本：** https://axylee.github.io/cosmic-timeline/

---

## 檔案結構

```
cosmic-timeline/
├── index.html              # 主程式（時間軸 UI）
├── data/
│   └── events.json         # 所有事件、軸線、時代資料
├── tools/
│   ├── add-events.html     # 新增事件 / 軸線工具
│   └── update-images.html  # 圖片搜尋與更新工具
├── check.py                # 驗證 events.json 的 Python 腳本
└── README.md
```

---

## 作業流程

### A. 新增事件或軸線（推薦方式）

1. 用瀏覽器開啟 `tools/add-events.html`
2. 載入 `data/events.json`（拖曳或從 GitHub URL 載入）
3. 切換到「新增軸線」或「新增事件」分頁
4. 填寫表單 → 點「加入」
5. 重複加入多個項目
6. 點「下載 events.json」
7. 覆蓋 `data/events.json`
8. 執行 `python check.py` 驗證
9. 上傳 GitHub

### B. 直接修改 events.json

適合批量修改或結構調整。

1. 用文字編輯器開啟 `data/events.json`
2. 修改 `axes` 或 `events` 陣列
3. 執行 `python check.py` 驗證
4. 上傳 GitHub

### C. 在 UI 裡編輯現有事件

1. 開啟網站
2. 點擊任一事件 → popup 開啟
3. 點「✏ 編輯」
4. 修改：所在軸線、顯示門檻、CrossRef、父軸、圖片、名稱、描述、Wikipedia 連結
5. 點「✓ 儲存修改」→ 立即生效
6. 點「⬇ 匯出 JSON」→ 下載 `events.json`
7. 覆蓋 `data/events.json` → 上傳 GitHub

### D. 更新圖片

1. 用瀏覽器開啟 `tools/update-images.html`
2. 載入 `data/events.json`
3. 搜尋缺圖事件 → 選擇圖片
4. 點「下載 events.json」
5. 覆蓋 `data/events.json` → 上傳 GitHub

---

## Python 環境

```bash
cd C:\Users\aytle\OneDrive\蓁\20260409-cosmic-timeline
python check.py
```

輸出範例：
```
=============================================
  事件總數   : 375
  有圖片     : 338
  缺圖片     : 37
  有 crossRef: 90
  定義軸線數 : 36
=============================================
✓ 所有事件軸線正確
✓ 無重複 ID
```

---

## events.json 結構

### axes 欄位

| 欄位 | 說明 |
|------|------|
| `id` | 唯一識別碼（英文小寫 + 連字號） |
| `label` | 顯示名稱 |
| `color` | 顏色（hex） |
| `order` | 排列順序 |
| `parent` | 父軸 id（null = 頂層） |
| `startYear` | 起始年份 |
| `endYear` | 結束年份（null = 至今） |
| `zoomMin` | 顯示門檻（0 = 全局，0.58 = zoom in 才出現） |
| `group` | 分類群組 |

### events 欄位

| 欄位 | 必填 | 說明 |
|------|------|------|
| `id` | ✓ | 唯一識別碼 |
| `year` | ✓ | 年份（負數 = BC） |
| `zh` | ✓ | 中文名稱 |
| `en` | | 英文名稱 |
| `axis` | ✓ | 所在軸線 id |
| `level` | ✓ | 重要程度（1=大 2=中 3=小） |
| `endYear` | | 結束年份（有填 = pill，沒填 = 點） |
| `crossRef` | | 縱線連接軸線 id |
| `image` | | 圖片 URL |
| `desc_zh` | | 中文描述 |
| `desc_en` | | 英文描述 |
| `wiki_zh` | | 中文 Wikipedia URL |
| `wiki_en` | | 英文 Wikipedia URL |

---

## UI 操作

| 操作 | 說明 |
|------|------|
| 滑鼠滾輪 | 水平縮放 |
| 拖曳 | 水平平移 |
| 右側滑桿 | 垂直縮放 |
| 單擊 Legend | 顯示 / 隱藏軸線 |
| 雙擊 Legend | Solo 模式 |
| Solo 時單擊 | 加入比較 |
| 右上角 中/EN | 語言切換 |

---

## 開發記錄

| 日期 | 內容 |
|------|------|
| 2026-04-09 | 專案建立，基礎時間軸 |
| 2026-04-10 | 動態軸線系統、事件資料 |
| 2026-04-11 | 非洲、美洲、科技、波斯、古埃及軸線 |
| 2026-04-11 | Legend 右側化、Solo 模式、中英文切換 |
| 2026-04-11 | Popup 編輯支援 crossRef / 父軸 / zoomMin |
| 2026-04-11 | add-events.html 工具 |
