#!/usr/bin/env python3
"""Bundle approved conference editions and a read-only monitoring summary.

The site works on GitHub Pages and as a local file without API calls. Review
candidates are never promoted to approved conference editions automatically.
"""
from __future__ import annotations
import json
from pathlib import Path
from urllib.parse import urlparse
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'

def read_json(name: str, fallback):
    path = DATA / name
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else fallback

def build_status(registry, health, candidates, pending, changed):
    sources = []
    for item in registry:
        health_item = health.get(item['id'], {})
        sources.append({
            'id': item['id'],
            'organization': item['organization'],
            'url': item['url'],
            'state': health_item.get('status', 'not_checked'),
            'lastCheckedAt': health_item.get('lastCheckedAt'),
            'passages': health_item.get('passages', 0),
            'note': str(health_item.get('reason', ''))[:180]
        })
    # Keep all potential leads visible, but explicitly unverified. Do not infer
    # whether a candidate represents a distinct new conference edition.
    links = []
    seen = set()
    for entry in candidates:
        url = entry.get('url', '')
        if url in seen or urlparse(url).scheme != 'https':
            continue
        seen.add(url)
        label = str(entry.get('name') or 'Untitled link').strip()[:145]
        looks_like_utility = any(word in label.lower() for word in ('add to calendar', 'print', 'guidelines', 'resources')) or urlparse(url).path.lower().endswith('.ics')
        links.append({'title': label, 'year': entry.get('year'), 'url': url,
                      'discoveredFrom': entry.get('discoveredFrom', ''),
                      'reviewType': 'Utility or related resource' if looks_like_utility else 'Potential conference link'})
    dates = []
    for p in pending:
        dates.append({'conferenceId':p.get('conferenceId'),'field':p.get('field'),
                      'previous':p.get('previous'),'observed':p.get('observed'),
                      'url':p.get('officialSource'),'checkedAt':p.get('checkedAt')})
    announcements = []
    for item in changed:
        announcements.append({'organizer':item.get('organizer'),'observedAt':item.get('observedAt'),
                              'url':item.get('url'),'passageCount':len(item.get('newPassages',[])),
                              'status':item.get('status','needs_manual_review')})
    latest = max((s['lastCheckedAt'] for s in sources if s['lastCheckedAt']), default=None)
    return {'lastMonitoringCheck': latest,
            'sourceCount':len(sources),
            'sourceSuccessCount':sum(s['state']=='ok' for s in sources),
            'sources':sources, 'candidateLinks':links,
            'pendingDates':dates,'pendingAnnouncements':announcements,
            'notice':'Read-only monitoring snapshot. Unverified candidate URLs are not conference editions.'}

def export():
    catalogue=read_json('conferences.json', {'conferences':[], 'meta':{}})
    ids=[c['id'] for c in catalogue['conferences']]
    if len(ids)!=len(set(ids)):
        raise ValueError('Duplicate conference IDs detected')
    catalogue['status'] = build_status(
        read_json('monitor_sources.json', []), read_json('source_health.json', {}),
        read_json('candidates.json', []), read_json('pending_changes.json', []),
        read_json('source_changes.json', []))
    (DATA / 'conferences.js').write_text('window.ATLAS_DATA = '+json.dumps(catalogue,ensure_ascii=False,indent=2)+';\n',encoding='utf-8')
    return len(ids)

if __name__=='__main__':
    print(f'Exported {export()} reviewed conference editions and a monitoring summary')
