import sys
from pathlib import Path
repo_root = Path(__file__).resolve().parents[1]
src_dir = repo_root / 'src'
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))
from data.data_cleaning import clean_column_names
import csv
p=repo_root / 'data' / 'processed' / 'dryerMAP_prototype_processed_2.csv'
with open(p,'r',encoding='utf-8-sig') as f:
    h=next(csv.reader(f))
cleaned = clean_column_names(h)
import json
out = {
    'cleaned_header': cleaned,
    'contains_final_moisture_h2o': 'final_moisture_h2o' in cleaned,
    'contains_unicode_subscript': any('final_moisture' in c and '\u2082' in c for c in cleaned),
}
with open('tools/header_inspect_out.json','w',encoding='utf-8') as f:
    json.dump(out,f,ensure_ascii=True,indent=2)
print('Wrote tools/header_inspect_out.json')
