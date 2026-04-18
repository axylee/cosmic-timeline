"""
═══════════════════════════════════════════════════════
  Cosmic Timeline — 死圖檢查腳本（本機執行）

  職責：檢查 events.json 中所有 image URL 是否還能載入。
  這是補圖流程的最後一道防線，不負責補圖（補圖由 tools.html 或
  images-find-missing.py 處理）。

  用法：
    python tools/images-check-dead.py          # 只檢查，產報告
    python tools/images-check-dead.py --fix    # 清空死連結的 image，產 .py

  檢查邏輯：
    對每個 image URL 發 HTTP HEAD 請求（序列化，對 Wikimedia 友善）
      - 200 OK                → 正常，跳過
      - 403 Forbidden         → 死連結
      - 404 Not Found         → 死連結
      - 429 Too Many Requests → 可疑（限流，依 Retry-After 重試）
      - 其他錯誤 / timeout    → 可疑

  --fix 的處理方式：
    把死連結事件的 image 欄位清空（= ""）
    產出 add-events-YYYYMMDDHHmm-clear-dead.py
    執行後，使用者可以到 cosmic-tools.html 篩「缺圖事件」手動補

  遵循 Wikimedia Robot Policy:
    - concurrency = 1 (序列化)
    - delay >= 1 秒
    - 遇 429 依 Retry-After 標頭等待

  產出（都放在 tools/）：
    tools/dead-images-YYYYMMDDHHmm.txt        ← 人看的報告
    tools/add-events-YYYYMMDDHHmm-clear-dead.py  ← --fix 時產出
═══════════════════════════════════════════════════════
"""
import argparse
import json
import os
import sys
import time
from datetime import datetime

try:
    import requests
except ImportError:
    print("✗ 缺少 requests 套件，請先執行：pip install requests")
    sys.exit(1)


# ════════════════════════════════════════════
# 設定
# ════════════════════════════════════════════
USER_AGENT = "CosmicTimeline-ImageChecker/1.0 (https://cosmichistorytimeline.com)"
REQUEST_TIMEOUT = 10
DEAD_STATUS_CODES = {403, 404}

session = requests.Session()
session.headers.update({"User-Agent": USER_AGENT})


# ════════════════════════════════════════════
# URL 檢查
# ════════════════════════════════════════════
def check_url(url, max_retries=3):
    """
    回傳 (status, detail)
      'ok'         - 2xx
      'dead'       - 403 / 404
      'suspicious' - 429 重試仍失敗 / 其他錯誤 / timeout

    遇 429 依 Retry-After 標頭等待並重試。
    """
    if not url:
        return ("suspicious", "empty url")

    for attempt in range(max_retries + 1):
        try:
            r = session.head(url, timeout=REQUEST_TIMEOUT, allow_redirects=True)
            code = r.status_code

            # 某些 CDN 對 HEAD 回 405，fallback GET
            if code in (405, 501):
                r = session.get(url, timeout=REQUEST_TIMEOUT,
                                stream=True, allow_redirects=True)
                code = r.status_code
                r.close()

            # 429 Rate Limit → 依 Retry-After 等待
            if code == 429 and attempt < max_retries:
                retry_after = r.headers.get("Retry-After", "")
                try:
                    wait = int(retry_after) if retry_after.isdigit() else 5
                except Exception:
                    wait = 5
                wait = min(max(wait, 5), 30)
                print(f"     ⏸ 429 限流，等 {wait} 秒...")
                time.sleep(wait)
                continue

            # 5xx → 等 10 秒重試
            if 500 <= code < 600 and attempt < max_retries:
                time.sleep(10)
                continue

            if 200 <= code < 300:
                return ("ok", str(code))
            elif code in DEAD_STATUS_CODES:
                return ("dead", str(code))
            else:
                return ("suspicious", str(code))
        except requests.Timeout:
            if attempt < max_retries:
                time.sleep(3)
                continue
            return ("suspicious", "timeout")
        except requests.ConnectionError as e:
            if attempt < max_retries:
                time.sleep(3)
                continue
            return ("suspicious", f"conn: {type(e).__name__}")
        except Exception as e:
            return ("suspicious", f"err: {type(e).__name__}")

    return ("suspicious", "retries exhausted")


