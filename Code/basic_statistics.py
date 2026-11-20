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

    output_dir = BASE_DIR / "Code"
    output_dir.mkdir(parents=True, exist_ok=True)

    stats.to_csv(output_dir / "basic_statistics.csv",index_label="Feature")
    corr.to_csv(output_dir / "correlation_matrix.csv", index_label="Feature")