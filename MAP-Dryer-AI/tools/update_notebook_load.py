import nbformat
from pathlib import Path
p = Path(__file__).resolve().parents[1] / 'notebooks' / '04_Model2_AnomalyDetection&Diagnosis.ipynb'
with open(p, 'r', encoding='utf-8-sig') as f:
    nb = nbformat.read(f, as_version=4)
changed = False
for cell in nb.cells:
    if cell.cell_type == 'code' and isinstance(cell.source, list):
        src = ''.join(cell.source)
    elif cell.cell_type == 'code':
        src = cell.source
    else:
        continue
    if 'dryerMAP_model = pd.read_csv(' in src:
        new_src = '''DATA_PATH = PROJECT_ROOT / "data" / "processed" / "dryerMAP_prototype_processed_2.csv"

        # Read the processed table and normalize column names (convert unicode subscripts
        # to ascii digits) so notebooks can reference feature names consistently.
raw_df = pd.read_csv(DATA_PATH, parse_dates=["date", "timestamp"], encoding='utf-8-sig')
        from data.data_cleaning import clean_column_names
        raw_df.columns = clean_column_names(raw_df.columns)

        dryerMAP_model = raw_df

        dryerMAP_model["time"] = dryerMAP_model["time"].astype(str)

        # Show a preview and schema
        display(dryerMAP_model.head())
        dryerMAP_model.info()
        '''
        cell.source = [new_src]
        changed = True
        break
if changed:
    with open(p, 'w', encoding='utf-8') as f:
        nbformat.write(nb, f)
    print('Notebook load cell updated')
else:
    print('No matching cell found')
