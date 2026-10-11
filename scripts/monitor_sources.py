#!/usr/bin/env python3
"""Watch known official conference pages for substantive announcement changes.

No inferred deadline is ever published from this generic watcher. Instead, new
links and changed dated passages are queued for human review. Safe to schedule
because only explicitly configured/approved organizer hosts are fetched.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import requests
from sync_conferences import ROOT, ALLOWED, HEADERS, normalized_text, safe_fetch, discover_candidates

REGISTRY=ROOT/'data/monitor_sources.json'
STATE=ROOT/'data/source_watch_state.json'
CHANGES=ROOT/'data/source_changes.json'
ERRORS=ROOT/'data/source_health.json'
CANDIDATES=ROOT/'data/candidates.json'
DATE_WORDS=re.compile(r'(?i)(call for|abstract|deadline|paper|proposal|panel|register|registration|202[6-9]|conference|meeting|annual)')
DATE_DIGITS=re.compile(r'20(?:2[6-9]|3\d)|\b\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)',re.I)

def relevant_passages(html: str) -> list[str]:
    """Stable, human-readable snippets; skip footer and navigation boilerplate."""
    soup=BeautifulSoup(html,'html.parser')
    for part in soup(['script','style','footer','nav','noscript','header']):part.decompose()
    seen=set();out=[]
    for tag in soup.select('h1,h2,h3,p,li,td'):
        text=' '.join(tag.stripped_strings)
        if len(text)<25 or len(text)>650:continue
        if not (DATE_WORDS.search(text) and DATE_DIGITS.search(text)):continue
        key=' '.join(text.lower().split())
        if key in seen:continue
        seen.add(key);out.append(text[:350])
        if len(out)>=45:break
    return out

def fingerprint(items):
    return hashlib.sha256('\n'.join(items).encode('utf-8')).hexdigest()

def changed_snippets(old,new):
    previous=set(old)
    return [part for part in new if part not in previous][:12]

def run(fixtures:Path|None=None,dry_run=False):
    sources=json.loads(REGISTRY.read_text(encoding='utf-8'))
    state=json.loads(STATE.read_text(encoding='utf-8')) if STATE.exists() else {}
    changes=json.loads(CHANGES.read_text(encoding='utf-8')) if CHANGES.exists() else []
    health=json.loads(ERRORS.read_text(encoding='utf-8')) if ERRORS.exists() else {}
    existing=json.loads(CANDIDATES.read_text(encoding='utf-8')) if CANDIDATES.exists() else []
    candidate_by_url={c['url']:c for c in existing}
    dataset=json.loads((ROOT/'data/conferences.json').read_text(encoding='utf-8'))
    known_links={c[key] for c in dataset['conferences'] for key in ('source','website') if c.get(key)}
    now=datetime.now(timezone.utc).isoformat(timespec='seconds')
    session=requests.Session();robots={};n_ok=0
    for entry in sources:
        key=entry['id'];url=entry['url']
        try:
            if urlparse(url).hostname not in ALLOWED: raise ValueError('Official URL host not approved')
            html=(fixtures/f'{key}.html').read_text(encoding='utf-8') if fixtures else safe_fetch(session,url,robots)
            sections=relevant_passages(html)
            if not sections:raise ValueError('No dated passages available; preserving previous state')
            digest=fingerprint(sections)
            old=state.get(key)
            if old and old.get('sha256')!=digest:
                parts=changed_snippets(old.get('passages',[]),sections)
                if parts:
                    identifier=hashlib.sha256((key+'|'+digest).encode()).hexdigest()[:16]
                    if not any(c.get('changeId')==identifier for c in changes):
                        changes.append({'changeId':identifier,'sourceId':key,'organizer':entry['organization'],'url':url,'observedAt':now,'status':'needs_manual_review','newPassages':parts,'note':'Changes are NOT published to the conference database automatically.'})
            state[key]={'url':url,'organization':entry['organization'],'sha256':digest,'passages':sections,'lastSuccessfulCheck':now}
            health[key]={'status':'ok','lastCheckedAt':now,'passages':len(sections),'url':url}
            soup=BeautifulSoup(html,'html.parser')
            for c in discover_candidates(soup,url,set()):
                if c['url'] not in known_links and c['url'] not in candidate_by_url:
                    candidate_by_url[c['url']]=c
            n_ok+=1
            print('OK',key,'tracked excerpts',len(sections))
        except (requests.RequestException,PermissionError,ValueError,OSError) as exc:
            health[key]={'status':'not_checked','lastCheckedAt':now,'reason':str(exc)[:200],'url':url}
            print('SKIP',key,str(exc)[:150])
    if not dry_run:
        for file,content in [(STATE,state),(CHANGES,changes),(ERRORS,health),(CANDIDATES,list(candidate_by_url.values()))]:
            file.write_text(json.dumps(content,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'Watched {n_ok}/{len(sources)} official pages; {len(changes)} cumulative review tasks; {len(candidate_by_url)} new-edition candidates.')
    return 0 if n_ok else 1

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--fixtures',type=Path,help='Local <source-id>.html files (no network)')
    p.add_argument('--dry-run',action='store_true')
    a=p.parse_args()
    raise SystemExit(run(a.fixtures,a.dry_run))
