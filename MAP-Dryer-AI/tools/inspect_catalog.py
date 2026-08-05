import json
from pathlib import Path
repo=Path(__file__).resolve().parents[1]
import sys
if str(repo/'src') not in sys.path:
    sys.path.insert(0,str(repo/'src'))
from data.feature_catalog import load_feature_catalog
cat = load_feature_catalog(repo/'config'/'data_dictionary.yaml')
out={'index': list(cat.index)}
with open('tools/feature_catalog_index.json','w',encoding='utf-8') as f:
    json.dump(out,f,ensure_ascii=True,indent=2)
print('Wrote tools/feature_catalog_index.json')
