# 宇宙歷史時間軸 · Cosmic Timeline

🌐 **線上版本**：https://axylee.github.io/cosmic-timeline/

## 使用方式
- **滾輪**：縮放（以滑鼠位置為中心）
- **拖曳**：上下左右平移
- **點擊 pill 左側**：展開子事件
- **點擊 pill 右側 ℹ**：開啟詳細 Popup
- **點擊圖例**：切換軸線顯示/隱藏
- **底部快跳按鈕**：跳到特定時代

## 維護工具

### 圖片批量更新工具
`tools/update-images.html` — 在瀏覽器直接開啟，自動從 Wikipedia API 抓取所有事件的圖片 URL，下載更新後的 events.json。

使用流程：
1. 開啟 `tools/update-images.html`
2. 點「從 URL 載入」載入最新 events.json
3. 點「▶ 開始更新圖片」
4. 下載更新後的 JSON → 上傳到 `data/events.json`

## 檔案結構
```
cosmic-timeline/
├── index.html              ← 主程式
├── data/
│   └── events.json         ← 事件資料（可自行增減）
├── tools/
│   └── update-images.html  ← 圖片批量更新工具
├── images/                 ← 本地圖片（可選）
└── README.md
```

## 新增事件
在 `data/events.json` 新增一筆，只需設定：
```json
{
  "id": "唯一識別碼",
  "year": -221,
  "zh": "秦朝統一",
  "en": "Qin Unification",
  "axis": "china",
  "level": 1,
  "desc_zh": "中文描述",
  "desc_en": "English description",
  "wiki_zh": "https://zh.wikipedia.org/wiki/秦朝",
  "wiki_en": "https://en.wikipedia.org/wiki/Qin_dynasty"
}
```
`image` 欄位不用手動填，用圖片更新工具自動從 Wikipedia 抓取即可。

如有 `endYear` 欄位，事件會顯示為時期 pill（可展開）；否則顯示為圓點。  
子事件只需時間範圍**嚴格落在父事件內**，系統自動建立父子關係。

## GitHub Pages 部署
repo → Settings → Pages → Source: main branch → 儲存
