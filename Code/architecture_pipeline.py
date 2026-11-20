"""
IndusMind - System Pipeline Baseline (Week 1)
Evaluates AI4I 2020 records and optionally exports a summary report to JSON.
"""
from dataclasses import dataclass
import json
from pathlib import Path
from data_loader import load_dataset
@dataclass
class SystemOutputResult:
    udi: int
    product_id: str
    status: str
    risk_score: float
    failure_reason: str
    recommendation: str
class IndusMindAdvancedPipeline:
    def __init__(self, df):
        self.df = df

    def evaluate_machine(self, row) -> SystemOutputResult:
        failures = []
        if row["TWF"] == 1: failures.append("Tool Wear Failure")
        if row["HDF"] == 1:   failures.append("Heat Dissipation Failure")
        if row["PWF"] == 1: failures.append("Power Failure")
        if row["OSF"] == 1: failures.append("Overstrain Failure")
        if row["RNF"] == 1: failures.append("Random Failure")

        temp_diff = row["Process temperature [K]"] - row["Air temperature [K]"]
        if failures:
            risk_score = 0.95
            status = "Critical Failure Risk"
            failure_reason = ", ".join(failures)
            recommendation = f"Immediate maintenance required due to: {failure_reason}."
        elif temp_diff > 10.0 or row["Tool wear [min]"] > 180:
            risk_score = 0.75
            status = "Warning - High Stress"
            failure_reason = "High Thermal/Tool Stress"
            recommendation = "Schedule inspection for cooling and tool replacement soon."
        else:
            risk_score = 0.05
            status = "Normal"
            failure_reason = "None"
            recommendation = "System operating within safe parameters."

        return SystemOutputResult(
            udi=int(row["UDI"]),
            product_id=str(row["Product ID"]),
            status=status,
            risk_score=risk_score,
            failure_reason=failure_reason,
            recommendation=recommendation,
        )

    def run_pipeline(self, output_file: Path | None = None):
        results = []
        normal_count = 0
        warning_count = 0
        critical_count = 0

        for _, row in self.df.iterrows():
            res = self.evaluate_machine(row)
            results.append(res.__dict__)

            if res.status == "Normal":
                normal_count += 1
            elif "Warning" in res.status:
                warning_count += 1
            else:
                critical_count += 1

        print("=" * 60)
        print("        INDUSMIND - SYSTEM PIPELINE SUMMARY REPORT")
        print("=" * 60)
        print(f" Total Machines Analyzed : {len(self.df)}")
        print(f" Normal Operations       : {normal_count}")
        print(f" Warnings / High Stress  : {warning_count}")
        print(f" Critical Failures       : {critical_count}")
        print("=" * 60)

        if output_file is not None:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=4)
            print(f"[SAVED] Report exported to: '{output_path}'")

if __name__ == "__main__":
    df = load_dataset()
    pipeline = IndusMindAdvancedPipeline(df)
    pipeline.run_pipeline()