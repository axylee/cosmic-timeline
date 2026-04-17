"""
═══════════════════════════════════════════════════════
  Cosmic Timeline — 自動補圖腳本（本機執行）

  補 cosmic-tools.html 做不到的事：
    - 本機 Python 沒有瀏覽器 CORS 限制
    - 可以直接抓 Wikipedia 頁面 HTML 解析 infobox 圖片
    - 這能救回 pageimages API 找不到圖的情境

  使用方式（在 repo 根目錄或 tools/ 底下執行皆可）：
    python tools/find-missing-images.py              # 只補缺圖事件（image 為空）
    python tools/find-missing-images.py --overwrite  # 重新抓所有事件圖片

  輸出（全部放在 tools/）：
    1. tools/events.json                     更新後的資料（不會動 data/events.json）
    2. tools/pending-picks-YYYYMMDDHHMM.json 多候選清單（給 Claude 挑）

  驗收流程：
    1. 跑腳本 → 看 log
    2. 檢查 tools/events.json 變動
    3. 確認無誤 → 手動將 tools/events.json 覆蓋到 data/events.json
    4. python check.py 驗證
    5. 有 pending-picks → 上傳給 Claude 挑圖
═══════════════════════════════════════════════════════
"""
import argparse
import json
import os
import re
import sys
import time
from datetime import datetime
from urllib.parse import quote, unquote

try:
    import requests
except ImportError:
    print("✗ 缺少 requests 套件，請先執行：pip install requests")
    sys.exit(1)


# ════════════════════════════════════════════
# 設定
# ════════════════════════════════════════════
USER_AGENT = "CosmicTimeline-ImageFinder/1.0 (https://cosmichistorytimeline.com)"
REQUEST_TIMEOUT = 10
DELAY_BETWEEN_EVENTS = 0.2


# ════════════════════════════════════════════
# HTTP helpers
# ════════════════════════════════════════════
session = requests.Session()
session.headers.update({"User-Agent": USER_AGENT})


