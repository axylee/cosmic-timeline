#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Generate static SEO-friendly aggregation pages from events.json.

Usage:
  python generate-pages.py <view_id>       # generate one view
  python generate-pages.py --all           # generate all views (later)

Output: <project>/<view.group>/<view.id>.html
        e.g. wars/ww2.html, countries/japan.html
"""
import json, os, sys, html, re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent
DATA = ROOT / 'data' / 'events.json'

# ---------- helpers ----------

def load():
    with open(DATA, encoding='utf-8') as f:
        return json.load(f)

def event_axes(e):
    if 'axes' in e and isinstance(e['axes'], list):
        return e['axes']
    if 'axis' in e:
        return [e['axis']]
    return []

def fmt_year(y):
    """1933 -> '1933'; 1933.08 -> '1933 年 1 月'; -660 -> '西元前 660 年'"""
    if y is None: return ''
    if y < 0:
        return f'西元前 {abs(int(y))} 年'
    yi = int(y)
    frac = y - yi
    if frac > 0.005:
        m = max(1, min(12, round(frac * 12)))
        return f'{yi} 年 {m} 月'
    return f'{yi} 年'

def fmt_year_short(y):
    if y is None: return ''
    if y < 0:
        return f'-{abs(int(y))}'
    return str(int(y))

def _dedupe_for_view(out, view):
    """Drop duplicate events (same zh title, same int year). Common cause:
    one event tagged on 2+ axes for canvas cross-display (e.g. 凱撒遇刺
    has julius-caesar on greece axis AND julius-caesar-emp-rome on emp-rome-early).

    Also drops "begin point + pill" pairs (same year + one title is substring of
    another, e.g. "百年戰爭爆發" 1337 + "百年戰爭" pill 1337-1453).
    Prefers the pill (more informative).

    Picks the event whose axis appears earliest in view.axes (most specific to this view)."""
    view_ax = view.get('axes') or []
    ax_priority = {a: i for i, a in enumerate(view_ax)}

    def specificity(e):
        # Lower = more specific to this view; cross axis worst
        for ax in event_axes(e):
            if ax in ax_priority and ax != 'cross':
                return ax_priority[ax]
        return 9999

    # Phase 1: exact (title, year) dedup as before
    best = {}  # key: (zh title, int year) -> best event so far
    for e in out:
        title = (e.get('zh', '') or '').strip()
        year = e.get('year')
        if not title or year is None:
            best.setdefault(('__nokey__', id(e)), e)
            continue
        key = (title, int(year))
        if key not in best or specificity(e) < specificity(best[key]):
            best[key] = e
    phase1 = [e for e in out if id(e) in {id(v) for v in best.values()}]

    # Phase 2: substring dedup — same int year + one title substring of another.
    # Prefer pill (has endYear) over point (more context); else prefer more specific axis.
    by_year = {}
    for e in phase1:
        y = e.get('year')
        if y is None: continue
        by_year.setdefault(int(y), []).append(e)

    drop_ids = set()
    for y, group in by_year.items():
        if len(group) < 2: continue
        for i, a in enumerate(group):
            if id(a) in drop_ids: continue
            ta = (a.get('zh', '') or '').strip()
            if not ta: continue
            for b in group[i+1:]:
                if id(b) in drop_ids: continue
                tb = (b.get('zh', '') or '').strip()
                if not tb or ta == tb: continue
                # Substring match: one title contains the other (both directions)
                if ta in tb or tb in ta:
                    # Prefer event with endYear (pill); tie-break by specificity
                    a_pill = a.get('endYear') is not None
                    b_pill = b.get('endYear') is not None
                    if a_pill and not b_pill:
                        drop_ids.add(id(b))
                    elif b_pill and not a_pill:
                        drop_ids.add(id(a)); break  # a dropped, no need to compare further
                    else:
                        # Both pill or both point — drop the less specific
                        if specificity(a) <= specificity(b):
                            drop_ids.add(id(b))
                        else:
                            drop_ids.add(id(a)); break

    return [e for e in phase1 if id(e) not in drop_ids]


def filter_events(events, view):
    """Pick events for the agg page based on the highest-priority filter available.

    Priority (first match wins):
      1. LLM-curated: events with `relevant_views` containing this view.id
      2. Manual focus config: any of core_axes / core_id_prefixes / core_event_ids
      3. Fallback: view.axes (canvas overview behavior)

    Always followed by dedup (drops same-title-same-year duplicates).
    """
    vid = view['id']
    yr_start = view.get('yearStart', -1e18)
    yr_end = view.get('yearEnd', 1e18)

    # If view uses manual focus (core_axes/prefixes/ids), skip year-bound limits.
    # Lets bio views include legacy events (e.g. da-vinci's 2017 Salvator auction,
    # genghis's 2003 DNA study) without forcing yearEnd to be artificially long
    # — yearEnd then only controls canvas default zoom range, not agg-page filter.
    has_focus_year_skip = bool(
        view.get('core_axes') or view.get('core_id_prefixes') or view.get('core_event_ids')
    )

    def _in_year(e):
        if has_focus_year_skip: return True
        y = e.get('year')
        return y is not None and yr_start <= y <= yr_end

    def _sort_key(e):
        eid = e.get('id', '') or ''
        origin = 0 if eid.startswith('big-bang') else 1
        return (origin, e.get('year', 0), -(e.get('level') or 0))

    # 1. LLM-curated relevance (if any event is tagged for this view)
    llm_tagged = [e for e in events if vid in (e.get('relevant_views') or [])]
    if llm_tagged:
        out = [e for e in llm_tagged if _in_year(e)]
        out = _dedupe_for_view(out, view)
        out.sort(key=_sort_key)
        return out

    # 2. Manual focus config
    has_focus = bool(view.get('core_axes') or view.get('core_id_prefixes') or view.get('core_event_ids'))
    axset = set(view.get('core_axes') or ([] if has_focus else (view.get('axes') or [])))
    prefixes = tuple(view.get('core_id_prefixes') or [])
    ids = set(view.get('core_event_ids') or [])

    out = []
    for e in events:
        if not _in_year(e): continue
        eid = e.get('id', '') or ''
        if axset and any(a in axset for a in event_axes(e)):
            out.append(e); continue
        # Bio-view friendly: also include events whose crossRef points back to a core axis.
        # Lets historical events (Battle of Gaugamela on emp-alex axis) appear in alexander
        # agg page when they crossRef to bio-alexander.
        if axset:
            xr = e.get('crossRef') or []
            if isinstance(xr, str): xr = [xr]
            if any(a in axset for a in xr):
                out.append(e); continue
        if prefixes and eid.startswith(prefixes):
            out.append(e); continue
        if ids and eid in ids:
            out.append(e); continue
    out = _dedupe_for_view(out, view)
    out.sort(key=_sort_key)
    return out


def ensure_year_bounds(view, events):
    """If view lacks yearStart/yearEnd, derive from in-scope events."""
    if view.get('yearStart') is not None and view.get('yearEnd') is not None:
        return
    in_scope = filter_events(events, view)
    if not in_scope:
        view['yearStart'] = view.get('yearStart', 0)
        view['yearEnd'] = view.get('yearEnd', 1)
        return
    ys = min(e['year'] for e in in_scope)
    ye = max(e['year'] for e in in_scope)
    if view.get('yearStart') is None: view['yearStart'] = int(ys)
    if view.get('yearEnd') is None: view['yearEnd'] = int(ye) + 1

def split_eras(events, view):
    """Return list of (label_zh, label_en, [events])."""
    if not events: return []
    span = view['yearEnd'] - view['yearStart']
    if view.get('group') == 'wars' and span <= 30:
        s = view['yearStart']; e = view['yearEnd']
        cuts = [s, s + span*0.25, s + span*0.5, s + span*0.75, e]
        labels_zh = ['戰前序曲', '開戰', '全面爆發', '終戰']
        labels_en = ['Prelude', 'Outbreak', 'Escalation', 'Endgame']
    elif span > 5000:
        cuts = [view['yearStart'], 600, 1500, 1900, view['yearEnd']]
        labels_zh = ['古代', '中世紀', '近代', '現代']
        labels_en = ['Ancient', 'Medieval', 'Early Modern', 'Modern']
    else:
        s = view['yearStart']; e = view['yearEnd']
        cuts = [s, s + span*0.25, s + span*0.5, s + span*0.75, e]
        labels_zh = [f'{fmt_year_short(cuts[i])} – {fmt_year_short(cuts[i+1])}' for i in range(4)]
        labels_en = labels_zh[:]

    buckets = [[] for _ in labels_zh]
    for ev in events:
        y = ev['year']
        idx = 0
        for i in range(len(labels_zh)):
            if y >= cuts[i]:
                idx = i
        buckets[idx].append(ev)
    return [(lz, le, evs) for lz, le, evs in zip(labels_zh, labels_en, buckets) if evs]

def image_credit(img_url):
    """Try to derive a Wikimedia Commons file page URL from a hot-linked image.
    Returns (display_label, file_page_url) or (None, None)."""
    if not img_url:
        return None, None
    # Wikimedia thumb: /wikipedia/commons/thumb/<a>/<ab>/<filename>/<thumb_size>-<filename>
    m = re.search(r'/wikipedia/commons/thumb/[^/]+/[^/]+/([^/]+)/', img_url)
    if m:
        fn = m.group(1)
        return ('Wikimedia Commons', f'https://commons.wikimedia.org/wiki/File:{fn}')
    # Wikimedia direct: /wikipedia/commons/<a>/<ab>/<filename>
    m = re.search(r'/wikipedia/commons/[^/]+/[^/]+/([^/?]+)', img_url)
    if m:
        fn = m.group(1)
        return ('Wikimedia Commons', f'https://commons.wikimedia.org/wiki/File:{fn}')
    # Local /images/ asset — own work or pre-cleared
    if '/images/' in img_url or img_url.startswith('images/'):
        return ('本站圖庫', None)
    return ('外部來源', None)


def render_mini_timeline(view, events, axes_by_id, cat_color):
    """Render a static SVG mini-timeline as the signature visual.
    Lanes per view axis, dots per event, click → scroll to article anchor."""
    yr_start = view['yearStart']
    yr_end = view['yearEnd']
    span = max(1, yr_end - yr_start)
    width = 720
    margin_left = 110
    margin_right = 14
    margin_top = 28
    lane_h = 20
    plot_w = width - margin_left - margin_right
    view_axes = view.get('axes') or []
    height = margin_top + len(view_axes) * lane_h + 16

    def x_for(yr):
        return margin_left + (yr - yr_start) / span * plot_w

    # Year markers — pick ~6 ticks
    n_ticks = 6
    ticks = []
    for i in range(n_ticks + 1):
        yr = yr_start + span * i / n_ticks
        ticks.append(yr)

    parts = [
        f'<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" '
        f'role="img" aria-label="{html.escape(view.get("label",""))} 時間軸概覽" '
        f'style="display:block;width:100%;height:auto;background:rgba(255,255,255,0.015);'
        f'border:1px solid rgba(167,139,250,0.18);border-radius:6px;">'
    ]
    # year ticks
    for yr in ticks:
        x = x_for(yr)
        lab = fmt_year_short(yr)
        parts.append(
            f'<line x1="{x:.1f}" y1="{margin_top-4}" x2="{x:.1f}" y2="{height-8}" '
            f'stroke="rgba(255,255,255,0.05)" stroke-width="1"/>'
            f'<text x="{x:.1f}" y="{margin_top-10}" fill="rgba(221,216,200,0.5)" '
            f'font-size="10" font-family="sans-serif" text-anchor="middle">{lab}</text>'
        )
    # axis lanes
    # bucket events by primary axis (first matching view axis)
    view_ax_set = set(view_axes)
    by_axis = {ax: [] for ax in view_axes}
    for e in events:
        for ax in event_axes(e):
            if ax in view_ax_set:
                by_axis[ax].append(e); break
    for i, ax_id in enumerate(view_axes):
        y = margin_top + i * lane_h + lane_h / 2
        ax = axes_by_id.get(ax_id, {})
        ax_label = ax.get('label', ax_id)
        ax_color = ax.get('color', '#888')
        # lane line
        parts.append(
            f'<line x1="{margin_left}" y1="{y:.1f}" x2="{width-margin_right}" y2="{y:.1f}" '
            f'stroke="rgba(255,255,255,0.06)" stroke-width="1"/>'
            f'<text x="{margin_left-6}" y="{y+3.5:.1f}" fill="{ax_color}" '
            f'font-size="11" font-family="sans-serif" text-anchor="end">{html.escape(ax_label)}</text>'
        )
        # event dots
        for e in by_axis[ax_id]:
            x = x_for(e['year'])
            cat = e.get('category', '')
            color = cat_color.get(cat, '#aaa')
            level = e.get('level', 2)
            r = 4 if level == 1 else (3 if level == 2 else 2.2)
            eid = e.get('id', '')
            title = html.escape(f'{fmt_year_short(e["year"])} · {e.get("zh","")}')
            parts.append(
                f'<a href="#ev-{html.escape(eid)}">'
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{color}" '
                f'stroke="rgba(0,0,0,0.5)" stroke-width="0.5">'
                f'<title>{title}</title></circle></a>'
            )
    parts.append('</svg>')
    return ''.join(parts)


def auto_intro(view, events, lang='zh'):
    """Use curated `intro_zh`/`intro_en` from view if present; else minimal fallback."""
    curated = view.get(f'intro_{lang}')
    if curated:
        return curated
    ys = view['yearStart']; ye = view['yearEnd']
    if lang == 'en':
        def _y(y): return f'{abs(int(y))} BCE' if y < 0 else f'{int(y)}'
        return f'{_y(ys)} to {_y(ye)}.'
    def _y(y): return f'前 {abs(int(y))}' if y < 0 else f'{int(y)}'
    return f'{_y(ys)} 至 {_y(ye)} 年。'

def render_event(e, in_page_axes_to_view, axes_by_id, view):
    h = html.escape
    eid = e.get('id', '')
    year_label = fmt_year(e.get('year'))
    title_zh = h(e.get('zh', ''))
    title_en = h(e.get('en', ''))
    desc_zh = h(e.get('desc_zh', ''))
    desc_en = h(e.get('desc_en', ''))
    img = e.get('image', '')
    cat = h(e.get('category', ''))
    wiki_zh = e.get('wiki_zh') or ''
    wiki_en = e.get('wiki_en') or ''
    asin = e.get('amazon_asin') or ''

    # crossRef can be list or accidentally a string
    xr = e.get('crossRef') or []
    if isinstance(xr, str):
        xr = [xr]

    # Build crossRef pills (dual-lang label)
    pill_html = ''
    if xr:
        pills = []
        for ax_id in xr[:6]:
            ax = axes_by_id.get(ax_id)
            ax_label_zh = h(ax.get('label', ax_id)) if ax else h(ax_id)
            ax_label_en = h(ax.get('label_en') or ax.get('label', ax_id)) if ax else h(ax_id)
            target_view = in_page_axes_to_view.get(ax_id)
            inner = (f'<span class="zh-only">{ax_label_zh}</span>'
                     f'<span class="en-only">{ax_label_en}</span>')
            if target_view:
                pills.append(f'<a class="xref" href="{target_view["id"]}.html">{inner}</a>')
            else:
                pills.append(f'<span class="xref">{inner}</span>')
        pill_html = (f'<div class="xrefs">'
                     f'<span class="xrefs-label zh-only">相關主軸：</span>'
                     f'<span class="xrefs-label en-only">Related axes:</span>'
                     f'{"".join(pills)}</div>')

    # Image with proper Wikimedia Commons credit (uses image_credit if fetched, else fallback)
    img_html = ''
    if img:
        ic = e.get('image_credit') or {}
        # Dedupe Wiki metadata's frequent "X X" doubled author
        def _dedupe(s):
            if not s: return s
            n = len(s)
            if n % 2 == 0 and s[:n//2] == s[n//2:]: return s[:n//2]
            return s
        author = h(_dedupe(ic.get('author', ''))[:80]) if ic.get('author') else ''
        license_name = h(ic.get('license', '')) if ic.get('license') else ''
        license_url = ic.get('license_url') or ''
        source_url = ic.get('source_url') or ''
        if not source_url:
            _, derived = image_credit(img)
            source_url = derived or ''
        # Build credit string
        parts = []
        if author: parts.append(author)
        if license_name:
            if license_url:
                parts.append(f'<a href="{h(license_url)}" target="_blank" rel="noopener">{license_name}</a>')
            else:
                parts.append(license_name)
        if source_url:
            parts.append(f'<a href="{h(source_url)}" target="_blank" rel="noopener">Wikimedia Commons</a>')
        elif not parts:
            parts.append('外部來源 / external source')
        credit_html = ' · '.join(parts)
        img_html = (f'<figure class="event-img">'
                    f'<img loading="lazy" src="{h(img)}" alt="{title_zh} / {title_en}" />'
                    f'<figcaption>'
                    f'<span class="zh-only">圖：{credit_html}</span>'
                    f'<span class="en-only">Image: {credit_html}</span>'
                    f'</figcaption></figure>')

    # In-canvas anchor link
    canvas_anchor = (f'<a class="canvas-jump" href="../index.html?v={h(view["id"])}&year={e.get("year","")}" '
                     f'title="在主時間軸上定位此事件 / Locate on main timeline">'
                     f'<span class="zh-only">📍 在主時間軸定位</span>'
                     f'<span class="en-only">📍 Locate on main timeline</span></a>')

    # External links
    links = [canvas_anchor]
    # Wiki link 語言邏輯：
    #   中文模式 → 同時顯示「中」與「EN」(雙語讀者方便對照)
    #   英文模式 → 只顯示 EN (英文讀者不看中文 wiki)
    # 實作：wiki_zh 用 zh-only(只在中文模式顯示)、wiki_en 不限制(兩種模式都顯示)
    if wiki_zh:
        links.append(f'<a class="zh-only" href="{h(wiki_zh)}" target="_blank" rel="noopener">Wikipedia (中)</a>')
    if wiki_en:
        links.append(f'<a href="{h(wiki_en)}" target="_blank" rel="noopener">Wikipedia (EN)</a>')
    if asin:
        links.append(f'<a href="https://www.amazon.com/dp/{h(asin)}?tag=universetimel-20" target="_blank" rel="noopener sponsored">'
                     f'<span class="zh-only">延伸閱讀 ↗</span>'
                     f'<span class="en-only">Further reading ↗</span></a>')
    links_html = ('<div class="event-links">' + ' · '.join(links) + '</div>') if links else ''

    return f'''
    <article class="event" id="ev-{h(eid)}">
      <header class="event-head">
        <span class="event-year">{year_label}</span>
        <span class="event-cat" data-cat="{cat}">{cat}</span>
      </header>
      <h3>
        <span class="zh-only">{title_zh}</span>
        <span class="en-only">{title_en}</span>
      </h3>
      {img_html}
      <p class="desc desc-zh zh-only">{desc_zh}</p>
      <p class="desc desc-en en-only" lang="en">{desc_en}</p>
      {pill_html}
      {links_html}
    </article>'''

def render_view(view, axes, events, views, filter_cats=None):
    h = html.escape
    label = view.get('label', view['id'])
    label_en = view.get('label_en', '')
    vid = view['id']
    group = view['group']

    ensure_year_bounds(view, events)
    in_scope = filter_events(events, view)
    eras = split_eras(in_scope, view)
    intro_zh = auto_intro(view, in_scope, lang='zh')
    intro_en = auto_intro(view, in_scope, lang='en')
    axes_by_id = {a['id']: a for a in axes}
    cat_color = {c['id']: c.get('color', '#888') for c in (filter_cats or [])}
    canvas_iframe = (
        f'<iframe class="canvas-embed" src="../index.html?v={h(vid)}&embed=1" '
        f'title="{h(label)} / {h(label_en)} · interactive timeline" loading="lazy"></iframe>'
    )

    # Map axis_id -> view that "owns" it (prefer matching id, else any view that includes)
    axes_to_view = {}
    for ax_id in (view.get('axes') or []):
        for v in views:
            if v.get('id') == ax_id:
                axes_to_view[ax_id] = v; break
    # also for crossRef axis ids that point to other views' main axis
    for ax_id in {x for e in in_scope for x in (e.get('crossRef') or []) if isinstance(e.get('crossRef'), list)}:
        if ax_id in axes_to_view: continue
        for v in views:
            if v.get('id') == ax_id:
                axes_to_view[ax_id] = v; break

    # Related views: from axes (excluding self)
    related = []
    seen = set()
    for ax_id in (view.get('axes') or []):
        if ax_id == vid: continue
        v = next((x for x in views if x['id'] == ax_id), None)
        if v and v['id'] not in seen:
            related.append(v); seen.add(v['id'])

    # TOC (dual-lang labels)
    toc_items = ''.join(
        f'<li><a href="#era-{i}">'
        f'<span class="zh-only">{h(lz)}</span>'
        f'<span class="en-only">{h(le)}</span>'
        f' <span class="toc-n">{len(evs)}</span></a></li>'
        for i, (lz, le, evs) in enumerate(eras))

    # Era sections
    era_sections = ''
    for i, (lz, le, evs) in enumerate(eras):
        ev_html = ''.join(render_event(e, axes_to_view, axes_by_id, view) for e in evs)
        era_sections += f'''
    <section class="era" id="era-{i}">
      <h2>
        <span class="zh-only">{h(lz)} <span class="era-n">· {len(evs)} 條事件</span></span>
        <span class="en-only">{h(le)} <span class="era-n">· {len(evs)} events</span></span>
      </h2>
      {ev_html}
    </section>'''

    # Related views (dual-lang label)
    related_html = ''
    if related:
        items = ''.join(
            f'<a class="rel" href="{h(v["id"])}.html">'
            f'<span class="zh-only">{h(v.get("label", v["id"]))}</span>'
            f'<span class="en-only">{h(v.get("label_en") or v.get("label", v["id"]))}</span>'
            f'</a>'
            for v in related)
        related_html = f'''
    <section class="related">
      <h2>
        <span class="zh-only">相關時間軸</span>
        <span class="en-only">Related Timelines</span>
      </h2>
      <p>
        <span class="zh-only">本頁事件涉及以下其他時間軸主題，點擊瀏覽相關脈絡：</span>
        <span class="en-only">This view touches on the following related timelines — click to explore:</span>
      </p>
      <div class="rel-list">{items}</div>
    </section>'''

    canvas_url = f'../index.html?v={h(vid)}'

    title_full = f'{label} / {label_en} · Cosmic History Timeline'
    desc_meta = f'{label_en} ({label}) — full timeline of {len(in_scope)} key events, with bilingual descriptions, images, Wikipedia and further reading. {fmt_year_short(view["yearStart"])} to {fmt_year_short(view["yearEnd"])}.'

    return f'''<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{h(title_full)}</title>
<meta name="description" content="{h(desc_meta)}">
<meta property="og:title" content="{h(title_full)}">
<meta property="og:description" content="{h(desc_meta)}">
<meta property="og:type" content="article">
<link rel="canonical" href="https://www.cosmichistorytimeline.com/views/{h(vid)}.html">
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-9386529087603046" crossorigin="anonymous"></script>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;700;800;900&display=swap" rel="stylesheet">
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  html {{ background:#fff; }}
  body {{
    background:#fff; color:#121212;
    font-family:'Noto Sans TC','Helvetica Neue',Helvetica,Arial,sans-serif;
    font-size:17px; line-height:1.6;
    -webkit-font-smoothing:antialiased; -moz-osx-font-smoothing:grayscale;
  }}
  .container {{ max-width:740px; margin:0 auto; padding:24px 20px 80px; }}
  a {{ color:#052962; text-decoration:none; border-bottom:1px solid #052962; }}
  a:hover {{ color:#c70000; border-bottom-color:#c70000; }}

  /* 頂部 nav */
  .crumb {{
    font-size:12px; color:#707070; font-weight:700;
    text-transform:uppercase; letter-spacing:1px;
    padding-bottom:10px; margin-bottom:24px;
    border-bottom:2px solid #c70000;
  }}
  .crumb a {{ color:#707070; border:none; }}
  .crumb a:hover {{ color:#c70000; }}

  /* 標題 */
  header h1 {{
    font-size:42px; font-weight:900; color:#121212;
    line-height:1.12; letter-spacing:-0.6px;
    margin-bottom:6px;
  }}
  header h1 .en {{
    display:block; font-size:18px; font-weight:400;
    color:#707070; margin-top:8px; letter-spacing:0;
  }}

  /* Lead 段落 */
  .hero {{ margin:14px 0 28px; padding:0; background:none; border:none; }}
  .hero p {{
    font-size:19px; font-weight:500; line-height:1.5;
    color:#444; margin:0;
  }}
  .cta {{
    display:inline-block; margin-top:18px;
    padding:11px 22px; background:#c70000;
    color:#fff !important; font-size:14px; font-weight:700;
    border-radius:9999px; border:none !important;
  }}
  .cta:hover {{ background:#052962; text-decoration:none; }}

  /* Canvas embed 區 */
  .canvas-block {{ margin:32px 0 40px; }}
  .canvas-head {{
    border-top:1px solid #121212; border-bottom:1px solid #ddd;
    padding:8px 0; margin-bottom:14px;
  }}
  .canvas-title {{
    display:inline-block; font-size:11px; font-weight:700;
    color:#c70000; text-transform:uppercase; letter-spacing:1.5px;
    margin-right:14px;
  }}
  .canvas-hint {{ font-size:13px; color:#707070; }}
  .canvas-embed {{
    width:100%; height:560px; display:block;
    border:1px solid #ddd; background:#050810;
  }}
  .canvas-foot {{ margin-top:14px; text-align:center; }}
  .cta-mini {{
    display:inline-block; padding:8px 18px; font-size:13px; font-weight:700;
    color:#052962 !important; border:1px solid #052962 !important;
    border-radius:9999px; background:transparent;
  }}
  .cta-mini:hover {{ background:#052962; color:#fff !important; }}

  /* 版權聲明 */
  .disclosure {{
    margin:24px 0 28px; padding:14px 16px;
    background:#f5f5f5; border-left:3px solid #c70000;
    font-size:13.5px; color:#444; line-height:1.65;
  }}
  .disclosure strong {{ color:#121212; font-weight:700; }}

  /* TOC */
  .toc {{
    margin:24px 0 40px; padding:14px 0;
    border-top:1px solid #ddd; border-bottom:1px solid #ddd;
    background:none;
  }}
  .toc-title {{
    font-size:11px; font-weight:700; color:#c70000;
    text-transform:uppercase; letter-spacing:1.5px;
    margin-bottom:10px;
  }}
  .toc ul {{ list-style:none; display:flex; flex-wrap:wrap; gap:4px 22px; }}
  .toc li {{ font-size:15px; font-weight:600; }}
  .toc li a {{ color:#121212; border:none; }}
  .toc li a:hover {{ color:#c70000; }}
  .toc-n {{ color:#707070; font-size:12px; font-weight:400; margin-left:4px; }}

  /* Era 標題 */
  h2 {{
    font-size:28px; font-weight:900; color:#121212;
    margin:60px 0 22px; padding:14px 0 0;
    border-top:2px solid #121212;
    letter-spacing:-0.3px; line-height:1.2;
  }}
  .era-n {{
    display:block; font-size:13px; font-weight:400;
    color:#707070; margin-top:6px; letter-spacing:0;
  }}

  /* 事件文章 */
  .event {{
    margin:0 0 36px; padding:0 0 28px;
    border-bottom:1px solid #eaeaea;
    background:none; border-left:none; border-radius:0;
  }}
  .event:last-child {{ border-bottom:none; }}
  .event-head {{
    display:flex; align-items:baseline; gap:14px;
    margin-bottom:8px;
  }}
  .event-year {{
    font-size:13px; font-weight:700; color:#c70000;
    letter-spacing:0.5px;
  }}
  .event-cat {{
    font-size:10px; font-weight:700; color:#707070;
    text-transform:uppercase; letter-spacing:1px;
    background:none; padding:0 0 0 10px;
    border-left:2px solid #ddd; border-radius:0;
  }}
  .event h3 {{
    font-size:24px; font-weight:800; color:#121212;
    margin-bottom:14px; line-height:1.25; letter-spacing:-0.2px;
  }}
  .event h3 .en {{
    display:block; font-size:15px; font-weight:400;
    color:#707070; margin-top:4px;
  }}

  .event-img {{ margin:18px 0 18px; }}
  .event-img img {{
    width:100%; max-height:500px; height:auto;
    display:block; border-radius:0;
    background:#f0f0f0; object-fit:contain;
  }}
  .event-img figcaption {{
    margin-top:6px; font-size:12px;
    color:#707070; font-style:normal;
  }}
  .event-img figcaption a {{
    color:#707070; border-bottom:1px dotted #aaa;
  }}
  .event-img figcaption a:hover {{ color:#c70000; border-bottom-color:#c70000; }}

  .desc-zh {{
    font-size:17px; line-height:1.7; color:#121212;
    margin-bottom:12px;
  }}
  .desc-en {{
    font-size:15px; line-height:1.65; color:#555;
    margin-bottom:14px; font-style:italic;
  }}

  /* CrossRef */
  .xrefs {{
    margin-top:16px; padding-top:12px;
    font-size:13px; border-top:1px solid #f0f0f0;
  }}
  .xrefs-label {{
    color:#707070; font-weight:700; margin-right:10px;
    text-transform:uppercase; font-size:11px; letter-spacing:0.8px;
  }}
  .xref {{
    display:inline-block; padding:0;
    margin:0 14px 0 0; background:none; border:none;
    color:#052962; font-size:13px; font-weight:600;
    border-bottom:1px solid #052962; border-radius:0;
  }}
  a.xref:hover {{
    color:#c70000; border-bottom-color:#c70000; background:none;
  }}

  /* 事件 footer 連結 */
  .event-links {{
    margin-top:14px; font-size:13px; color:#707070;
  }}
  .event-links a {{
    color:#052962; border-bottom:1px solid #052962;
  }}
  .event-links a:hover {{ color:#c70000; border-bottom-color:#c70000; }}
  .canvas-jump {{
    color:#c70000 !important; font-weight:700;
    border-bottom-color:#c70000 !important;
  }}

  /* 相關 */
  .related {{
    margin-top:64px; padding-top:28px;
    border-top:2px solid #121212;
  }}
  .related h2 {{
    border:none; padding:0; margin:0 0 12px;
  }}
  .related p {{
    color:#707070; font-size:15px; margin-bottom:18px;
  }}
  .rel-list {{ display:flex; flex-wrap:wrap; gap:10px; }}
  .rel {{
    padding:8px 14px; background:#f5f5f5;
    border:none !important; color:#121212; font-size:14px; font-weight:700;
    border-radius:0; border-bottom:2px solid transparent !important;
  }}
  .rel:hover {{
    background:#fff; color:#c70000;
    border-bottom-color:#c70000 !important; text-decoration:none;
  }}

  /* Footer */
  footer {{
    margin-top:80px; padding-top:24px;
    border-top:1px solid #ddd;
    font-size:12px; color:#707070; line-height:1.7;
    text-align:left;
  }}
  footer a {{
    color:#707070; border-bottom:1px solid #ccc;
  }}
  footer a:hover {{ color:#c70000; border-bottom-color:#c70000; }}

  /* Lang toggle button (top right of crumb) */
  .crumb-bar {{ display:flex; justify-content:space-between; align-items:center; }}
  .lang-toggle {{
    font-size:11px; font-weight:700; letter-spacing:1px;
    color:#707070; border:1px solid #ddd; padding:5px 10px;
    background:#fff; cursor:pointer; text-transform:uppercase;
    border-radius:0;
  }}
  .lang-toggle:hover {{ color:#c70000; border-color:#c70000; }}
  .lang-toggle .on {{ color:#121212; font-weight:800; }}

  /* Single-language display (no zh+en side-by-side) */
  body.lang-zh .en-only {{ display:none !important; }}
  body.lang-en .zh-only {{ display:none !important; }}

  /* AdSense */
  .ad-slot {{
    margin:36px 0; padding:8px 0; min-height:90px;
    display:flex; align-items:center; justify-content:center;
    border-top:1px solid #f0f0f0; border-bottom:1px solid #f0f0f0;
  }}
  .ad-slot::before {{
    content:'Advertisement';
    position:absolute; transform:translateY(-22px);
    font-size:9px; color:#aaa; letter-spacing:1.5px; text-transform:uppercase;
  }}

  /* Mobile */
  @media (max-width:600px) {{
    .container {{ padding:16px 16px 60px; }}
    header h1 {{ font-size:30px; }}
    .hero p {{ font-size:17px; }}
    .event h3 {{ font-size:21px; }}
    h2 {{ font-size:24px; }}
    .canvas-embed {{ height:420px; }}
  }}
</style>
</head>
<body class="lang-en">
<div class="container">
  <nav class="crumb">
    <div class="crumb-bar">
      <div>
        <a href="../index.html"><span class="zh-only">← 主時間軸</span><span class="en-only">← Main Timeline</span></a>
        &nbsp;|&nbsp;
        <a href="../about.html">About</a>
      </div>
      <button class="lang-toggle" id="lang-toggle" type="button" title="Switch language / 切換語言">
        <span id="lang-zh-mark">中</span> / <span id="lang-en-mark" class="on">EN</span>
      </button>
    </div>
  </nav>

  <header>
    <h1>
      <span class="zh-only">{h(label)}</span>
      <span class="en-only">{h(label_en)}</span>
    </h1>
  </header>

  <section class="hero">
    <p class="zh-only">{h(intro_zh)}</p>
    <p class="en-only">{h(intro_en)}</p>
    <a class="cta" href="{canvas_url}">
      <span class="zh-only">在互動時間軸上瀏覽 →</span>
      <span class="en-only">Open in interactive timeline →</span>
    </a>
  </section>

  <section class="canvas-block" aria-label="Interactive timeline">
    <div class="canvas-head">
      <span class="canvas-title zh-only">互動時間軸</span>
      <span class="canvas-title en-only">Interactive Timeline</span>
      <span class="canvas-hint zh-only">本 view 的 {len(view.get('axes') or [])} 條軸線 · 滾輪縮放 · 拖曳平移 · 點事件查看詳情</span>
      <span class="canvas-hint en-only">{len(view.get('axes') or [])} axes · scroll to zoom · drag to pan · click events for detail</span>
    </div>
    {canvas_iframe}
    <div class="canvas-foot">
      <a class="cta-mini" href="{canvas_url}" target="_top">
        <span class="zh-only">放大到完整版（含跨 view 對比、Era 跳躍、搜尋)→</span>
        <span class="en-only">Open full version (cross-view, era jumps, search) →</span>
      </a>
    </div>
  </section>

  <!-- AdSense slot 1: after interactive canvas (mid-content) -->
  <div class="ad-slot">
    <ins class="adsbygoogle"
         style="display:block"
         data-ad-client="ca-pub-9386529087603046"
         data-ad-slot="8876685027"
         data-ad-format="auto"
         data-full-width-responsive="true"></ins>
    <script>(adsbygoogle = window.adsbygoogle || []).push({{}});</script>
  </div>

  <nav class="toc">
    <div class="toc-title zh-only">本頁目錄</div>
    <div class="toc-title en-only">Contents</div>
    <ul>{toc_items}</ul>
  </nav>

  <div class="disclosure">
    <span class="zh-only">
      📌 <strong>內容與授權</strong>：本頁事件說明文字（中英）為 Cosmic History Timeline 編輯整理。
      圖片來自 Wikimedia Commons，作者與授權詳見每張圖下方連結。
      延伸閱讀的 Wikipedia 與 Amazon 連結著作權歸原權利人；Amazon 連結為聯盟連結（不影響你的價格）。
    </span>
    <span class="en-only">
      📌 <strong>Sources & Credits</strong>: Event descriptions (zh / en) are editorial work by Cosmic History Timeline.
      Images are sourced from Wikimedia Commons — author and license shown below each image.
      Wikipedia and Amazon links belong to their respective rights holders; Amazon links are affiliate links (no extra cost to you).
    </span>
  </div>

  {era_sections}

  <!-- AdSense slot 2: end of content (before related-views) -->
  <div class="ad-slot">
    <ins class="adsbygoogle"
         style="display:block"
         data-ad-client="ca-pub-9386529087603046"
         data-ad-slot="8876685027"
         data-ad-format="auto"
         data-full-width-responsive="true"></ins>
    <script>(adsbygoogle = window.adsbygoogle || []).push({{}});</script>
  </div>

  {related_html}

  <footer>
    Cosmic History Timeline ·
    <a href="../index.html"><span class="zh-only">主站</span><span class="en-only">Home</span></a> ·
    <a href="../about.html">About</a> ·
    <a href="../privacy-policy.html">Privacy</a>
    <br>
    <span class="zh-only">事件說明為本站編輯內容，© 2025–2026 Cosmic History Timeline · All rights reserved.</span>
    <span class="en-only">Editorial text by Cosmic History Timeline. © 2025–2026 · All rights reserved.</span>
    <br>
    <span class="zh-only">圖片：Wikimedia Commons（個別作者與授權詳見圖下方連結）· Wikipedia 連結著作權歸原作者</span>
    <span class="en-only">Images: Wikimedia Commons (per-image author / license shown below each image) · Wikipedia text rights belong to original contributors</span>
  </footer>
</div>

<script>
(function() {{
  // Three-way lang sync: URL ?lang= > localStorage (shared with main canvas) > default 'en'
  const KEY = 'cosmic-lang';
  const valid = (l) => l === 'zh' || l === 'en';
  function readLang() {{
    const url = new URLSearchParams(location.search).get('lang');
    if (valid(url)) return url;
    try {{ const ls = localStorage.getItem(KEY); if (valid(ls)) return ls; }} catch(e){{}}
    return 'en';  // 預設英文（目標讀者）
  }}
  function applyLang(l) {{
    document.body.classList.remove('lang-zh', 'lang-en');
    document.body.classList.add('lang-' + l);
    document.documentElement.setAttribute('lang', l === 'zh' ? 'zh-Hant' : 'en');
    const zhMark = document.getElementById('lang-zh-mark');
    const enMark = document.getElementById('lang-en-mark');
    if (zhMark && enMark) {{
      zhMark.classList.toggle('on', l === 'zh');
      enMark.classList.toggle('on', l === 'en');
    }}
    // Pass lang to all internal links (other agg pages, main canvas, iframe)
    document.querySelectorAll('a[href]').forEach(a => {{
      const href = a.getAttribute('href');
      if (!href || href.startsWith('http') || href.startsWith('#')) return;
      // Skip mailto, javascript:, etc
      if (href.startsWith('mailto:') || href.startsWith('javascript:')) return;
      const url = new URL(href, location.href);
      url.searchParams.set('lang', l);
      a.setAttribute('href', url.pathname + url.search + url.hash);
    }});
    // Update iframe src to carry lang too
    document.querySelectorAll('iframe.canvas-embed').forEach(f => {{
      const src = new URL(f.getAttribute('src'), location.href);
      src.searchParams.set('lang', l);
      const next = src.pathname + src.search;
      if (f.getAttribute('src') !== next) f.setAttribute('src', next);
    }});
  }}
  function setLang(l, push) {{
    if (!valid(l)) return;
    try {{ localStorage.setItem(KEY, l); }} catch(e) {{}}
    applyLang(l);
    if (push && history.replaceState) {{
      const url = new URL(location.href);
      url.searchParams.set('lang', l);
      history.replaceState(null, '', url.toString());
    }}
  }}
  const initial = readLang();
  applyLang(initial);
  // sync URL on first load (so URL always shows current lang)
  if (history.replaceState && new URLSearchParams(location.search).get('lang') !== initial) {{
    const url = new URL(location.href);
    url.searchParams.set('lang', initial);
    history.replaceState(null, '', url.toString());
  }}
  const btn = document.getElementById('lang-toggle');
  if (btn) btn.addEventListener('click', () => {{
    const cur = document.body.classList.contains('lang-en') ? 'en' : 'zh';
    setLang(cur === 'en' ? 'zh' : 'en', true);
  }});
}})();

// ── Auto-reload when this HTML file itself is updated on the server ──
(function() {{
  let _pageEtag = null;
  let stopped = false;
  fetch(location.href, {{ method: 'HEAD', cache: 'no-store' }})
    .then(r => {{ _pageEtag = r.headers.get('etag') || r.headers.get('last-modified'); }})
    .catch(() => {{}});
  document.addEventListener('visibilitychange', async () => {{
    if (document.hidden || stopped || !_pageEtag) return;
    try {{
      const r = await fetch(location.href, {{ method: 'HEAD', cache: 'no-store' }});
      const cur = r.headers.get('etag') || r.headers.get('last-modified');
      if (cur && cur !== _pageEtag) {{ stopped = true; location.reload(); }}
    }} catch (_) {{}}
  }});
}})();
</script>
</body>
</html>
'''

# ---------- index (views.html) ----------

def render_index_page(views, view_groups, generated_ids, events, axes_by_id):
    """Render an index page listing every generated agg page, grouped by view-group.
    Output goes to <project>/views.html (root, not in views/ dir)."""
    h = html.escape

    # Group label lookup
    vg_map = {g['id']: g for g in (view_groups or [])}

    # Group views by view.group
    grouped = {}
    for v in views:
        if v['id'] not in generated_ids: continue
        g = v.get('group', 'other')
        grouped.setdefault(g, []).append(v)

    # Sort groups by view_groups[].order
    group_ids = sorted(grouped.keys(), key=lambda g: vg_map.get(g, {}).get('order', 9999))

    # Render each group section
    sections = []
    for gid in group_ids:
        items = grouped[gid]
        if not items: continue
        items.sort(key=lambda v: -len(filter_events(events, v)))  # most events first

        g_label_zh = vg_map.get(gid, {}).get('label', gid)
        g_label_en = vg_map.get(gid, {}).get('label_en', gid)

        rows = []
        for v in items:
            n = len(filter_events(events, v))
            label_zh = h(v.get('label', v['id']))
            label_en = h(v.get('label_en') or v.get('label', v['id']))
            ys = fmt_year_short(v.get('yearStart', 0))
            ye = fmt_year_short(v.get('yearEnd', 0))
            rows.append(f'''
        <a class="idx-row" href="views/{h(v["id"])}.html">
          <div class="idx-label">
            <span class="zh-only">{label_zh}</span>
            <span class="en-only">{label_en}</span>
          </div>
          <div class="idx-meta">{ys} – {ye} · {n} <span class="zh-only">事件</span><span class="en-only">events</span></div>
        </a>''')

        sections.append(f'''
    <section class="idx-group">
      <h2>
        <span class="zh-only">{h(g_label_zh)}</span>
        <span class="en-only">{h(g_label_en)}</span>
        <span class="idx-count">{len(items)}</span>
      </h2>
      <div class="idx-rows">{"".join(rows)}</div>
    </section>''')

    return f'''<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Reading Index · 完整文字版總覽 — Cosmic History Timeline</title>
<meta name="description" content="Cosmic History Timeline reading index: {len(generated_ids)} curated topic timelines covering 13.8 billion years of history. 完整文字版總覽。">
<link rel="canonical" href="https://www.cosmichistorytimeline.com/views.html">
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-9386529087603046" crossorigin="anonymous"></script>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;700;800;900&display=swap" rel="stylesheet">
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  html {{ background:#fff; }}
  body {{
    background:#fff; color:#121212;
    font-family:'Noto Sans TC','Helvetica Neue',sans-serif;
    font-size:16px; line-height:1.5;
    -webkit-font-smoothing:antialiased;
  }}
  .container {{ max-width:980px; margin:0 auto; padding:24px 20px 80px; }}
  a {{ color:#052962; text-decoration:none; }}
  .crumb {{
    display:flex; justify-content:space-between; align-items:center;
    font-size:12px; color:#707070; font-weight:700; text-transform:uppercase; letter-spacing:1px;
    padding-bottom:10px; margin-bottom:24px;
    border-bottom:2px solid #c70000;
  }}
  .crumb a {{ color:#707070; }}
  .crumb a:hover {{ color:#c70000; }}
  .lang-toggle {{
    font-size:11px; font-weight:700; letter-spacing:1px; color:#707070;
    border:1px solid #ddd; padding:5px 10px; background:#fff; cursor:pointer;
    text-transform:uppercase;
  }}
  .lang-toggle:hover {{ color:#c70000; border-color:#c70000; }}
  .lang-toggle .on {{ color:#121212; font-weight:800; }}
  body.lang-zh .en-only {{ display:none !important; }}
  body.lang-en .zh-only {{ display:none !important; }}
  header h1 {{
    font-size:42px; font-weight:900; line-height:1.12; letter-spacing:-0.6px; margin-bottom:8px;
  }}
  .lead {{
    font-size:18px; color:#444; margin-bottom:36px;
  }}
  .idx-group {{ margin-top:48px; }}
  .idx-group h2 {{
    font-size:24px; font-weight:800; padding:10px 0; margin-bottom:14px;
    border-top:2px solid #121212;
    display:flex; align-items:baseline; gap:10px;
  }}
  .idx-count {{ font-size:13px; font-weight:400; color:#707070; }}
  .idx-rows {{
    display:grid; grid-template-columns:repeat(auto-fill, minmax(260px, 1fr));
    gap:0; border-top:1px solid #eaeaea;
  }}
  .idx-row {{
    display:block; padding:14px 12px; border-bottom:1px solid #eaeaea;
    color:#121212; transition:background .1s;
  }}
  .idx-row:hover {{ background:#f9f5ec; color:#c70000; }}
  .idx-label {{ font-size:16px; font-weight:600; margin-bottom:4px; }}
  .idx-meta {{ font-size:12px; color:#707070; }}
  footer {{
    margin-top:80px; padding-top:24px; border-top:1px solid #ddd;
    font-size:12px; color:#707070; line-height:1.7;
  }}
  footer a {{ color:#707070; border-bottom:1px solid #ccc; }}
  .ad-slot {{
    margin:36px 0; padding:8px 0; min-height:90px;
    display:flex; align-items:center; justify-content:center;
    border-top:1px solid #f0f0f0; border-bottom:1px solid #f0f0f0;
  }}
  .ad-slot::before {{
    content:'Advertisement';
    position:absolute; transform:translateY(-22px);
    font-size:9px; color:#aaa; letter-spacing:1.5px; text-transform:uppercase;
  }}
  @media (max-width:600px) {{
    header h1 {{ font-size:30px; }}
    .lead {{ font-size:16px; }}
  }}
</style>
</head>
<body class="lang-en">
<div class="container">
  <nav class="crumb">
    <div>
      <a href="index.html"><span class="zh-only">← 主時間軸</span><span class="en-only">← Main Timeline</span></a>
      &nbsp;|&nbsp;
      <a href="about.html">About</a>
    </div>
    <button class="lang-toggle" id="lang-toggle" type="button" title="Switch / 切換語言">
      <span id="lang-zh-mark">中</span> / <span id="lang-en-mark" class="on">EN</span>
    </button>
  </nav>

  <header>
    <h1>
      <span class="zh-only">完整文字版總覽</span>
      <span class="en-only">Reading Index</span>
    </h1>
  </header>

  <p class="lead">
    <span class="zh-only">{len(generated_ids)} 個主題時間軸，涵蓋 138 億年歷史。每個主題包含中英雙語事件說明、原始圖片、Wikipedia 連結與互動 canvas。</span>
    <span class="en-only">{len(generated_ids)} curated topic timelines covering 13.8 billion years of history. Each topic includes bilingual event descriptions, source images, Wikipedia links, and an interactive canvas embed.</span>
  </p>

  <!-- AdSense slot: index page (between intro and topic list) -->
  <div class="ad-slot">
    <ins class="adsbygoogle"
         style="display:block"
         data-ad-client="ca-pub-9386529087603046"
         data-ad-slot="8876685027"
         data-ad-format="auto"
         data-full-width-responsive="true"></ins>
    <script>(adsbygoogle = window.adsbygoogle || []).push({{}});</script>
  </div>

  {"".join(sections)}

  <footer>
    Cosmic History Timeline ·
    <a href="index.html"><span class="zh-only">主站</span><span class="en-only">Home</span></a> ·
    <a href="about.html">About</a> ·
    <a href="privacy-policy.html">Privacy</a>
    <br>© 2025–2026 Cosmic History Timeline · All rights reserved.
  </footer>
</div>
<script>
(function() {{
  const KEY = 'cosmic-lang';
  const valid = (l) => l === 'zh' || l === 'en';
  function readLang() {{
    const u = new URLSearchParams(location.search).get('lang');
    if (valid(u)) return u;
    try {{ const ls = localStorage.getItem(KEY); if (valid(ls)) return ls; }} catch(e){{}}
    return 'en';
  }}
  function applyLang(l) {{
    document.body.classList.remove('lang-zh','lang-en');
    document.body.classList.add('lang-' + l);
    document.documentElement.setAttribute('lang', l === 'zh' ? 'zh-Hant' : 'en');
    const zh = document.getElementById('lang-zh-mark');
    const en = document.getElementById('lang-en-mark');
    if (zh && en) {{ zh.classList.toggle('on', l==='zh'); en.classList.toggle('on', l==='en'); }}
    document.querySelectorAll('a[href]').forEach(a => {{
      const href = a.getAttribute('href');
      if (!href || href.startsWith('http') || href.startsWith('#')) return;
      if (href.startsWith('mailto:') || href.startsWith('javascript:')) return;
      const url = new URL(href, location.href);
      url.searchParams.set('lang', l);
      a.setAttribute('href', url.pathname + url.search + url.hash);
    }});
  }}
  function setLang(l) {{
    if (!valid(l)) return;
    try {{ localStorage.setItem(KEY, l); }} catch(e){{}}
    applyLang(l);
    if (history.replaceState) {{
      const u = new URL(location.href);
      u.searchParams.set('lang', l);
      history.replaceState(null, '', u.toString());
    }}
  }}
  const initial = readLang();
  applyLang(initial);
  if (history.replaceState && new URLSearchParams(location.search).get('lang') !== initial) {{
    const u = new URL(location.href);
    u.searchParams.set('lang', initial);
    history.replaceState(null, '', u.toString());
  }}
  const btn = document.getElementById('lang-toggle');
  if (btn) btn.addEventListener('click', () => {{
    const cur = document.body.classList.contains('lang-en') ? 'en' : 'zh';
    setLang(cur==='en' ? 'zh' : 'en');
  }});
}})();

// ── Auto-reload when this HTML file itself is updated on the server ──
(function() {{
  let _pageEtag = null;
  let stopped = false;
  fetch(location.href, {{ method: 'HEAD', cache: 'no-store' }})
    .then(r => {{ _pageEtag = r.headers.get('etag') || r.headers.get('last-modified'); }})
    .catch(() => {{}});
  document.addEventListener('visibilitychange', async () => {{
    if (document.hidden || stopped || !_pageEtag) return;
    try {{
      const r = await fetch(location.href, {{ method: 'HEAD', cache: 'no-store' }});
      const cur = r.headers.get('etag') || r.headers.get('last-modified');
      if (cur && cur !== _pageEtag) {{ stopped = true; location.reload(); }}
    }} catch (_) {{}}
  }});
}})();
</script>
</body>
</html>
'''


# ---------- sitemap.xml ----------

def render_sitemap(generated_ids):
    """Auto-generate sitemap.xml covering canvas main + agg index + 79 agg pages.
    Each agg page gets hreflang annotations for zh-Hant and en variants (?lang=...)."""
    today = date.today().isoformat()
    BASE = 'https://cosmichistorytimeline.com'

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"',
        '        xmlns:xhtml="http://www.w3.org/1999/xhtml">',
    ]

    def emit(loc, freq, prio, hreflang=False):
        lines.append('  <url>')
        lines.append(f'    <loc>{loc}</loc>')
        lines.append(f'    <lastmod>{today}</lastmod>')
        lines.append(f'    <changefreq>{freq}</changefreq>')
        lines.append(f'    <priority>{prio}</priority>')
        if hreflang:
            lines.append(f'    <xhtml:link rel="alternate" hreflang="x-default" href="{loc}"/>')
            lines.append(f'    <xhtml:link rel="alternate" hreflang="zh-Hant" href="{loc}?lang=zh"/>')
            lines.append(f'    <xhtml:link rel="alternate" hreflang="en" href="{loc}?lang=en"/>')
        lines.append('  </url>')

    # Main + meta pages
    emit(BASE + '/',                    'weekly',  '1.0')
    emit(BASE + '/views.html',          'weekly',  '0.9', hreflang=True)
    emit(BASE + '/about.html',          'monthly', '0.5')
    emit(BASE + '/privacy-policy.html', 'yearly',  '0.3')

    # 79 agg pages — bilingual hreflang for international SEO
    for vid in sorted(generated_ids):
        emit(f'{BASE}/views/{vid}.html', 'monthly', '0.8', hreflang=True)

    lines.append('</urlset>')
    return '\n'.join(lines) + '\n'


# ---------- main ----------

def main():
    args = sys.argv[1:]
    if not args:
        print('usage:')
        print('  python generate-pages.py <view_id>          # one view')
        print('  python generate-pages.py --all [min_events] # batch all (default min=5)')
        sys.exit(1)

    d = load()
    out_dir = ROOT / 'views'
    out_dir.mkdir(parents=True, exist_ok=True)

    if args[0] == '--all':
        try:
            min_events = int(args[1]) if len(args) > 1 else 5
        except ValueError:
            min_events = 5
        ok = skipped = 0
        skip_reasons = []
        generated_ids = []
        for v in d['views']:
            n = len(filter_events(d['events'], v))
            if n < min_events:
                skipped += 1
                skip_reasons.append(f'  - skip {v["id"]:25s} ({n} events < {min_events})')
                continue
            html_out = render_view(v, d['axes'], d['events'], d['views'], d.get('filter_cats'))
            out_path = out_dir / f'{v["id"]}.html'
            out_path.write_text(html_out, encoding='utf-8')
            ok += 1
            generated_ids.append(v['id'])
            print(f'  + {v["id"]:25s} {n:>4} events  ({len(html_out):,} chars)')
        # Also write the index page (views.html at project root)
        axes_by_id = {a['id']: a for a in d['axes']}
        index_html = render_index_page(
            d['views'], d.get('view_groups'), set(generated_ids), d['events'], axes_by_id)
        index_path = ROOT / 'views.html'
        index_path.write_text(index_html, encoding='utf-8')
        print(f'\n  + views.html (index of {len(generated_ids)} pages)')

        # Auto-generate sitemap.xml (canvas + index + 79 agg with hreflang)
        sitemap = render_sitemap(set(generated_ids))
        (ROOT / 'sitemap.xml').write_text(sitemap, encoding='utf-8')
        print(f'  + sitemap.xml ({len(generated_ids) + 4} URLs · hreflang on agg pages)')

        print()
        for r in skip_reasons: print(r)
        print(f'\nbatch done: {ok} generated + 1 index + sitemap, {skipped} skipped')
        return

    # single view
    vid = args[0]
    v = next((x for x in d['views'] if x.get('id') == vid), None)
    if not v:
        print(f'view not found: {vid}'); sys.exit(1)
    html_out = render_view(v, d['axes'], d['events'], d['views'], d.get('filter_cats'))
    out_path = out_dir / f'{vid}.html'
    out_path.write_text(html_out, encoding='utf-8')
    n_events = len(filter_events(d['events'], v))
    print(f'wrote {out_path}')
    print(f'  events: {n_events}  output: {len(html_out):,} chars')

if __name__ == '__main__':
    main()