def check_all_urls(events, delay=1.0):
    """
    序列化檢查所有 events 的 image URL
    遵循 Wikimedia Robot Policy (concurrency=1, delay>=1s)
    """
    tasks = [ev for ev in events if ev.get("image")]

    print(f"🔍 準備檢查 {len(tasks)} 個 URL")
    print(f"   並發: 1 線程（遵循 Wikimedia Robot Policy）")
    print(f"   間隔: {delay} 秒")
    est_min = len(tasks) * delay / 60
    print(f"   預估: 約 {est_min:.0f} 分鐘（不含 429 重試）")
    print()

    results = {}
    last_print = time.time()

    for i, ev in enumerate(tasks, 1):
        zh = ev.get("zh", "?")
        status, detail = check_url(ev["image"])
        results[ev["id"]] = (status, detail)

        symbol = {"ok": "✓", "dead": "✗", "suspicious": "?"}[status]
        now = time.time()
        if status != "ok":
            print(f"  [{i:>3}/{len(tasks)}] {symbol} {zh[:24]:24s} — {status} ({detail})")
            last_print = now
        elif i % 50 == 0 or now - last_print > 30:
            print(f"  [{i:>3}/{len(tasks)}] 進行中... ({ev.get('axis', ''):15s} {zh[:20]})")
            last_print = now

        if i < len(tasks):
            time.sleep(delay)

    return results


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
# 產出 add-events-*.py（--fix 時用）
# ════════════════════════════════════════════
def generate_clear_py(dead_events, timestamp):
    """產出清空 image 欄位的 .py"""
    lines = [
        '"""',
        '═══════════════════════════════════════════════════════',
        f'  add-events-{timestamp}-clear-dead.py',
        '',
        '  清空死連結事件的 image 欄位（由 images-check-dead.py --fix 產生）',
        '',
        f'  包含 {len(dead_events)} 個事件',
        '  執行後這些事件的 image="" ，使用者可以到 cosmic-tools.html',
        '  篩「缺圖事件」手動補圖，或跑 images-find-missing.py 自動補',
        '',
        '  執行：',
        f'    python add-events-{timestamp}-clear-dead.py',
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
        '# ═══ 要清空 image 的事件清單 ═══',
        'EVENT_IDS_TO_CLEAR = [',
    ]
    for ev, detail in dead_events:
        old_url = ev.get("image", "")
        old_short = old_url.split("/")[-1][:50]
        lines.append(f'    # {ev["zh"]}  (HTTP {detail})  ← 原:{old_short}')
        lines.append(f'    {repr(ev["id"])},')
    lines.extend([
        ']',
        '',
        'cleared = 0',
        'missing = 0',
        '',
        'for eid in EVENT_IDS_TO_CLEAR:',
        '    ev = ev_by_id.get(eid)',
        '    if not ev:',
        '        print(f"⚠ 找不到事件: {eid}")',
        '        missing += 1',
        '        continue',
        '    ev["image"] = ""',
        '    print(f"⊘ 清空 {ev[\'zh\']:25s} (待手動補圖)")',
        '    cleared += 1',
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
        'print(f"  清空: {cleared} 個事件")',
        'if missing:',
        '    print(f"  找不到事件: {missing}")',
        'print("=" * 55)',
        'print("清空完成！現在可以：")',
        'print("  1. 打開 cosmic-tools.html 篩「缺圖事件」手動補")',
        'print("  2. 或跑 python tools/images-find-missing.py 自動補")',
        '',
    ])
    return "\n".join(lines)


# ════════════════════════════════════════════
# 產出報告
# ════════════════════════════════════════════
def generate_report(results, events, fix_mode=False):
    """產出死圖報告 txt"""
    ev_by_id = {e["id"]: e for e in events}

    dead = [(eid, det) for eid, (s, det) in results.items() if s == "dead"]
    suspicious = [(eid, det) for eid, (s, det) in results.items() if s == "suspicious"]
    ok_count = sum(1 for (s, _) in results.values() if s == "ok")

    lines = []
    lines.append("═══════════════════════════════════════════════════════")
    lines.append(f"  Cosmic Timeline 死圖檢查報告")
    lines.append(f"  產生時間: {datetime.now().isoformat()}")
    if fix_mode:
        lines.append(f"  模式: --fix（死連結將被清空）")
    lines.append("═══════════════════════════════════════════════════════")
    lines.append("")
    lines.append(f"總檢查數: {len(results)}")
    lines.append(f"  ✓ 正常     : {ok_count}")
    lines.append(f"  ✗ 死連結   : {len(dead)}  (403/404)")
    lines.append(f"  ? 可疑     : {len(suspicious)}  (限流、timeout、其他錯誤)")
    lines.append("")

    # 死連結清單
    lines.append("─── 死連結事件 ─────")
    if fix_mode:
        lines.append("    (這些事件的 image 會被清空，使用 tools.html 或 images-find-missing.py 補回)")
    else:
        lines.append("    (加 --fix 可清空這些事件的 image 欄位)")
    if not dead:
        lines.append("  (無)")
    else:
        for eid, det in sorted(dead):
            ev = ev_by_id.get(eid, {})
            zh = ev.get("zh", "?")
            url = ev.get("image", "")
            lines.append(f"  [{det}] {eid:30s} {zh}")
            lines.append(f"         URL: {url}")
    lines.append("")

    # 可疑清單
    lines.append("─── 可疑事件（不會自動處理，可能要人工判斷）─────")
    lines.append("    (常見原因：429 限流、網站暫時性錯誤、網路連線問題)")
    if not suspicious:
        lines.append("  (無)")
    else:
        for eid, det in sorted(suspicious):
            ev = ev_by_id.get(eid, {})
            zh = ev.get("zh", "?")
            url = ev.get("image", "")
            lines.append(f"  [{det:15s}] {eid:30s} {zh}")
            lines.append(f"         URL: {url}")
    lines.append("")

    return "\n".join(lines)


