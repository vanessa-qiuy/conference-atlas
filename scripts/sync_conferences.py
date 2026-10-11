#!/usr/bin/env python3
"""Conservative, source-specific academic conference monitor.

Reads officially curated conference records, checks only whitelisted URLs, and
updates explicit deadlines only when an event-specific pattern matches.
Suspicious changes are queued for manual review instead of silently published.
Also discovers likely new year-edition links into data/candidates.json.
Run via GitHub Actions (daily) or manually. No AI key required.
"""
from __future__ import annotations
import argparse
import json
import re
import sys
import time
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urlparse, urljoin, urldefrag
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data' / 'conferences.json'
HEADERS = {'User-Agent': 'AcademicConferenceAtlasBot/1.0 (+https://github.com/; official-source research monitoring)'}
ALLOWED = {'www.irspm.org', 'www.ippapublicpolicy.org', 'www.pmranet.org', 'www.appam.org', 'www.aspanet.org', 'aspanet.org', 'aapa.asia', '2027.iaia.org', 'www.nispa.org', 'ecpr.eu', 'events.ecpr.eu', 'www.ipsa.org', 'wc2027.ipsa.org', 'apsanet.org', 'www.arnova.org', 'members.arnova.org', 'www.egu.eu', 'iias.timtul.es', 'iias-iisa.org', 'www.iias-iisa.org', 'iaee.org'}
MONTH = r'(?:January|February|March|April|May|June|July|August|September|October|November|December)'
DATE = rf'(?:{MONTH}\s+\d{{1,2}}(?:st|nd|rd|th)?\s*,?\s*20\d{{2}}|\d{{1,2}}(?:st|nd|rd|th)?\s+{MONTH}\s*,?\s*20\d{{2}})'


