# 宇宙歷史時間軸 · Cosmic Timeline

## 使用方式
- 滾輪：縮放（以滑鼠位置為中心）
- 拖曳：左右平移
- 點擊事件點：開啟詳細 Popup
- 點擊圖例：切換軸線顯示/隱藏

## 檔案結構
```
cosmic-timeline/
├── index.html          ← 主程式
├── data/
│   └── events.json     ← 事件資料（可自行增減）
├── images/             ← 本地圖片（可選，JSON 預設使用 Wikimedia URL）
│   ├── cosmos/
│   ├── life/
│   ├── human-evo/
│   ├── cross/
│   └── civilization/
│       ├── east/
│       └── west/
└── README.md
```

## 更新資料
只需修改 `data/events.json` 並上傳覆蓋即可。

## GitHub Pages 部署
repo → Settings → Pages → Source: main branch → 儲存
