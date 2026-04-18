"""
═══════════════════════════════════════════════════════
  Cosmic Timeline — 自動補圖腳本（本機執行）

  補 cosmic-tools.html 做不到的事：
    - 本機 Python 沒有瀏覽器 CORS 限制
    - 可以直接抓 Wikipedia 頁面 HTML 解析 infobox 圖片
    - 這能救回 pageimages API 找不到圖的情境

  使用方式（在 repo 根目錄或 tools/ 底下執行皆可）：
    python tools/images-find-missing.py              # 只補缺圖事件（image 為空）
    python tools/images-find-missing.py --overwrite  # 重新抓所有事件圖片

  產出（都放在 tools/）：
    tools/add-events-YYYYMMDDHHmm-fill-images.py
      ← 可執行的 .py，執行後會更新 data/events.json
      ← 每個成功找到替代圖的事件都會列出來
      ← 多候選事件不會進此檔案（留空白由使用者在 tools.html 手動挑）

  驗收流程：
    1. python tools/images-find-missing.py
    2. 看產出的 add-events-*.py 確認變動
    3. 滿意就執行：
       copy tools\add-events-YYYYMMDDHHmm-fill-images.py .
       python add-events-YYYYMMDDHHmm-fill-images.py
       python check.py
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

# Wikimedia 標準縮圖尺寸（2026/01 起非標準尺寸會 HTTP 429）
# 參考 https://w.wiki/GHai
STANDARD_THUMB_SIZE = 1280  # 接近 1200 的標準尺寸


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
    """縮圖 URL 升級到標準尺寸 1280px（跟 cosmic-tools.html 一致）"""
    if not url:
        return url
    if ".svg/" in url and url.endswith(".svg.png"):
        return re.sub(r"/\d+px-", f"/{STANDARD_THUMB_SIZE}px-", url)
    if "/thumb/" in url:
        m = re.search(r"/(\d+)px-", url)
        if m and int(m.group(1)) < 640:
            return re.sub(r"/\d+px-", f"/{STANDARD_THUMB_SIZE}px-", url)
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
            "pithumbsize": str(STANDARD_THUMB_SIZE),
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
            "prop": "imageinfo", "iiprop": "url|mime",
            "iiurlwidth": str(STANDARD_THUMB_SIZE),
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
    html = http_get_text(
        f"https://{w['lang']}.wikipedia.org/wiki/{quote(w['title'], safe='')}"
    )
    if not html:
        return None

    infobox_match = INFOBOX_RE.search(html)
    search_area = infobox_match.group(1) if infobox_match else html[: len(html) // 3]

    m = IMG_SRC_RE.search(search_area)
    if not m:
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
            "prop": "imageinfo", "iiprop": "url|mime",
            "iiurlwidth": str(STANDARD_THUMB_SIZE),
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
# 彙整所有候選
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

    # 1. pageimages API
    for u in wiki_urls:
        add(fetch_pageimage(u))

    # 2. Wikidata P18
    for u in wiki_urls:
        add(fetch_wikidata(u))
        break

    # 3. Wiki HTML infobox
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
# 路徑工具
# ════════════════════════════════════════════
def find_events_json():
    """從 tools/ 或 repo 根目錄執行時都能找到 events.json"""
    here = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(here, "..", "data", "events.json"),
        os.path.join(os.getcwd(), "data", "events.json"),
        os.path.join(here, "data", "events.json"),
    ]
    for p in candidates:
        if os.path.exists(p):
            return os.path.abspath(p)
    return None


# ════════════════════════════════════════════
# 產出 add-events-*.py
# ════════════════════════════════════════════
def generate_fill_py(fills, timestamp, mode):
    """
    產出 add-events-YYYYMMDDHHmm-fill-images.py
      fills  - [(ev, new_url, source), ...] 找到替代圖的事件
      mode   - 'default' 或 'overwrite'（用於註解）
    """
    lines = [
        '"""',
        '═══════════════════════════════════════════════════════',
        f'  add-events-{timestamp}-fill-images.py',
        '',
        '  自動補圖（由 images-find-missing.py 產生）',
        '',
        f'  模式: {mode}',
        f'  包含 {len(fills)} 個事件',
        '  每個替代圖的 URL 已使用 Wikimedia 標準縮圖尺寸（1280px）',
        '',
        '  執行：',
        f'    python add-events-{timestamp}-fill-images.py',
        '    python check.py',
        '═══════════════════════════════════════════════════════',
        '"""',
        'import json',
        '',
        "with open('data/events.json', encoding='utf-8') as f:",
        '    d = json.load(f)',
        '',
        "ev_by_id = {e['id']: e for e in d['events']}",
        '',
        '# ═══ 圖片更新對照表 ═══',
        'IMAGE_UPDATES = {',
    ]
    for ev, new_url, source in fills:
        old_url = ev.get("image", "")
        old_short = old_url.split("/")[-1][:60] if old_url else "(空)"
        lines.append(f'    # {ev["zh"]} ({source})  ← 原:{old_short}')
        safe_url = new_url.replace('"', '\\"')
        lines.append(f'    {repr(ev["id"])}: "{safe_url}",')
    lines.extend([
        '}',
        '',
        'updated = 0',
        'missing = 0',
        '',
        'for eid, new_url in IMAGE_UPDATES.items():',
        '    ev = ev_by_id.get(eid)',
        '    if not ev:',
        '        print(f"⚠ 找不到事件: {eid}")',
        '        missing += 1',
        '        continue',
        '    ev["image"] = new_url',
        '    print(f"✓ {ev[\'zh\']:25s} → {new_url[:55]}...")',
        '    updated += 1',
        '',
        '# 儲存（保持 key 順序）',
        'ordered = {}',
        "key_order = ['meta', 'axis_groups', 'axes', 'era_bands', 'era_buttons',",
        "             'filter_cats', 'views', 'view_groups', 'events']",
        'for k in key_order:',
        '    if k in d:',
        '        ordered[k] = d[k]',
        'for k in d:',
        '    if k not in ordered:',
        '        ordered[k] = d[k]',
        '',
        "with open('data/events.json', 'w', encoding='utf-8') as f:",
        '    json.dump(ordered, f, ensure_ascii=False, indent=2)',
        '',
        'print()',
        'print("=" * 55)',
        'print(f"  圖片更新: {updated} 個")',
        'if missing:',
        '    print(f"  找不到事件: {missing}")',
        'print("=" * 55)',
        'print("補圖完成！請執行 python check.py 驗證")',
        '',
    ])
    return "\n".join(lines)