def http_get_json(url, params=None):
    try:
        r = session.get(url, params=params, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


def http_get_text(url, params=None):
    try:
        r = session.get(url, params=params, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        return r.text
    except Exception:
        return None


# ════════════════════════════════════════════
# Wiki URL 處理
# ════════════════════════════════════════════
def parse_wiki_url(url):
    if not url or "wikipedia.org/wiki/" not in url:
        return None
    try:
        host = url.split("//")[1].split(".wikipedia")[0]
        title = unquote(url.split("/wiki/")[1].split("#")[0])
        return {"lang": host, "title": title}
    except Exception:
        return None


def sanitize_image_url(url):
    """縮圖 URL 升級到 1200px（跟 cosmic-tools.html 一致）"""
    if not url:
        return url
    if ".svg/" in url and url.endswith(".svg.png"):
        return re.sub(r"/\d+px-", "/1200px-", url)
    if "/thumb/" in url:
        m = re.search(r"/(\d+)px-", url)
        if m and int(m.group(1)) < 640:
            return re.sub(r"/\d+px-", "/1200px-", url)
    return url


# ════════════════════════════════════════════
# 來源 1: Wikipedia pageimages API
# ════════════════════════════════════════════
def fetch_pageimage(wiki_url):
    w = parse_wiki_url(wiki_url)
    if not w:
        return None
    d = http_get_json(
        f"https://{w['lang']}.wikipedia.org/w/api.php",
        params={
            "action": "query", "titles": w["title"],
            "prop": "pageimages", "piprop": "original|thumbnail",
            "pithumbsize": "1200",
            "format": "json", "redirects": "1", "origin": "*",
        },
    )
    if not d:
        return None
    for pg in (d.get("query", {}).get("pages") or {}).values():
        if pg.get("pageid") == -1:
            continue
        url = (pg.get("original") or {}).get("source") \
              or (pg.get("thumbnail") or {}).get("source")
        if url:
            return {
                "url": sanitize_image_url(url),
                "label": f"Wiki主圖({w['lang']})",
                "source": f"Wiki-PageImage({w['lang']})",
            }
    return None


# ════════════════════════════════════════════
# 來源 2: Wikidata P18
# ════════════════════════════════════════════
def fetch_wikidata(wiki_url):
    w = parse_wiki_url(wiki_url)
    if not w:
        return None
    site = "zhwiki" if w["lang"] == "zh" else "enwiki"
    d = http_get_json(
        "https://www.wikidata.org/w/api.php",
        params={
            "action": "wbgetentities", "sites": site, "titles": w["title"],
            "props": "claims", "format": "json", "origin": "*",
        },
    )
    if not d:
        return None
    for ent in (d.get("entities") or {}).values():
        p18_list = (ent.get("claims") or {}).get("P18") or []
        if not p18_list:
            continue
        filename = (((p18_list[0] or {}).get("mainsnak") or {})
                    .get("datavalue") or {}).get("value")
        if not filename:
            continue
        url = _resolve_commons_file(filename)
        if url:
            return {"url": url, "label": "Wikidata P18", "source": "Wikidata"}
    return None


def _resolve_commons_file(filename):
    """把 Commons File:xxx.jpg 解析成真實 URL"""
    d = http_get_json(
        "https://commons.wikimedia.org/w/api.php",
        params={
            "action": "query", "titles": f"File:{filename}",
            "prop": "imageinfo", "iiprop": "url|mime", "iiurlwidth": "1200",
            "format": "json", "origin": "*",
        },
    )
    if not d:
        return None
    for pg in (d.get("query", {}).get("pages") or {}).values():
        ii_list = pg.get("imageinfo") or []
        if not ii_list:
            continue
        ii = ii_list[0]
        mime = ii.get("mime", "")
        if not mime.startswith("image/") or "svg" in mime:
            continue
        url = ii.get("thumburl") or ii.get("url")
        if url:
            return sanitize_image_url(url)
    return None


# ════════════════════════════════════════════
# 來源 3: 解析 Wikipedia 頁面 HTML（本機才能做）
# ════════════════════════════════════════════
# 抓 infobox 裡的 <img src="//upload.wikimedia.org/...">
INFOBOX_RE = re.compile(
    r'<table[^>]*class="[^"]*infobox[^"]*"[^>]*>(.*?)</table>',
    re.DOTALL | re.IGNORECASE,
)
IMG_SRC_RE = re.compile(
    r'<img[^>]+src="(//upload\.wikimedia\.org/wikipedia/commons/[^"]+?\.(?:jpg|jpeg|png|webp))"',
    re.IGNORECASE,
)


def fetch_html_infobox(wiki_url):
    w = parse_wiki_url(wiki_url)
    if not w:
        return None
    # 用渲染後的頁面 HTML（包含完整 infobox）
    html = http_get_text(
        f"https://{w['lang']}.wikipedia.org/wiki/{quote(w['title'], safe='')}"
    )
    if not html:
        return None

    # 先找 infobox
    infobox_match = INFOBOX_RE.search(html)
    search_area = infobox_match.group(1) if infobox_match else html[: len(html) // 3]

    m = IMG_SRC_RE.search(search_area)
    if not m:
        # infobox 裡沒有 → 看整頁前 1/3（避免拿到導航圖示/頁尾）
        if infobox_match:
            m = IMG_SRC_RE.search(html[: len(html) // 3])
        if not m:
            return None

    raw_url = m.group(1)
    if raw_url.startswith("//"):
        raw_url = "https:" + raw_url
    return {
        "url": sanitize_image_url(raw_url),
        "label": f"Wiki頁面解析({w['lang']})",
        "source": f"Wiki-Infobox({w['lang']})",
    }


# ════════════════════════════════════════════
# 來源 4: Commons search（關鍵字搜尋）
# ════════════════════════════════════════════
def fetch_commons_search(query, limit=3):
    if not query:
        return []
    d = http_get_json(
        "https://commons.wikimedia.org/w/api.php",
        params={
            "action": "query", "generator": "search", "gsrsearch": query,
            "gsrnamespace": "6", "gsrlimit": str(limit),
            "prop": "imageinfo", "iiprop": "url|mime", "iiurlwidth": "1200",
            "format": "json", "origin": "*",
        },
    )
    if not d:
        return []
    results = []
    for pg in (d.get("query", {}).get("pages") or {}).values():
        ii_list = pg.get("imageinfo") or []
        if not ii_list:
            continue
        ii = ii_list[0]
        mime = ii.get("mime", "")
        if not mime.startswith("image/") or "svg" in mime:
            continue
        url = ii.get("thumburl") or ii.get("url")
        if not url:
            continue
        title = (pg.get("title") or "").replace("File:", "").replace("_", " ")
        results.append({
            "url": sanitize_image_url(url),
            "label": title[:40],
            "source": "Commons",
        })
    return results


# ════════════════════════════════════════════
# 彙整所有候選（跟 cosmic-tools.html 邏輯一致）
# ════════════════════════════════════════════
def fetch_all_candidates(ev, zh_first=True):
    candidates = []
    seen = set()

    def add(c):
        if c and c.get("url") and c["url"] not in seen:
            seen.add(c["url"])
            candidates.append(c)

    wiki_urls = []
    if zh_first:
        if ev.get("wiki_zh"):
            wiki_urls.append(ev["wiki_zh"])
        if ev.get("wiki_en"):
            wiki_urls.append(ev["wiki_en"])
    else:
        if ev.get("wiki_en"):
            wiki_urls.append(ev["wiki_en"])
        if ev.get("wiki_zh"):
            wiki_urls.append(ev["wiki_zh"])

    # 1. pageimages API（每個 wiki 連結試一次）
    for u in wiki_urls:
        add(fetch_pageimage(u))

    # 2. Wikidata P18
    for u in wiki_urls:
        add(fetch_wikidata(u))
        break   # Wikidata 每事件只試一次即可（同個條目兩語言結果一樣）

    # 3. 直接解析 Wiki HTML infobox（本機獨家）
    for u in wiki_urls:
        add(fetch_html_infobox(u))

    # 4. Commons 關鍵字搜尋
    if ev.get("en"):
        for c in fetch_commons_search(ev["en"], 3):
            add(c)
    elif ev.get("zh"):
        for c in fetch_commons_search(ev["zh"], 3):
            add(c)

    return candidates


# ════════════════════════════════════════════
# 主流程
# ════════════════════════════════════════════
def find_events_json():
    """從 tools/ 或 repo 根目錄執行時都能找到 ../data/events.json 或 ./data/events.json"""
    here = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(here, "..", "data", "events.json"),   # 從 tools/ 執行
        os.path.join(os.getcwd(), "data", "events.json"),  # 從 repo 根執行
        os.path.join(here, "data", "events.json"),
    ]
    for p in candidates:
        if os.path.exists(p):
            return os.path.abspath(p)
    return None


def main():
    parser = argparse.ArgumentParser(description="Cosmic Timeline 自動補圖腳本")
    parser.add_argument("--overwrite", action="store_true",
                        help="覆蓋所有事件圖片（預設只處理 image 為空的事件）")
    parser.add_argument("--events", default=None,
                        help="手動指定 events.json 路徑（預設自動尋找）")
    parser.add_argument("--zh-first", action="store_true", default=True,
                        help="優先中文 Wikipedia（預設開啟）")
    args = parser.parse_args()

    # 1. 讀 events.json
    events_path = args.events or find_events_json()
    if not events_path or not os.path.exists(events_path):
        print("✗ 找不到 events.json，請確認執行位置或用 --events 指定路徑")
        sys.exit(1)
    print(f"📂 讀取: {events_path}")
    with open(events_path, encoding="utf-8") as f:
        data = json.load(f)

    events = data.get("events", [])
    print(f"   共 {len(events)} 個事件")

    # 2. 篩選目標
    if args.overwrite:
        targets = events
        print(f"   模式: 覆蓋所有圖片（--overwrite）")
    else:
        targets = [e for e in events if not e.get("image")]
        print(f"   模式: 只補缺圖（{len(targets)} 個）")

    if not targets:
        print("\n✓ 沒有需要處理的事件，結束")
        return

    print()

    # 3. 逐個事件處理
    tools_dir = os.path.dirname(os.path.abspath(__file__))
    stat_auto = 0
    stat_pending = 0
    stat_fail = 0
    failed_list = []
    pending_picks = []

    for i, ev in enumerate(targets, 1):
        zh = ev.get("zh", "?")
        prefix = f"[{i}/{len(targets)}]"

        # 跳過沒有任何可搜尋資訊的
        if not (ev.get("wiki_zh") or ev.get("wiki_en")
                or ev.get("en") or ev.get("zh")):
            print(f"{prefix} ⊘ {zh}（無可搜尋資訊）")
            stat_fail += 1
            failed_list.append((ev["id"], zh, "no search info"))
            continue

        candidates = fetch_all_candidates(ev, zh_first=args.zh_first)

        if not candidates:
            print(f"{prefix} ✗ {zh}（找不到圖片）")
            stat_fail += 1
            failed_list.append((ev["id"], zh, "no candidates"))
        elif len(candidates) == 1:
            ev["image"] = candidates[0]["url"]
            print(f"{prefix} ✓ {zh}  [自動·{candidates[0]['source']}]")
            stat_auto += 1
        else:
            # 多候選 → 進 pending-picks
            pending_picks.append({
                "id": ev["id"],
                "zh": ev.get("zh", ""),
                "en": ev.get("en", ""),
                "year": ev.get("year"),
                "axis": ev.get("axis", ""),
                "category": ev.get("category", ""),
                "desc_zh": ev.get("desc_zh", ""),
                "desc_en": ev.get("desc_en", ""),
                "wiki_zh": ev.get("wiki_zh", ""),
                "wiki_en": ev.get("wiki_en", ""),
                "current_image": ev.get("image") or None,
                "candidates": candidates,
            })
            print(f"{prefix} 📦 {zh}（待挑·{len(candidates)} 張）")
            stat_pending += 1

        time.sleep(DELAY_BETWEEN_EVENTS)

    # 4. 輸出 tools/events.json
    out_events = os.path.join(tools_dir, "events.json")
    # 保持 key 順序（跟 events.json sample 一致）
    ordered = {}
    key_order = ["meta", "axis_groups", "axes", "era_bands", "era_buttons",
                 "filter_cats", "views", "view_groups", "events"]
    for k in key_order:
        if k in data:
            ordered[k] = data[k]
    for k in data:
        if k not in ordered:
            ordered[k] = data[k]

    with open(out_events, "w", encoding="utf-8") as f:
        json.dump(ordered, f, ensure_ascii=False, indent=2)

    # 5. 輸出 pending-picks（若有）
    out_pending = None
    if pending_picks:
        ts = datetime.now().strftime("%Y%m%d%H%M")
        out_pending = os.path.join(tools_dir, f"pending-picks-{ts}.json")
        payload = {
            "meta": {
                "exported_at": datetime.now().isoformat(),
                "count": len(pending_picks),
                "source": "find-missing-images.py",
                "note": "請 Claude 根據 candidates 挑選最適合的圖，輸出 add-events-YYYYMMDDHHMM.py",
            },
            "items": pending_picks,
        }
        with open(out_pending, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

    # 6. 總結
    print()
    print("═" * 50)
    print(f"  自動套用 : {stat_auto}")
    print(f"  待挑     : {stat_pending}")
    print(f"  失敗     : {stat_fail}")
    print("═" * 50)

    print(f"\n📄 輸出: {out_events}")
    if out_pending:
        print(f"📄 輸出: {out_pending}")

    if failed_list:
        print(f"\n─── 失敗清單（{len(failed_list)} 個）───")
        for eid, zh, reason in failed_list:
            print(f"  {zh} ({eid}) — {reason}")

    print("\n─── 下一步 ───")
    print("  1. 檢視 tools/events.json 的變動")
    print("  2. 確認無誤 → 手動覆蓋到 data/events.json")
    print("  3. python check.py 驗證")
    if out_pending:
        print(f"  4. 上傳 {os.path.basename(out_pending)} 給 Claude 挑圖")


if __name__ == "__main__":
    main()
