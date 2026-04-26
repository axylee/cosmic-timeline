#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Fetch author + license metadata for every Wikimedia Commons image referenced
by events.json, and store as `image_credit` field per event.

Use:
  python fetch-image-credits.py            # full run (~15 min, ~2200 images)
  python fetch-image-credits.py --report   # dry-run, just report stats
  python fetch-image-credits.py --redo     # ignore existing image_credit, refetch

Output schema added to each event with a Commons image:
  image_credit: {
    "author":      "<plain text, HTML stripped>",
    "license":     "CC BY-SA 4.0" or similar short name,
    "license_url": "https://creativecommons.org/...",
    "source_url":  "https://commons.wikimedia.org/wiki/File:..."
  }

Failures (404, missing metadata, parse error) leave image_credit absent;
generator's render_event handles missing gracefully.

Rate limit: 0.4s/request to be courteous to WMF.
"""
import json, time, re, sys, urllib.request, urllib.parse
from pathlib import Path

PATH = Path(__file__).parent / 'data' / 'events.json'
SLEEP = 0.4
USER_AGENT = 'CosmicHistoryTimeline/1.0 (https://www.cosmichistorytimeline.com)'
TIMEOUT = 20


def parse_filename(url):
    m = re.search(r'/wikipedia/commons/thumb/[^/]+/[^/]+/([^/]+)/', url)
    if m: return urllib.parse.unquote(m.group(1))
    m = re.search(r'/wikipedia/commons/[^/]+/[^/]+/([^/?]+)', url)
    if m: return urllib.parse.unquote(m.group(1))
    return None


def fetch_credit(filename):
    api = (
        'https://commons.wikimedia.org/w/api.php?'
        'action=query&format=json&prop=imageinfo&iiprop=extmetadata&'
        f'titles={urllib.parse.quote("File:" + filename)}'
    )
    req = urllib.request.Request(api, headers={'User-Agent': USER_AGENT})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        data = json.loads(r.read().decode('utf-8'))
    pages = data.get('query', {}).get('pages', {})
    if not pages: return None
    page = next(iter(pages.values()))
    if page.get('missing') or 'imageinfo' not in page:
        return None
    md = (page['imageinfo'][0] or {}).get('extmetadata', {}) or {}

    def get(k):
        v = (md.get(k) or {}).get('value', '')
        if not isinstance(v, str): return ''
        return re.sub(r'<[^>]+>', '', v).strip()

    return {
        'author':      get('Artist') or get('Credit') or '',
        'license':     get('LicenseShortName') or get('License') or '',
        'license_url': (md.get('LicenseUrl') or {}).get('value', '') or '',
        'source_url':  f'https://commons.wikimedia.org/wiki/File:{urllib.parse.quote(filename.replace(" ","_"))}',
    }


def main():
    with open(PATH, encoding='utf-8') as f:
        d = json.load(f)

    redo = '--redo' in sys.argv
    report = '--report' in sys.argv

    have_img = [e for e in d['events'] if e.get('image')]
    wm = [e for e in have_img if 'wikipedia/commons' in e['image']]
    non_wm = [e for e in have_img if 'wikipedia/commons' not in e['image']]
    todo = [e for e in wm if redo or not e.get('image_credit')]

    print(f'events with image: {len(have_img)}')
    print(f'  wikimedia commons: {len(wm)}  (todo={len(todo)})')
    print(f'  other src:         {len(non_wm)}  (manual review)')
    print(f'estimated time:    ~{len(todo)*SLEEP/60:.1f} min @ {SLEEP}s/req')

    if report:
        return

    if not todo:
        print('nothing to fetch.')
        return

    n_ok = n_fail = 0
    for i, e in enumerate(todo):
        fn = parse_filename(e['image'])
        if not fn:
            n_fail += 1
            continue
        try:
            cred = fetch_credit(fn)
            if cred and (cred['author'] or cred['license']):
                e['image_credit'] = cred
                n_ok += 1
            else:
                n_fail += 1
        except Exception as ex:
            print(f'  ! {e.get("id")}: {type(ex).__name__}: {ex}')
            n_fail += 1
        # checkpoint every 100
        if (i + 1) % 100 == 0:
            with open(PATH, 'w', encoding='utf-8') as f:
                json.dump(d, f, ensure_ascii=False, indent=2)
            print(f'  [{i+1:>4}/{len(todo)}]  ok={n_ok}  fail={n_fail}  (checkpoint saved)')
        time.sleep(SLEEP)

    with open(PATH, 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f'done.  ok={n_ok}  fail={n_fail}')


if __name__ == '__main__':
    main()
