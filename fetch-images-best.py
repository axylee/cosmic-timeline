#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
For events with no image, find the best Wikimedia-Commons image using:
  1. LLM-generated search keywords (semantic understanding of the event)
  2. Multi-source candidate gathering:
     - Commons direct search
     - Multi-language Wikipedia article image lists (filtered to Commons-hosted)
     - Wikidata image property (always Commons)
  3. Claude vision picks best from candidates by visual relevance to event

Stays Commons-only for license safety. Other-wiki images that are fair-use
local files are filtered out.

If no good candidate found, leaves image field blank (better than wrong image).

Run:
  ANTHROPIC_API_KEY="..." python fetch-images-best.py            # all missing
  ANTHROPIC_API_KEY="..." python fetch-images-best.py event-id1 event-id2  # specific
"""
import json, os, sys, time, urllib.request, urllib.parse, re, base64
from pathlib import Path

try:
    import anthropic
except ImportError:
    print("ERROR: pip install anthropic", file=sys.stderr); sys.exit(1)

PATH = Path(__file__).parent / 'data' / 'events.json'
USER_AGENT = 'CosmicHistoryTimeline/1.0 (https://www.cosmichistorytimeline.com)'
SLEEP = 0.25
MAX_CANDIDATES = 8
MODEL = 'claude-sonnet-4-5'  # vision-heavy task, Sonnet picks better than Haiku

GENERIC_BLACKLIST = (
    'flag_of_', 'flag of ', 'flag-of-',
    'coat_of_arms', 'coat of arms', 'coat-of-arms',
    'state_emblem', 'state emblem', 'seal_of_', 'logo_of_', 'symbol_of_',
    'commons-logo', 'edit-icon', 'wikipedia-logo', 'stub_icon',
    'wiki_letter_w', 'translation_to_english',
)

# Only accept actual image file types (browsers can't render PDFs/audio in <img>).
# Commons hosts PDFs (book scans), DjVu, OGG audio etc. — LLM might pick them by
# semantic relevance, but they break in HTML. Filter at candidate-gathering stage.
VALID_IMG_EXTS = ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.tif', '.tiff')


def is_image_file(url_or_title):
    """True if URL/title ends with a valid image extension."""
    low = url_or_title.lower().split('?')[0]
    return low.endswith(VALID_IMG_EXTS)

KEYWORD_SYSTEM_PROMPT = """You are a research assistant generating concise Wikimedia Commons search keywords for finding the best image of a historical event.

Output JSON: {"keywords": ["term1", "term2", "term3"]} — exactly 3 keywords.

Rules:
- Use English keywords only (Commons indexes English best).
- Each keyword should be 2-4 words, specific enough to find on Commons.
- Prefer concrete nouns: artifacts, monuments, paintings, persons by name, places.
- AVOID generic terms like "ancient history", "war", "civilization" — too broad.
- Think about what physical evidence exists for this event in museums/archives.

Examples:
  Event: "Sargon of Akkad rises to power" →
    {"keywords": ["Sargon Akkad bronze head", "Akkadian Empire artifact", "Sargon ancient Mesopotamia"]}

  Event: "Naram-Sin victory stele commemoration" →
    {"keywords": ["Naram-Sin victory stele", "Akkadian victory stele Louvre", "Naram-Sin king relief"]}

  Event: "4.2 kya climate event drought" →
    {"keywords": ["4.2 kiloyear event", "Bronze Age collapse climate", "Akkadian drought paleoclimate"]}
"""

PICK_SYSTEM_PROMPT = """You are a picture editor selecting the single best image to illustrate a historical event for a museum-quality timeline website.

You will see one event description and several candidate images. Pick the SINGLE candidate that is most directly and informatively related to the event itself.

Output JSON: {"choice": <0-based index>, "reason": "<brief>"} or {"choice": -1, "reason": "none acceptable"}.

