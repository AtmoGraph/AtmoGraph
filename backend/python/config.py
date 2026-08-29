from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = PROJECT_ROOT / "backend" / "data"

MODEL_DIR = PROJECT_ROOT / "backend" / "models"

REPORT_DIR = PROJECT_ROOT / "backend" / "reports"


FULL_RIPPLE_DATASET = DATA_DIR / "full_ripple_dataset.csv"

RIPPLE_DATASET = DATA_DIR / "ripple_dataset.csv"

SYNTHETIC_DISRUPTIONS = DATA_DIR / "synthetic_disruptions.csv"

TRAIN_FILE = DATA_DIR / "train.csv"

VALIDATION_FILE = DATA_DIR / "validation.csv"

TEST_FILE = DATA_DIR / "test.csv"

GNN_MODEL = MODEL_DIR / "ripple_gnn.pt"

GNN_METRICS = REPORT_DIR / "gnn_test_metrics.json"

GNN_PREDICTIONS = REPORT_DIR / "gnn_test_predictions.csv"
