import nbformat
from nbformat.v4 import new_code_cell
from nbconvert.preprocessors import ExecutePreprocessor
from pathlib import Path
import json

# Helper script: append a small save-cell to notebooks 03 and 04, execute them,
# and write saved model artifacts into models/ as requested.

PROJECT_ROOT = Path(__file__).resolve().parents[1]
NB_DIR = PROJECT_ROOT / "notebooks"
MODELS_DIR = PROJECT_ROOT / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

NOTEBOOKS = [
    NB_DIR / "03_Model1_SoftSensor.ipynb",
    NB_DIR / "04_Model2_AnomalyDetection&Diagnosis.ipynb",
]

# Save cell for Notebook 03: save final_model as models/moisture_pipeline.joblib
SAVE_CELL_03 = f"""
# === Auto-saved cell (moisture pipeline) ===
import joblib
from pathlib import Path
import json

models_dir = Path(r'{MODELS_DIR.as_posix()}')
models_dir.mkdir(parents=True, exist_ok=True)

saved = {{}}
try:
    joblib.dump(final_model, models_dir / "moisture_pipeline.joblib")
    saved['moisture_pipeline'] = str(models_dir / "moisture_pipeline.joblib")
except NameError:
    print('final_model not found; skipping moisture pipeline save')

# Collect simple metadata
moisture_meta = {{
    'model_class': final_model.__class__.__name__ if 'final_model' in globals() else None,
    'features': list(MODEL_FEATURES) if 'MODEL_FEATURES' in globals() else None,
}}

# Merge into shared metadata file
meta_path = models_dir / 'model_metadata.json'
if meta_path.exists():
    try:
        existing = json.loads(meta_path.read_text(encoding='utf-8'))
    except Exception:
        existing = {{}}
else:
    existing = {{}}
existing['moisture_pipeline'] = moisture_meta
try:
    meta_path.write_text(json.dumps(existing, indent=2), encoding='utf-8')
except Exception as e:
    print('Failed to write shared metadata:', e)

print('Saved artifacts:', saved)
"""

# Save cell for Notebook 04: save selected detector as models/anomaly_pipeline.joblib
SAVE_CELL_04 = f"""
# === Auto-saved cell (anomaly pipeline) ===
import joblib
from pathlib import Path
import json

models_dir = Path(r'{MODELS_DIR.as_posix()}')
models_dir.mkdir(parents=True, exist_ok=True)

saved = {{}}
# Prefer provisional_selected_model, fall back to selected_isolation_forest_model or one_class_svm_model
_detector = globals().get('provisional_selected_model') or globals().get('selected_isolation_forest_model') or globals().get('one_class_svm_model')
if _detector is not None:
    try:
        joblib.dump(_detector, models_dir / 'anomaly_pipeline.joblib')
        saved['anomaly_pipeline'] = str(models_dir / 'anomaly_pipeline.joblib')
    except Exception as e:
        print('Failed to save anomaly_pipeline:', e)
else:
    print('No selected detector found; skipping anomaly_pipeline save')

# Optionally save tuned components if present
for varname, filename in [('selected_isolation_forest_model','isolation_forest.joblib'),('one_class_svm_model','one_class_svm.joblib')]:
    try:
        obj = globals().get(varname)
        if obj is not None:
            joblib.dump(obj, models_dir / filename)
            saved[varname] = str(models_dir / filename)
    except Exception as e:
        print('Failed to save', filename, e)

# Save reference profile if present
try:
    if 'reference_profile' in globals() and reference_profile is not None:
        reference_profile.save(models_dir / 'reference_profile.json')
        saved['reference_profile'] = str(models_dir / 'reference_profile.json')
except Exception as e:
    print('Failed to save reference_profile:', e)

# Simple anomaly metadata
anomaly_meta = {{
    'detector_name': _detector.__class__.__name__ if _detector is not None else None,
    'detector_parameters': globals().get('best_one_class_svm_parameters') if 'best_one_class_svm_parameters' in globals() else None,
}}

# Merge into shared metadata file
meta_path = models_dir / 'model_metadata.json'
if meta_path.exists():
    try:
        existing = json.loads(meta_path.read_text(encoding='utf-8'))
    except Exception:
        existing = {{}}
else:
    existing = {{}}
existing['anomaly_pipeline'] = anomaly_meta
try:
    meta_path.write_text(json.dumps(existing, indent=2), encoding='utf-8')
except Exception as e:
    print('Failed to write shared metadata:', e)

print('Saved artifacts:', saved)
"""


def append_and_execute(nb_path: Path, save_cell: str):
    print('Processing', nb_path)
    # Read with utf-8-sig to handle possible BOMs
    with open(nb_path, 'r', encoding='utf-8-sig') as f:
        nb = nbformat.read(f, as_version=4)
    # Append save cell
    nb.cells.append(new_code_cell(save_cell))

    ep = ExecutePreprocessor(timeout=1200, kernel_name='python3')
    ep.preprocess(nb, {'metadata': {'path': str(nb_path.parent)}})

    # write executed notebook to a new file (preserve original)
    out_path = nb_path.with_suffix('.executed.ipynb')
    nbformat.write(nb, out_path)
    print('Executed notebook written to', out_path)


if __name__ == '__main__':
    for nb in NOTEBOOKS:
        append_and_execute(nb, SAVE_CELL_03 if '03_Model1' in nb.name else SAVE_CELL_04)
    print('All notebooks processed.')