def parse_date(value: str) -> str | None:
    s = re.sub(r'(?<=\d)(st|nd|rd|th)\b', '', value, flags=re.I)
    s = re.sub(r'\s+', ' ', s.replace(',', ' ')).strip()
    for fmt in ('%B %d %Y', '%d %B %Y'):
        try:
            return datetime.strptime(s, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def normalized_text(html: str) -> str:
    soup = BeautifulSoup(html, 'html.parser')
    for node in soup(['style', 'script', 'nav', 'footer', 'noscript']):
        node.decompose()
    return re.sub(r'\s+', ' ', ' '.join(soup.stripped_strings)).strip()


def extract_near(text: str, anchor: str, pattern: str, window: int = 320):
    """Find date after an exact descriptive anchor in a bounded context."""
    match = re.search(anchor, text, flags=re.I)
    if not match:
        return None
    section = text[match.end():match.end() + window]
    x = re.search(pattern, section, flags=re.I)
    if not x:
        return None
    return parse_date(x.group('date'))


def field_rules(conf_id: str, text: str) -> dict[str, str]:
    """Do not generalize across conferences: explicit anchors prevent year mixups."""
    out = {}
    def add(field, date_value):
        if date_value:
            out[field] = date_value
    if conf_id == 'irspm-2027':
        add('deadline:Abstract', extract_near(text, r'will close on|close(?:s)? on', rf'(?P<date>{DATE})', 110))
    elif conf_id == 'icpp8-2027':
        # Official schedule uses two distinct calls; preserve BOTH dates.
        add('deadline:Panel', extract_near(text, r'Call for panels', rf'{DATE}\s*[-–]\s*(?P<date>{DATE})', 130))
        add('deadline:Paper', extract_near(text, r'Call for papers', rf'{DATE}\s*[-–]\s*(?P<date>{DATE})', 130))
        add('registration:closes', extract_near(text, r'\bRegistration\b', rf'{DATE}\s*[-–]\s*(?P<date>{DATE})', 130))
    elif conf_id == 'aspa-2027':
        add('deadline:Proposal', extract_near(text, r'deadline extended to|proposals (?:are )?due', rf'(?P<date>{DATE})', 90))
    elif conf_id == 'iaia-2027':
        # The IAIA site publishes '2 November 2026: Deadline for submission...' etc.
        for field, phrase in [('deadline:Abstract', r'deadline for submission of paper or poster abstract'),
                              ('registration:earlyBird', r'presenter registration deadline\s*&\s*early bird rate deadline'),
                              ('registration:closes', r'final registration\s*&\s*payment deadline')]:
            p = re.search(rf'(?P<date>{DATE})\s*:\s*.{{0,12}}{phrase}', text, flags=re.I)
            add(field, parse_date(p.group('date')) if p else None)
    elif conf_id == 'aapa-2026':
        p = re.search(rf'(?P<date>{DATE})\s*\|\s*Registration and payment deadline',text,re.I)
        add('registration:closes',parse_date(p.group('date')) if p else None)
    elif conf_id == 'nispacee-2027':
        add('deadline:Paper proposal / Abstract', extract_near(text,r'paper proposals submitted within the round of applications,?',rf'by\s+(?P<date>{DATE})',180))
        add('registration:earlyBird', extract_near(text,r'early on-line registration deadline',rf'(?P<date>{DATE})',60))
    elif conf_id == 'ecpr-gc-2027':
        add('deadline:Section', extract_near(text, r'Call for Sections', rf'{DATE}\s*[-–]\s*(?P<date>{DATE})',130))
        add('deadline:Panel / Paper', extract_near(text, r'Call for full Panels and individual Papers', rf'{DATE}\s*[-–]\s*(?P<date>{DATE})',140))
    elif conf_id == 'ecpr-js-2027':
        add('deadline:Workshop', extract_near(text,r'Call for Workshops',rf'{DATE}\s*[-–]\s*(?P<date>{DATE})',140))
        add('deadline:Paper proposal', extract_near(text,r'Call for Papers',rf'{DATE}\s*[-–]\s*(?P<date>{DATE})',130))
    elif conf_id == 'ipsa-2027':
        # Only extract if the target date is explicitly tied to submission, not event dates.
        add('deadline:Paper', extract_near(text,r'Paper and Closed Panel Submission Deadline\s*:',rf'(?P<date>{DATE})',60))
        add('deadline:Closed panel',extract_near(text,r'Paper and Closed Panel Submission Deadline\s*:',rf'(?P<date>{DATE})',60))
    elif conf_id in ('iaee-europe-2027','iaee-intl-2027'):
        add('deadline:Abstract', extract_near(text,r'Abstract Submission Deadline\s*:',rf'(?P<date>{DATE})',90))
        add('registration:earlyBird', extract_near(text,r'(?:Presenters[’\']|Presenters)\s*&\s*Early Bird Registration Deadline\s*:',rf'(?P<date>{DATE})',110))
    elif conf_id == 'appam-2026':
        # Formatted pricing table is not regular enough to reliably update automatically.
        pass
    return out


def check_robots(session: requests.Session, url: str, cache: dict) -> bool:
    p = urlparse(url)
    origin=f'{p.scheme}://{p.netloc}'
    if origin not in cache:
        try:
            response = session.get(origin + '/robots.txt', timeout=12, headers=HEADERS)
            if response.status_code == 404:
                cache[origin] = None
            elif response.ok:
                robot = RobotFileParser()
                robot.parse(response.text.splitlines())
                cache[origin] = robot
            else:
                cache[origin] = 'unknown'
        except requests.RequestException:
            cache[origin] = 'unknown'
    rule = cache[origin]
    return rule is None or (rule != 'unknown' and rule.can_fetch(HEADERS['User-Agent'],url))


def safe_fetch(session: requests.Session, url: str, robots: dict):
    u=urlparse(url)
    if u.scheme != 'https' or u.hostname not in ALLOWED:
        raise ValueError('Non-whitelisted source URL refused: ' + url)
    if not check_robots(session,url,robots):
        raise PermissionError('Robots unavailable or disallowed: '+url)
    response=session.get(url,timeout=22,headers=HEADERS,allow_redirects=True)
    response.raise_for_status()
    final=urlparse(response.url)
    if final.scheme!='https' or final.hostname not in ALLOWED:
        raise ValueError('Source redirected outside the official host allowlist')
    if len(response.content)>4*1024*1024:
        raise ValueError('Source size limit exceeded')
    if 'text/html' not in response.headers.get('Content-Type',''):
        raise ValueError('HTML expected; PDF support is not part of v1')
    return response.text


def get_current(conf,field):
    if field.startswith('deadline:'):
        kind=field.split(':',1)[1]
        return next((d.get('date') for d in conf.get('deadlines',[]) if d.get('type')==kind),None)
    return conf.get('registration',{}).get(field.split(':')[1])


def set_current(conf,field,value):
    if field.startswith('deadline:'):
        kind=field.split(':',1)[1]
        for d in conf.get('deadlines',[]):
            if d.get('type')==kind:
                d['date']=value
                return
    elif field.startswith('registration:'):
        conf['registration'][field.split(':')[1]]=value


def apply_updates(conf,found,asof,change_log,pending):
    for field,value in found.items():
        prior=get_current(conf,field)
        if not prior or prior==value:
            continue
        shift=abs((date.fromisoformat(value)-date.fromisoformat(prior)).days)
        entry={'conferenceId':conf['id'],'field':field,'previous':prior,'observed':value,'officialSource':conf['source'],'checkedAt':asof}
        if shift<=45:
            set_current(conf,field,value)
            conf['verifiedAt']=asof
            entry['decision']='auto-applied (explicit source-specific rule)'
            change_log.append(entry)
        else:
            entry['decision']='manual review (change >45 days)'
            pending.append(entry)


def discover_candidates(soup,source_url,known_ids):
    found=[]
    for link in soup.find_all('a',href=True):
        href=urldefrag(urljoin(source_url,link['href']))[0]
        parsed=urlparse(href)
        if parsed.scheme!='https' or parsed.hostname not in ALLOWED:
            continue
        name=' '.join(link.stripped_strings)
        combined=name+' '+parsed.path
        if not re.search(r'(?i)(annual conference|conference 20\d\d|202[6-9].{0,12}conference|icpp\d|pmrc 20\d\d|irspm 20\d\d|call for (abstracts|papers|panels))',combined):
            continue
        yrs=re.findall(r'20(?:2[6-9]|3\d)',combined)
        if not yrs:
            continue
        if len(name)>145: name=name[:145]
        found.append({'name':name or '(unnamed conference link)','year':max(map(int,yrs)),'url':href,'discoveredFrom':source_url,'status':'unverified candidate'})
    return found


def save_data(doc,changes,pending,candidates,dry):
    if dry:return
    DATA.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (ROOT/'data/conferences.js').write_text('window.ATLAS_DATA = '+json.dumps(doc,ensure_ascii=False,indent=2)+';\n',encoding='utf-8')
    (ROOT/'data/pending_changes.json').write_text(json.dumps(pending,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    (ROOT/'data/change_log.json').write_text(json.dumps(changes,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    (ROOT/'data/candidates.json').write_text(json.dumps(candidates,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--dry-run',action='store_true',help='do not modify any files')
    ap.add_argument('--fixtures',type=Path,help='Use local <conference-id>.html test snapshots; makes zero network calls')
    args=ap.parse_args()
    doc=json.loads(DATA.read_text(encoding='utf-8'))
    previous=json.loads((ROOT/'data/change_log.json').read_text()) if (ROOT/'data/change_log.json').exists() else []
    pending=json.loads((ROOT/'data/pending_changes.json').read_text()) if (ROOT/'data/pending_changes.json').exists() else []
    old_candidates=json.loads((ROOT/'data/candidates.json').read_text()) if (ROOT/'data/candidates.json').exists() else []
    candidates={p['url']:p for p in old_candidates}
    today=datetime.now(timezone.utc).date().isoformat()
    session=requests.Session()
    robots={}
    okay=0
    for conference in doc['conferences']:
        source=conference['source']
        try:
            if args.fixtures:
                html=(args.fixtures / f"{conference['id']}.html").read_text(encoding='utf-8')
            else:
                html=safe_fetch(session,source,robots)
            text=normalized_text(html)
            if len(text)<180:raise ValueError('Unexpectedly short source page')
            proposed=field_rules(conference['id'],text)
            before=len(previous)
            apply_updates(conference,proposed,today,previous,pending)
            soup=BeautifulSoup(html,'html.parser')
            for candidate in discover_candidates(soup,source,set()):
                candidates.setdefault(candidate['url'],candidate)
            conference['lastCheckedAt']=today
            okay+=1
            print(f"OK {conference['id']}: {len(proposed)} recognized fields, {len(previous)-before} date changes")
        except (requests.RequestException,PermissionError,ValueError,OSError) as exc:
            print(f"SKIP {conference['id']}: {str(exc)[:200]}",file=sys.stderr)
        if not args.fixtures:time.sleep(1.2)
    # Deduplicate pending by conference + field + observed date
    p={(e['conferenceId'],e['field'],e['observed']):e for e in pending}
    pending=list(p.values())
    if okay:
        save_data(doc,previous,pending,list(candidates.values()),args.dry_run)
    print(f'Checked {okay}/{len(doc["conferences"])} official sources. {len(pending)} pending reviews. {len(candidates)} discoverable candidate URLs.')
    return 0 if okay else 1

if __name__=='__main__':sys.exit(main())
