# 🌌 Cosmic History Timeline · 宇宙歷史時間軸

An interactive timeline spanning 13.8 billion years — from the Big Bang to the present day.

**🔗 Live:** [cosmichistorytimeline.com](https://cosmichistorytimeline.com)
**✏️ Editor:** [cosmichistorytimeline.com/indexedit.html](https://cosmichistorytimeline.com/indexedit.html)

---

## Overview

| | |
|---|---|
| Events | 802 |
| Axes | 59 |
| Groups | 6 (Natural · Global · Region · Civilization · Religion · Nation) |
| Languages | 中文 / English |
| Book links | 30 events with Amazon affiliate links |

---

## File Structure

```
cosmic-timeline/
├── index.html              # Public version (no edit UI)
├── indexedit.html           # Editor version (with edit panel)
├── about.html              # About / Contact / Privacy / Copyright
├── data/
│   └── events.json         # All events, axes, eras, views
├── tools/
│   └── cosmic-tools.html   # Image management & event tools
├── images/                 # Event images + og-preview.png + kofi_symbol.svg
├── check.py                # Python validation script
├── add-events-*.py         # Event/data update scripts
├── ads.txt                 # Google AdSense authorization
├── sitemap.xml             # SEO sitemap
├── robots.txt              # SEO crawler rules
├── netlify.toml            # Netlify deploy config (blocks dev files)
└── README.md
```

---

## Workflow

### Adding Events

```bash
# 1. Write a Python script (add-events-YYYYMMDDHHmm.py)
# 2. Run it
python add-events-202604151925.py

# 3. Validate
python check.py

# 4. Push to GitHub → Netlify auto-deploys
```

### Editing Events in Browser

Open `indexedit.html` → click any event → ✏ Edit → modify fields → Export JSON

### Image Management

Open `tools/cosmic-tools.html` → load events.json → search/update images → download

---

## Monetization

| Channel | Status |
|---------|--------|
| Google AdSense | Pending review |
| Amazon Associates | Active (ID: cosmictimelin-20) |
| 博客來 AP | Pending review |
| Ko-fi | [ko-fi.com/universetimeline](https://ko-fi.com/universetimeline) |

---

## SEO

- `<meta>` description + canonical URL
- Open Graph + Twitter Card tags
- JSON-LD structured data (WebApplication / Education)
- `sitemap.xml` + `robots.txt`

---

## Deployment

- **Hosting:** Netlify (auto-deploy from GitHub)
- **Domain:** [cosmichistorytimeline.com](https://cosmichistorytimeline.com)
- **SSL:** Let's Encrypt (auto-renewed)
- **Dev files blocked:** `netlify.toml` returns 404 for check.py, tools/, README.md, etc.

---

## Dev Log

| Date | Changes |
|------|---------|
| 2026-04-09 | Project created, Canvas timeline base |
| 2026-04-10 | Dynamic axis system, event data, zoom/pan |
| 2026-04-11 | Legend, Solo mode, language toggle, search, popup editor |
| 2026-04-12 | Image tools, crossRef, era bands, 36 axes |
| 2026-04-13 | JSON centralization, full English localization, 57 new events |
| 2026-04-13 | cosmic-tools.html (merged add-events + update-images) |
| 2026-04-14 | Color system unification, geological time hierarchy, __NOW__ endYear |
| 2026-04-14 | 90 new events (cosmos/galaxy/solar-system/science), 802 total |
| 2026-04-15 | Ko-fi, AdSense, about.html, SEO, Netlify deployment |
| 2026-04-15 | Amazon Associates, 30 book affiliate links, popup affiliate UI |
| 2026-04-15 | Public/editor split (index.html / indexedit.html) |
