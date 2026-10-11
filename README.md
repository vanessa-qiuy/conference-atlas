# Conference Atlas

A source-first international academic conference tracker for public policy, public administration and public management. **Working static MVP with four pages: Home / Explore / Calendar / Map.**

![Design direction](assets/hero-academia.svg)

## Use it

**Simplest:** double-click `index.html` in a browser. The conference database is bundled in `data/conferences.js` so no local server or internet is needed for the interface.

Or run locally:

```bash
cd conference-atlas
python3 -m http.server 8000
# Open http://localhost:8000
```

Included:

- Search across conference name, organizer, country, location, theme, fields, and research topics.
- Filters by discipline, year, region, and submission status; sorting; table/card modes.
- Saved conferences in browser local storage (local device only).
- Month calendar with submission / registration / conference / notification milestones.
- Interactive world map with **city-level** conference pins, active location cards, search, year/field/region filters, saved-only mode, zoom, drag-to-pan, and focus buttons for Europe, North America and Asia–Pacific. No maps API, third-party tiles, location permissions, or internet connection required for the map.
- Calendar `.ics` download for an individual conference or all milestones.
- Dedicated details drawer with venue, duration, theme, published deadlines, actual lead time (days before the conference), source URL and last curated date.
- Responsive English UI with polished illustration and no JavaScript build tool or server requirement.

## What is verified and what isn't

Twenty-one curated **conference editions**, NOT hundreds of events. Records are based on official organizer pages and were reviewed on **2026-10-12**. Unknown deadlines are deliberately null / “Not announced.” These are historical seed values; opening the static page does **not** itself fetch live content. Submission deadlines and registration dates may change. Links to official sources accompany each record. **Check cutoff time zones and organizer rules directly.**

The map uses approximate **city centres**, not individual university or convention-centre coordinates. The base map is derived from Natural Earth low-resolution public-domain geography, packaged as `assets/world-map.svg`. Map `geo.lat` / `geo.lon` coordinates are authored manually in the JSON for each edition; do not reuse these as precise venues. If you add a conference edition, populate `geo` with supported city coordinates and `precision: "city"` for the map marker to appear.

The internal dashboard number is actual conference-edition count (not marketing estimates). All data and source URLs can be edited in `data/conferences.json` and synchronized to the browser JS via the script described below.

## Automated official-source checks

Python parser checks known source URLs, respects `robots.txt`, identifies **only conference-specific** patterns (IRSPM, ICPP, IAIA, ASPA, AAPA, ECPR, IPSA, NISPAcee, IAEE), updates changed explicitly verifiable deadlines within a cautious 45-day range, and sends larger/unusual changes to manual review. Other conference pages are monitored for accessibility and official announcements, but not all are date-parsed automatically. HTML links suggesting new editions go to a candidate list, **never automatically added as confirmed conferences**.

```bash
python3 -m pip install -r requirements.txt
python3 scripts/sync_conferences.py --dry-run # preview checks, no saved changes
python3 scripts/sync_conferences.py           # update supported date fields when verified
python3 scripts/monitor_sources.py --dry-run    # preview official-site changes
python3 scripts/monitor_sources.py             # log detected changes for review
```

Outputs:

- `data/conferences.json`: canonical structured data
- `data/conferences.js`: browser-ready generated copy
- `data/change_log.json`: applied changes
- `data/pending_changes.json`: unusual/ambiguous changes awaiting verification
- `data/candidates.json`: new-edition links that still need editorial review
- `data/source_changes.json`: date-related passage changes from 14 official organization/event pages, queued for review
- `data/source_watch_state.json`: reference snippets and fingerprints for change detection
- `data/source_health.json`: source check status, including blocked / unreachable pages
- `data/monitor_sources.json`: authoritative website monitoring registry

If there is no network access, the script will report **SKIP** and preserve the old dataset. It does not fabricate or guess values from past conference cycles, aggregate sites, or 2026/2027 mixed pages. Source page checks can fail due to robots restrictions. A lastCheckedAt value means fetched, not re-verified by a person.

