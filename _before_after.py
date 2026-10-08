
import json, sys
sys.path.insert(0, 'weekly-cli')
from pathlib import Path
from evidence.claims import extract_claims
from narrative.revision import apply_revisions
from quality import publication_gate, scan_text_risk
from schema import SourceRecord

data = json.loads(Path('web/src/data/weekly/2026-W41.json').read_text(encoding='utf-8'))
event = data['events'][0]

ANALYSIS_KEYS = ("materialContent", "phaseSummary")
NESTED = ("unityOfOpposites", "quantityQuality", "negationOfNegation", "dataValidation")

def pick(ev):
    a = {}
    for k in ANALYSIS_KEYS:
        if isinstance(ev.get(k), str) and ev[k].strip():
            a[k] = ev[k]
    for k in NESTED:
        if isinstance(ev.get(k), dict) and any(ev[k].values()):
            a[k] = dict(ev[k])
    return a

analysis = pick(event)
sources = [SourceRecord(sourceId='s1', url=event.get('sourceUrl',''), title=event.get('title',''), kind='UNKNOWN', content=event.get('summary',''))]

print('=== CASE:', event.get('title'))
print()
print('--- BEFORE (what shipped) ---')
print('materialContent:', event.get('materialContent'))
print('sourceGrade  :', json.dumps(data['phase1']['selectedEvents'][0].get('sourceGrade'), ensure_ascii=False))
print()

claims = extract_claims(analysis, event_id='e1', sources=sources)
revised, records = apply_revisions(analysis, claims, round_no=1)

print('--- CLAIM LEDGER (deterministic) ---')
for c in claims:
    print(f'  {c.type:13} {c.riskLevel:6} {c.publicationDecision:9} | {c.statement[:56]}')
print()
print('--- REVISION RECORDS ---')
for r in records:
    print(f'  {r.action:8} {r.reason[:40]}')
    print(f'     before: {r.before[:60]}')
    print(f'     after : {r.after[:60]}')
print()
gate = publication_gate(dossiers=[], claims=claims, analysis_by_event={'e1': revised})
print('--- AFTER (what will ship) ---')
print('materialContent:', revised.get('materialContent'))
print('gate          :', gate.decision)
print('residual risk :', len(scan_text_risk(json.dumps(revised, ensure_ascii=False))))
print()
print('original unhedged sentence still present?', '希望通过主动通报控制舆论' in json.dumps(revised, ensure_ascii=False))
