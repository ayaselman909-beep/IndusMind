from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
df = pd.read_csv(BASE_DIR / "Dataset" / "ai4i2020.csv")

cols = {
    "Air temperature [K]": "Air Temperature",
    "Rotational speed [rpm]": "Rotational Speed",
    "Torque [Nm]": "Torque",
    "Tool wear [min]": "Tool Wear",
}
data = df[list(cols.keys())].rename(columns=cols)


def compute_stats(data: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame({
        "Mean": data.mean(),
        "Median": data.median(),
        "Min": data.min(),
        "Max": data.max(),
        "Std": data.std(),
        "Q1": data.quantile(0.25),
        "Q3": data.quantile(0.75),
    }).round(2)


if __name__ == "__main__":
    stats = compute_stats(data)
    corr = data.corr().round(3)

    print(stats)
    print()
    print(corr)

    stats.to_csv(BASE_DIR / "Code" / "basic_statistics.csv")
    corr.to_csv(BASE_DIR / "Code" / "correlation_matrix.csv")