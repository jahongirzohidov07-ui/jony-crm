"""Import reviewed vocabulary artifacts. Usage: python script.py ARTIFACT_DIR."""
import json, sys
from pathlib import Path
source=Path(sys.argv[1])
root=Path(__file__).resolve().parents[1]
rows=json.loads((source/'vocabulary-001-300-Memorable.json').read_text(encoding='utf-8'))
for part in [4,5]:
    for line in (source/f'foundation-{part:02d}.txt').read_text(encoding='utf-8').splitlines():
        if line.startswith('## '): topic=line[3:]
        elif line.strip():
            fields=line.split('|')
            assert len(fields)==5
            rows.append(dict(zip(['Mavzu','So‘z','IPA (BrE)','Tarjima','Misol gap','Gap tarjimasi'],[topic]+fields)))
assert len(rows)==500 and len({r['So‘z'].casefold() for r in rows})==500
data=[dict(id=i,topic=r['Mavzu'],word=r['So‘z'],ipa=r['IPA (BrE)'],meaning=r['Tarjima'],example=r['Misol gap'],translation=r['Gap tarjimasi']) for i,r in enumerate(rows,1)]
(root/'src/data/intensive-vocabulary.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
print(f'Imported {len(data)} unique words.')
