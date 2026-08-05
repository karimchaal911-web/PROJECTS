import json
from pathlib import Path
import csv
import sys
repo_root = Path(__file__).resolve().parents[1]
src_dir = repo_root / 'src'
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))
from data.data_cleaning import clean_column_names, DRYER_MAP_COLUMNS

p = repo_root / 'data' / 'processed' / 'dryerMAP_prototype_processed_2.csv'
with open(p, 'r', encoding='utf-8-sig') as f:
    header = next(csv.reader(f))
cleaned = clean_column_names(header)

out = {
    'header': header,
    'cleaned': cleaned,
    'expected': DRYER_MAP_COLUMNS,
    'missing_from_cleaned': [c for c in DRYER_MAP_COLUMNS if c not in cleaned],
    'extra_in_cleaned': [c for c in cleaned if c not in DRYER_MAP_COLUMNS],
}
with open('tools/check_schema_out.json', 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=True, indent=2)
print('Wrote tools/check_schema_out.json')