# ════════════════════════════════════════════
# 主流程
# ════════════════════════════════════════════
def main():
    parser = argparse.ArgumentParser(description="Cosmic Timeline 死圖檢查腳本")
    parser.add_argument("--fix", action="store_true",
                        help="清空死連結的 image 欄位，產 add-events-*.py")
    parser.add_argument("--delay", type=float, default=1.0,
                        help="每個 URL 之間的間隔秒數（預設 1.0）")
    parser.add_argument("--events", default=None,
                        help="手動指定 events.json 路徑（預設自動尋找）")
    args = parser.parse_args()

    # 1. 讀 events.json
    events_path = args.events or find_events_json()
    if not events_path or not os.path.exists(events_path):
        print("✗ 找不到 events.json")
        sys.exit(1)
    print(f"📂 讀取: {events_path}")
    with open(events_path, encoding="utf-8") as f:
        data = json.load(f)
    events = data.get("events", [])
    print(f"   共 {len(events)} 個事件")
    print()

    # 2. 檢查所有 URL
    t0 = time.time()
    results = check_all_urls(events, delay=args.delay)
    elapsed = time.time() - t0

    dead_count = sum(1 for (s, _) in results.values() if s == "dead")
    susp_count = sum(1 for (s, _) in results.values() if s == "suspicious")
    ok_count = sum(1 for (s, _) in results.values() if s == "ok")

    print()
    print("═" * 55)
    print(f"  檢查完成（耗時 {elapsed/60:.1f} 分鐘）")
    print(f"  ✓ 正常   : {ok_count}")
    print(f"  ✗ 死連結 : {dead_count}")
    print(f"  ? 可疑   : {susp_count}")
    print("═" * 55)

    tools_dir = os.path.dirname(os.path.abspath(__file__))
    ts = datetime.now().strftime("%Y%m%d%H%M")

    # 3. --fix 產 .py 清空死連結
    if args.fix and dead_count > 0:
        dead_events = [(e, results[e["id"]][1])
                       for e in events
                       if results.get(e["id"], (None,))[0] == "dead"]
        py_path = os.path.join(tools_dir, f"add-events-{ts}-clear-dead.py")
        with open(py_path, "w", encoding="utf-8") as f:
            f.write(generate_clear_py(dead_events, ts))
        print(f"\n📄 產出: {py_path}")
        print(f"   包含 {len(dead_events)} 個要清空 image 的事件")

    # 4. 產出報告 txt
    report_path = os.path.join(tools_dir, f"dead-images-{ts}.txt")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(generate_report(results, events, fix_mode=args.fix))
    print(f"\n📄 報告: {report_path}")

    # 5. 下一步提示
    print()
    print("─── 下一步 ───")
    if args.fix and dead_count > 0:
        print(f"  1. 檢視 tools/add-events-{ts}-clear-dead.py")
        print(f"  2. 覆蓋並執行：")
        print(f"     copy tools\\add-events-{ts}-clear-dead.py .")
        print(f"     python add-events-{ts}-clear-dead.py")
        print(f"     python check.py")
        print(f"  3. 之後補圖：")
        print(f"     - cosmic-tools.html 篩「缺圖事件」手動補，或")
        print(f"     - python tools/images-find-missing.py 自動補")
    else:
        print(f"  1. 檢視報告 tools/dead-images-{ts}.txt")
        if dead_count > 0:
            print(f"  2. 若要清空死連結：python tools/images-check-dead.py --fix")


if __name__ == "__main__":
    main()
