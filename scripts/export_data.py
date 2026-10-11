#!/usr/bin/env python3
"""Export canonical JSON into a file that works from file:// without fetch()."""
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
obj=json.loads((root/'data/conferences.json').read_text(encoding='utf-8'))
ids=[c['id'] for c in obj['conferences']]
if len(ids)!=len(set(ids)):
    raise SystemExit('Duplicate conference ids detected')
(root/'data/conferences.js').write_text('window.ATLAS_DATA = '+json.dumps(obj,ensure_ascii=False,indent=2)+';\n',encoding='utf-8')
print(f"Exported {len(ids)} conference editions")
