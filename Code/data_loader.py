"""
IndusMind - shared data loader.
Single place for the dataset path and column names, so every script and
Agent tool reads the data the same way and works from any folder.
"""

from functools import lru_cache
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_PATH = BASE_DIR / "Dataset" / "ai4i2020.csv"

# Agent-facing key -> column name in the CSV (sensor readings only, no failure labels)
SENSOR_COLUMNS = {
    "air_temperature": "Air temperature [K]",
    "process_temperature": "Process temperature [K]",
    "rotational_speed": "Rotational speed [rpm]",
    "torque": "Torque [Nm]",
    "tool_wear": "Tool wear [min]",
}


@lru_cache(maxsize=1)
def load_dataset() -> pd.DataFrame:
    """Load the AI4I 2020 CSV once and cache it."""
    if not DATASET_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found at {DATASET_PATH}. "
            "Download it and extract it into the 'Dataset' folder (see README)."
        )
    df = pd.read_csv(DATASET_PATH)
    missing_columns = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_columns:
        raise ValueError(
            f"Dataset is missing required columns: {missing_columns}. "
        )
    return df

REQUIRED_COLUMNS=[
    'UDI',
    'Product ID',
    'Type',
    'Machine failure',
    'TWF',
    'HDF',
    'PWF',
    'OSF',
    'RNF',
    *SENSOR_COLUMNS.values()
]