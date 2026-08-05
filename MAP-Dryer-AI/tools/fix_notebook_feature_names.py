import nbformat
from pathlib import Path

p = Path(__file__).resolve().parents[1] / 'notebooks' / '04_Model2_AnomalyDetection&Diagnosis.ipynb'
with open(p, 'r', encoding='utf-8-sig') as f:
    nb = nbformat.read(f, as_version=4)
replacements = {
    'final_moisture_h₂o': 'final_moisture_h2o',
    'final_moisture_hâ‚‚o': 'final_moisture_h2o',
}
changed = False
for cell in nb.cells:
    if isinstance(cell.source, list):
        src = ''.join(cell.source)
    else:
        src = cell.source
    new_src = src
    for old, new in replacements.items():
        if old in new_src:
            new_src = new_src.replace(old, new)
    if new_src != src:
        changed = True
        # preserve original cell.source type
        if isinstance(cell.source, list):
            cell.source = [new_src]
        else:
            cell.source = new_src

if changed:
    nbformat.write(nb, p)
    print('Notebook updated')
else:
    print('No changes made')
