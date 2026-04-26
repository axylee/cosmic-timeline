#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Find Wikimedia Commons replacement images for events whose current image is
either fair-use Wikipedia EN local files (cannot redistribute) or
non-Commons commercial sources.

Strategy: for each problem event, look at its existing wiki_en URL,
query MediaWiki API for the article's main image (pageimages), check if
it's hosted on Commons (not local fair-use), and replace if found.

If no Commons image found → image field is left BLANK (event renders
without image — generator handles missing images gracefully).
"""
import json, sys, time, urllib.request, urllib.parse, re
from pathlib import Path

PATH = Path(__file__).parent / 'data' / 'events.json'
USER_AGENT = 'CosmicHistoryTimeline/1.0 (https://www.cosmichistorytimeline.com)'
SLEEP = 0.5

# Non-Wikimedia / non-NASA images we want to replace
PROBLEM_IDS = [
    'huronian-glaciation',
    'picasso-modern-art',
    'hevo-011',
    'tur-004',
    'mgl-003',
    'hevo-013',
    'grk-colonels-coup',
]

# Allow CLI override for re-running specific events:
import sys as _sys
if len(_sys.argv) > 1 and not _sys.argv[1].startswith('--'):
    PROBLEM_IDS = _sys.argv[1:]


def article_title_from_url(url):
    """Extract article title from a Wikipedia URL."""
    m = re.search(r'/wiki/([^?#]+)', url)
    if not m: return None
    return urllib.parse.unquote(m.group(1).split('#')[0])


GENERIC_BLACKLIST = (
    'flag_of_', 'flag of ', 'flag-of-',
    'coat_of_arms', 'coat of arms', 'coat-of-arms',
    'state_emblem', 'state emblem', 'state-emblem',
    'seal_of_', 'seal of ', 'seal-of-',
    'logo_of_', 'symbol_of_',
    'commons-logo', 'edit-icon', 'wikipedia-logo',
    'stub_icon', 'stub-icon',
)


def is_generic(url):
    """Filter out flags / coats of arms / generic emblems — not informative."""
    low = url.lower()
    return any(b in low for b in GENERIC_BLACKLIST)


def get_pageimage(article_title, lang='en'):
    """Use Wikipedia API to fetch main page image (Commons-hosted, not fair use, not generic)."""
    api = (
        f'https://{lang}.wikipedia.org/w/api.php?'
        'action=query&format=json&prop=pageimages&piprop=original&'
        f'titles={urllib.parse.quote(article_title)}'
    )
    req = urllib.request.Request(api, headers={'User-Agent': USER_AGENT})
    with urllib.request.urlopen(req, timeout=20) as r:
        data = json.loads(r.read().decode('utf-8'))
    pages = data.get('query', {}).get('pages', {})
    if not pages: return None
    page = next(iter(pages.values()))
    if 'original' not in page: return None
    src = page['original'].get('source', '')
    if '/wikipedia/commons/' not in src:
        return None  # Local file (fair use) — skip
    if is_generic(src):
        return None  # Flag / coat of arms / etc — skip, try other strategies
    return src


def list_commons_images_on_page(article_title, lang='en'):
    """Fallback: list all Commons-hosted images on the article. Returns first one."""
    api = (
        f'https://{lang}.wikipedia.org/w/api.php?'
        'action=query&format=json&prop=images&imlimit=20&'
        f'titles={urllib.parse.quote(article_title)}'
    )
    req = urllib.request.Request(api, headers={'User-Agent': USER_AGENT})
    with urllib.request.urlopen(req, timeout=20) as r:
        data = json.loads(r.read().decode('utf-8'))
    pages = data.get('query', {}).get('pages', {})
    if not pages: return None
    page = next(iter(pages.values()))
    images = page.get('images', [])
    # Get URL for each File:xxx — only return ones on Commons
    for img in images:
        title = img.get('title', '')
        if not title.startswith('File:'): continue
        # Skip generic icons/logos by filename
        if is_generic(title.lower()):
            continue
        # Get image info to check it's hosted on Commons
        api2 = (
            f'https://{lang}.wikipedia.org/w/api.php?'
            'action=query&format=json&prop=imageinfo&iiprop=url&'
            f'titles={urllib.parse.quote(title)}'
        )
        req2 = urllib.request.Request(api2, headers={'User-Agent': USER_AGENT})
        try:
            with urllib.request.urlopen(req2, timeout=20) as r2:
                d2 = json.loads(r2.read().decode('utf-8'))
            for p in d2.get('query', {}).get('pages', {}).values():
                if 'imageinfo' not in p: continue
                src = p['imageinfo'][0].get('url', '')
                if '/wikipedia/commons/' in src and not is_generic(src):
                    return src
        except Exception:
            continue
        time.sleep(0.2)
    return None


def find_replacement(event):
    """Conservative: only accept the article's official main image (pageimage).
    Skip all fallback heuristics — better to leave blank than show junk."""
    # Strategy 1: pageimage from English Wikipedia
    wiki_en = event.get('wiki_en', '')
    title = article_title_from_url(wiki_en)
    if title:
        try:
            img = get_pageimage(title, 'en')
            if img: return img, 'pageimages-en'
        except Exception as ex:
            print(f'    pageimages-en fail: {ex}', flush=True)

    # Strategy 2: pageimage from Chinese Wikipedia
    wiki_zh = event.get('wiki_zh', '')
    title_zh = article_title_from_url(wiki_zh)
    if title_zh:
        try:
            img = get_pageimage(title_zh, 'zh')
            if img: return img, 'pageimages-zh'
        except Exception as ex:
            print(f'    pageimages-zh fail: {ex}', flush=True)

    # No reliable main image — leave blank rather than scrape junk
    return None, None


def main():
    with open(PATH, encoding='utf-8') as f:
        d = json.load(f)
    events_by_id = {e.get('id'): e for e in d['events']}

    n_found = n_blank = 0
    for eid in PROBLEM_IDS:
        e = events_by_id.get(eid)
        if not e:
            print(f'!! event not found: {eid}'); continue
        print(f'\n=== {eid} ===', flush=True)
        print(f'    current: {e.get("image","")[:90]}', flush=True)
        print(f'    wiki_en: {e.get("wiki_en","")[:90]}', flush=True)

        new_img, source = find_replacement(e)
        if new_img:
            e['image'] = new_img
            # Clear old image_credit so fetch-image-credits.py re-fetches new metadata
            if 'image_credit' in e:
                del e['image_credit']
            print(f'    + REPLACED via {source}: {new_img[:90]}', flush=True)
            n_found += 1
        else:
            # Leave blank — better than fair-use violation
            e['image'] = ''
            if 'image_credit' in e:
                del e['image_credit']
            print(f'    - NO COMMONS image found · cleared image field', flush=True)
            n_blank += 1
        time.sleep(SLEEP)

    with open(PATH, 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f'\ndone. replaced={n_found}  blanked={n_blank}')


if __name__ == '__main__':
    main()