**Limitations (MVP):** no PDF parsing, no login-gated scraping, no reliable extraction from arbitrary unstructured sites, no AI-assisted event discovery, no email push notifications, and no browser-side live synchronization. Multi-page sites may need a new specific parser rule before they can update dates automatically. Some official websites block bots. This design prioritizes correctness over completeness.

## Deploy to GitHub Pages and keep it current

This project uses **GitHub Actions as the Pages publishing source** rather than "Deploy from a branch." This is intentional: GitHub does not rebuild branch-based Pages when `GITHUB_TOKEN` commits new data. The scheduled refresh workflow **deploys the refreshed static files directly in the same run**, which avoids stale Pages content.

1. Create a **public** repo named `conference-atlas` (recommended for GitHub Free) with no starter README; upload the **contents** of this project at repository root. The root must contain `index.html`, `app.js`, `data/`, `assets/` and `.github/workflows/refresh.yml`. Do not upload the ZIP as a single file or nest the project within a `conference-atlas/` subfolder.
2. Repository **Settings → Pages → Build and deployment → Source → GitHub Actions**.
3. Repository **Settings → Actions → General → Workflow permissions → Read and write permissions** (if selectable; repository/org policies may restrict this). Check that Actions are enabled.
4. **Actions → Refresh conference data and deploy website → Run workflow** (branch `main`) to run manually. An initial push on `main` also triggers a build without doing a network scrape.
5. After a successful green run, go to **Settings → Pages → Visit site**, typically `https://USERNAME.github.io/conference-atlas/`. Initial deployment may take a few minutes.
6. The workflow runs daily around **02:17 UTC / 10:17 Singapore** (best-effort). It checks configured official sources, commits eligible changes in `data/`, and deploys a fresh site from the same run. Review `data/pending_changes.json` and `data/candidates.json` before promoting any uncertain announcements to the curated database.

This version requires no PAT, external database, API key or separate Vercel account. GitHub Pages hosts static HTML/CSS/JavaScript; the Python monitor runs in GitHub Actions, not in visitors' browsers. The website contains a snapshot of the curated database, not continuous real-time data. Records can be blocked by source websites or await manual verification.

## Editing the catalogue

Each conference edition has a unique `id` and `year`, separate deadline records by `type`, and direct source links. Treat missing data as `null` rather than predicting dates. After editing the JSON manually, rebuild browser data with:

```bash
python3 scripts/export_data.py
```

## Test

```bash
python3 -m unittest discover -s tests -v
```

## Rights

Website code, SVG artwork and editorial components are made for this prototype. Names of conferences and organizers belong to their respective organizations. No third-party conference logo or copyrighted stock imagery is bundled. The world geography is based on Natural Earth public-domain data (naturalearthdata.com), bundled locally as an SVG.

## Version 2 map integration

The map and filters use the **same** `data/conferences.json` / `data/conferences.js` as the directory and calendar, so adding editions updates every view after running `python scripts/export_data.py`. The map does not auto-discover or geocode new cities: editors must check coordinates before publication. Its initial data coverage remains **21 curated conference editions**, and the Python scraper rules remain limited as described above.

Map tests run alongside the existing parser tests with `python3 -m unittest discover -s tests -v`. Public event information is credited to its original official source in the dataset.

## Version 3: Style A map readability update

The interactive map now uses a soft-academic high-contrast palette: clearer sky-blue oceans, warm off-white land, visible slate-blue country borders, and subdued continent labels. Pins, interactions, filtering, conference records, source links, and calendar behavior remain unchanged. This is a UI/theme-only update, not a new data refresh.

## Version 4: Curated source expansion and official-source monitoring

Expanded to **21 curated conference editions** from **2026–2028**. Added a separate watcher for **14 organizer/official conference pages**; newly found conference links and changed dated passages enter review queues rather than being silently published. The static demo is not live-synced. See `PHASE_1_2_更新说明.md` for full instructions and caveats.
