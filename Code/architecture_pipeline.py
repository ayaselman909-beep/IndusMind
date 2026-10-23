"""
IndusMind - Advanced System Architecture & Pipeline
Author: System Architecture Specialist
Description: Processes the entire AI4I 2020 dataset, analyzes failure modes, generates 
             a comprehensive system report, and exports all results to a JSON file.
"""

from dataclasses import dataclass
from enum import Enum
import json
import pandas as pd

class ProductType(Enum):
    LOW = 'L'
    MEDIUM = 'M'
    HIGH = 'H'

@dataclass
class MachineInputData:
    udi: int
    product_id: str
    product_type: ProductType
    air_temperature: float
    process_temperature: float
    rotational_speed: int
    torque: float
    tool_wear: int
    twf: int  # Tool Wear Failure
    hdf: int  # Heat Dissipation Failure
    pwf: int  # Power Failure
    osf: int  # Overstrain Failure
    rnf: int  # Random Failures

@dataclass
class SystemOutputResult:
    udi: int
    product_id: str
    status: str
    risk_score: float
    failure_reason: str
    recommendation: str

class IndusMindAdvancedPipeline:
    def __init__(self, df: pd.DataFrame):
        self.df = df

    def evaluate_machine(self, row) -> SystemOutputResult:
        # Analyze failure conditions based on the dataset's failure flags
        failures = []
        if row['TWF'] == 1: failures.append("Tool Wear Failure")
        if row['HDF'] == 1: failures.append("Heat Dissipation Failure")
        if row['PWF'] == 1: failures.append("Power Failure")
        if row['OSF'] == 1: failures.append("Overstrain Failure")
        if row['RNF'] == 1: failures.append("Random Failure")

        # Determine risk score and status based on failure conditions and operational parameters
        if len(failures) > 0:
            risk_score = 0.95
            status = "Critical Failure Risk"
            failure_reason = ", ".join(failures)
            recommendation = f"Immediate maintenance required due to: {failure_reason}."
        elif (row['Process temperature [K]'] - row['Air temperature [K]']) > 10.0 or row['Tool wear [min]'] > 180:
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
            udi=int(row['UDI']),
            product_id=str(row['Product ID']),
            status=status,
            risk_score=risk_score,
            failure_reason=failure_reason,
            recommendation=recommendation
        )

    def run_pipeline(self):
        results = []
        normal_count = 0
        warning_count = 0
        critical_count = 0

        # Iterate through each machine record in the dataset and evaluate its status
        for _, row in self.df.iterrows():
            res = self.evaluate_machine(row)
            results.append(res.__dict__)
            
            if res.status == "Normal":
                normal_count += 1
            elif "Warning" in res.status:
                warning_count += 1
            else:
                critical_count += 1

        # printing the summary report to the console
        print("="*60)
        print("        INDUSMIND - SYSTEM PIPELINE SUMMARY REPORT")
        print("="*60)
        print(f" Total Machines Analyzed : {len(self.df)}")
        print(f" Normal Operations       : {normal_count}")
        print(f" Warnings / High Stress  : {warning_count}")
        print(f" Critical Failures       : {critical_count}")
        print("="*60)

        # save the complete system report to a JSON file
        output_file = "Code/system_results_report.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=4)
            
        print(f"[SUCCESS] All {len(self.df)} records processed successfully!")
        print(f"[SAVED] Complete system report exported to: '{output_file}'")
        print("="*60)

if __name__ == "__main__":
    # read the dataset
    dataset_path = "Dataset/ai4i2020.csv"
    df = pd.read_csv(dataset_path)

    # Initialize and run the advanced system architecture pipeline
    pipeline = IndusMindAdvancedPipeline(df)
    pipeline.run_pipeline()