# ════════════════════════════════════════════
# 主流程
# ════════════════════════════════════════════
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
        mode = "overwrite"
        print(f"   模式: 覆蓋所有圖片（--overwrite）")
    else:
        targets = [e for e in events if not e.get("image")]
        mode = "default"
        print(f"   模式: 只補缺圖（{len(targets)} 個）")

    if not targets:
        print("\n✓ 沒有需要處理的事件，結束")
        return

    print()

    # 3. 逐個事件處理
    stat_auto = 0
    stat_multi = 0
    stat_fail = 0
    fills = []          # 成功找到單一候選，會進 .py
    multi_list = []     # 多候選，留空白（只記報告）
    failed_list = []    # 找不到

    for i, ev in enumerate(targets, 1):
        zh = ev.get("zh", "?")
        prefix = f"[{i}/{len(targets)}]"

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
            new_url = candidates[0]["url"]
            source = candidates[0]["source"]
            fills.append((ev, new_url, source))
            print(f"{prefix} ✓ {zh}  [自動·{source}]")
            stat_auto += 1
        else:
            # 多候選 → 不處理（不產 pending-picks）
            multi_list.append((ev["id"], zh, len(candidates)))
            print(f"{prefix} ⊝ {zh}（{len(candidates)} 張候選，留空白由 tools.html 手動挑）")
            stat_multi += 1

        time.sleep(DELAY_BETWEEN_EVENTS)

    # 4. 產出 add-events-*.py
    tools_dir = os.path.dirname(os.path.abspath(__file__))
    ts = datetime.now().strftime("%Y%m%d%H%M")

    if fills:
        py_path = os.path.join(tools_dir, f"add-events-{ts}-fill-images.py")
        with open(py_path, "w", encoding="utf-8") as f:
            f.write(generate_fill_py(fills, ts, mode))
        print(f"\n📄 產出: {py_path}")

    # 5. 總結
    print()
    print("═" * 50)
    print(f"  自動補圖  : {stat_auto}  (進 add-events-*.py)")
    print(f"  多候選    : {stat_multi}  (留空白，用 tools.html 手動挑)")
    print(f"  找不到    : {stat_fail}  (留空白)")
    print("═" * 50)

    if multi_list:
        print(f"\n─── 多候選事件（留空白，請到 cosmic-tools.html 手動補）───")
        for eid, zh, n in multi_list[:10]:
            print(f"  ⊝ {eid:30s} {zh} ({n} 張候選)")
        if len(multi_list) > 10:
            print(f"  ... 還有 {len(multi_list)-10} 個")

    if failed_list:
        print(f"\n─── 找不到候選（留空白）───")
        for eid, zh, reason in failed_list[:10]:
            print(f"  ✗ {eid:30s} {zh} — {reason}")
        if len(failed_list) > 10:
            print(f"  ... 還有 {len(failed_list)-10} 個")

    if fills:
        print(f"\n─── 下一步 ───")
        print(f"  1. 檢視 tools/add-events-{ts}-fill-images.py")
        print(f"  2. 覆蓋並執行：")
        print(f"     copy tools\\add-events-{ts}-fill-images.py .")
        print(f"     python add-events-{ts}-fill-images.py")
        print(f"     python check.py")


if __name__ == "__main__":
    main()