Rules:
- "Most directly related" means: shows the actual subject, place, person, artifact, or visual evidence of the event.
- REJECT generic flags, coats of arms, country emblems, abstract diagrams, irrelevant landscapes, modern photos for ancient events, low-quality scans, or clearly unrelated images.
- A drawing/painting of the actual event or person is preferred over a generic period image.
- A close-up of an artifact (statue, relief, stele, manuscript) is excellent.
- Maps are OK if they specifically illustrate the event's geography.
- If NO candidate is acceptably relevant, return choice: -1.
"""


def is_generic(url_or_title):
    low = url_or_title.lower()
    return any(b in low for b in GENERIC_BLACKLIST)


def http_json(url):
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode('utf-8'))


def commons_search(term, limit=5):
    """Search Wikimedia Commons File: namespace for images matching term."""
    url = (
        'https://commons.wikimedia.org/w/api.php?'
        'action=query&format=json&list=search&srnamespace=6&'
        f'srsearch={urllib.parse.quote(term)}&srlimit={limit}'
    )
    try:
        data = http_json(url)
        results = data.get('query', {}).get('search', [])
        # Need to fetch URLs for each title
        out = []
        for r in results:
            title = r.get('title', '')
            if not title.startswith('File:'): continue
            if is_generic(title): continue
            if not is_image_file(title): continue  # File:Foo.pdf etc
            # Get image URL via imageinfo
            url2 = (
                'https://commons.wikimedia.org/w/api.php?'
                'action=query&format=json&prop=imageinfo&iiprop=url|size&'
                f'iiurlwidth=400&titles={urllib.parse.quote(title)}'
            )
            try:
                d2 = http_json(url2)
                for p in d2.get('query', {}).get('pages', {}).values():
                    info = (p.get('imageinfo') or [{}])[0]
                    full_url = info.get('url', '')
                    thumb_url = info.get('thumburl', full_url)
                    width = info.get('width', 0)
                    height = info.get('height', 0)
                    # Skip tiny images and SVGs that aren't art (icon-like)
                    if width < 200 or height < 150: continue
                    if is_generic(full_url): continue
                    if not is_image_file(full_url): continue  # skip PDF/djvu/ogg etc
                    out.append({
                        'url': full_url,
                        'thumb': thumb_url,
                        'title': title,
                    })
            except Exception:
                continue
            time.sleep(0.1)
        return out
    except Exception:
        return []


def article_images_via_wiki(event, lang):
    """Get Commons-hosted images linked from a language-specific Wikipedia article."""
    wiki_field = 'wiki_en' if lang == 'en' else 'wiki_zh'
    url = event.get(wiki_field, '')
    m = re.search(r'/wiki/([^?#]+)', url)
    if not m: return []
    title = urllib.parse.unquote(m.group(1).split('#')[0])
    api = (
        f'https://{lang}.wikipedia.org/w/api.php?'
        'action=query&format=json&prop=images&imlimit=15&'
        f'titles={urllib.parse.quote(title)}'
    )
    try:
        data = http_json(api)
        out = []
        for p in data.get('query', {}).get('pages', {}).values():
            for im in p.get('images', []):
                t = im.get('title', '')
                if not t.startswith('File:'): continue
                if is_generic(t): continue
                if not is_image_file(t): continue  # File:Foo.pdf etc
                # Verify hosted on Commons (not local fair-use)
                api2 = (
                    f'https://{lang}.wikipedia.org/w/api.php?'
                    'action=query&format=json&prop=imageinfo&iiprop=url|size&'
                    f'iiurlwidth=400&titles={urllib.parse.quote(t)}'
                )
                try:
                    d2 = http_json(api2)
                    for p2 in d2.get('query', {}).get('pages', {}).values():
                        info = (p2.get('imageinfo') or [{}])[0]
                        full_url = info.get('url', '')
                        thumb_url = info.get('thumburl', full_url)
                        width = info.get('width', 0)
                        height = info.get('height', 0)
                        if '/wikipedia/commons/' not in full_url: continue  # fair-use local
                        if width < 200 or height < 150: continue
                        if is_generic(full_url): continue
                        if not is_image_file(full_url): continue  # skip PDF/djvu/ogg
                        out.append({
                            'url': full_url,
                            'thumb': thumb_url,
                            'title': t,
                        })
                except Exception:
                    pass
                time.sleep(0.1)
        return out
    except Exception:
        return []


def llm_keywords(client, event):
    desc = (event.get('desc_en') or event.get('desc_zh') or '')[:300]
    user = f"Event: {event.get('en') or event.get('zh','')} ({event.get('year','?')})\nDescription: {desc}"
    try:
        resp = client.messages.create(
            model=MODEL,
            max_tokens=300,
            system=[{"type": "text", "text": KEYWORD_SYSTEM_PROMPT,
                     "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": user}],
            output_config={
                "format": {
                    "type": "json_schema",
                    "schema": {
                        "type": "object",
                        "properties": {"keywords": {
                            "type": "array",
                            "items": {"type": "string"},
                        }},
                        "required": ["keywords"],
                        "additionalProperties": False,
                    },
                },
            },
        )
        text = next((b.text for b in resp.content if b.type == "text"), "")
        data = json.loads(text)
        return data.get('keywords', []), resp.usage
    except Exception as e:
        print(f'    keyword LLM error: {e}')
        return [], None


def download_thumb(thumb_url):
    """Download thumbnail, return (bytes, media_type) or (None, None)."""
    req = urllib.request.Request(thumb_url, headers={'User-Agent': USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            data = r.read()
            ctype = r.headers.get('Content-Type', 'image/jpeg').split(';')[0].strip()
            # Anthropic supports: jpeg, png, gif, webp
            if ctype not in ('image/jpeg', 'image/png', 'image/gif', 'image/webp'):
                # SVG or other — convert/skip
                return None, None
            # Anthropic max 5MB per image
            if len(data) > 5_000_000: return None, None
            return data, ctype
    except Exception:
        return None, None


def llm_pick(client, event, candidates):
    """Use vision to pick best from candidates. Downloads thumbs as base64."""
    if len(candidates) == 1:
        return 0, "single candidate", None
    # Download each thumb as base64; drop unsupported formats
    valid = []
    for c in candidates:
        data, ctype = download_thumb(c['thumb'])
        if data is None: continue
        valid.append({**c, 'b64': base64.b64encode(data).decode('ascii'), 'ctype': ctype})
        time.sleep(0.1)
    if not valid:
        return -1, "no downloadable thumbs", None
    if len(valid) == 1:
        # Find original index in candidates
        idx = candidates.index(next(c for c in candidates if c['url'] == valid[0]['url']))
        return idx, "single downloadable", None
    desc = (event.get('desc_en') or event.get('desc_zh') or '')[:400]
    user_content = [
        {"type": "text", "text":
         f"Event: {event.get('en') or event.get('zh','')} ({event.get('year','?')})\n"
         f"Description: {desc}\n\nCandidate images (numbered 0-{len(valid)-1}):"},
    ]
    for i, c in enumerate(valid):
        user_content.append({"type": "text", "text": f"\n[{i}] {c['title']}"})
        user_content.append({"type": "image", "source": {
            "type": "base64", "media_type": c['ctype'], "data": c['b64']}})
    user_content.append({"type": "text",
                         "text": "\nPick the SINGLE most directly relevant. Return JSON only."})
    try:
        resp = client.messages.create(
            model=MODEL,
            max_tokens=300,
            system=[{"type": "text", "text": PICK_SYSTEM_PROMPT,
                     "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": user_content}],
            output_config={
                "format": {
                    "type": "json_schema",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "choice": {"type": "integer"},
                            "reason": {"type": "string"},
                        },
                        "required": ["choice", "reason"],
                        "additionalProperties": False,
                    },
                },
            },
        )
        text = next((b.text for b in resp.content if b.type == "text"), "")
        data = json.loads(text)
        choice = data.get('choice', -1)
        reason = data.get('reason', '')
        # Map valid-list index back to original candidates index
        if 0 <= choice < len(valid):
            chosen_url = valid[choice]['url']
            for orig_idx, c in enumerate(candidates):
                if c['url'] == chosen_url:
                    return orig_idx, reason, resp.usage
        return -1, reason, resp.usage
    except Exception as e:
        print(f'    pick LLM error: {e}')
        return -1, str(e), None


def gather_candidates(client, event):
    """Run keyword + multi-source search to collect up to MAX_CANDIDATES."""
    keywords, _kw_usage = llm_keywords(client, event)
    seen_urls = set()
    candidates = []

    # 1. Commons direct search per keyword
    for kw in keywords:
        for c in commons_search(kw, limit=4):
            if c['url'] in seen_urls: continue
            seen_urls.add(c['url'])
            candidates.append(c)
            if len(candidates) >= MAX_CANDIDATES * 2: break
        if len(candidates) >= MAX_CANDIDATES * 2: break
        time.sleep(SLEEP)

    # 2. Multi-language article-image search (en first, then zh)
    if len(candidates) < MAX_CANDIDATES:
        for lang in ['en', 'zh']:
            for c in article_images_via_wiki(event, lang):
                if c['url'] in seen_urls: continue
                seen_urls.add(c['url'])
                candidates.append(c)
            if len(candidates) >= MAX_CANDIDATES: break
            time.sleep(SLEEP)

    # Trim to MAX_CANDIDATES (LLM cost cap)
    return candidates[:MAX_CANDIDATES], _kw_usage


def main():
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY env var not set"); sys.exit(1)

    args = sys.argv[1:]
    only_ids = set(args) if args else None

    client = anthropic.Anthropic(api_key=api_key)

    with open(PATH, encoding='utf-8') as f:
        d = json.load(f)

    todo = []
    for e in d['events']:
        if e.get('image'): continue  # already has image
        if only_ids and e.get('id') not in only_ids: continue
        todo.append(e)

    print(f'events to process: {len(todo)}')
    if only_ids and not todo:
        print('no matching missing-image events'); return

    n_found = n_blank = 0
    grand_in = grand_out = 0

    for i, e in enumerate(todo, 1):
        eid = e.get('id', '?')
        try:
            print(f'\n[{i}/{len(todo)}] {eid} | {(e.get("en") or e.get("zh","") or "")[:50]}')
        except UnicodeEncodeError:
            print(f'\n[{i}/{len(todo)}] {eid}')

        try:
            cands, kw_usage = gather_candidates(client, e)
            if kw_usage:
                grand_in += kw_usage.input_tokens
                grand_out += kw_usage.output_tokens

            if not cands:
                print(f'    no candidates · LEAVE BLANK')
                n_blank += 1
                continue

            print(f'    {len(cands)} candidates → vision pick')
            idx, reason, pick_usage = llm_pick(client, e, cands)
            if pick_usage:
                grand_in += pick_usage.input_tokens
                grand_out += pick_usage.output_tokens

            if idx < 0 or idx >= len(cands):
                print(f'    LLM rejected all · LEAVE BLANK ({reason[:60]})')
                n_blank += 1
                continue

            chosen = cands[idx]
            e['image'] = chosen['url']
            if 'image_credit' in e: del e['image_credit']  # will re-fetch later
            print(f'    + {chosen["title"][:55]} ({reason[:40]})')
            n_found += 1
        except Exception as ex:
            print(f'    ERROR: {type(ex).__name__}: {ex}')
            n_blank += 1
            continue

        # Checkpoint every 25
        if i % 25 == 0:
            with open(PATH, 'w', encoding='utf-8') as f:
                json.dump(d, f, ensure_ascii=False, indent=2)
            cost_so_far = (grand_in * 1.0 + grand_out * 5.0) / 1_000_000
            print(f'\n  --- checkpoint [{i}/{len(todo)}] found={n_found} blank={n_blank} ~${cost_so_far:.3f} ---\n')

    with open(PATH, 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

    cost = (grand_in * 1.0 + grand_out * 5.0) / 1_000_000
    print(f'\nDONE. found={n_found} blank={n_blank}  ~${cost:.4f}')


if __name__ == '__main__':
    main()
