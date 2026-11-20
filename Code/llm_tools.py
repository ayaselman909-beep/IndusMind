import json
from data_loader import SENSOR_COLUMNS, load_dataset
from agent_tools import (
    analyze_machine,
    detect_anomaly,
    get_machine_history,
    recommend_maintenance,
)

def inspect_machine_by_udi(udi: int) -> str:
    """
    Fetches sensor readings for a specific machine record (UDI) from the dataset,
    runs full engineering analysis, checks for statistical anomalies, and generates
    maintenance recommendations if needed.
    Use this whenever the user asks to check, inspect, or diagnose a machine by its UDI number.
    """
    df = load_dataset()
    row = df[df["UDI"] == int(udi)]
    if row.empty:
        return json.dumps({"ok": False, "error": f"Machine UDI {udi} not found in dataset."})

    r = row.iloc[0]
    reading = {"product_type": str(r["Type"])}
    for key, col in SENSOR_COLUMNS.items():
        reading[key] = float(r[col])

    analysis = analyze_machine(reading)
    anomalies = detect_anomaly(reading)
    recommendations = recommend_maintenance(analysis)

    result = {
        "udi": int(udi),
        "product_id": str(r["Product ID"]),
        "actual_failure_flag_in_dataset": int(r["Machine failure"]),
        "analysis": analysis,
        "statistical_anomalies": anomalies,
        "maintenance": recommendations,
    }
    return json.dumps(result)


def evaluate_live_reading(
    air_temperature: float,
    process_temperature: float,
    rotational_speed: float,
    torque: float,
    tool_wear: float,
    product_type: str | None = None,
) -> str:
    """
    Evaluates custom or live sensor readings provided directly by the user in the chat.
    Returns risk level, failure modes (TWF, HDF, PWF, OSF), statistical anomalies, and maintenance advice.
    """
    reading = {
        "air_temperature": air_temperature,
        "process_temperature": process_temperature,
        "rotational_speed": rotational_speed,
        "torque": torque,
        "tool_wear": tool_wear,
        "product_type": product_type,
    }
    analysis = analyze_machine(reading)
    anomalies = detect_anomaly(reading)
    recommendations = recommend_maintenance(analysis)

    return json.dumps({
        "analysis": analysis,
        "statistical_anomalies": anomalies,
        "maintenance": recommendations,
    })


def fetch_history(udi: int, limit: int = 5) -> str:
    """
    Retrieves the last `limit` readings up to and including the specified `udi` to observe trends.
    """
    return json.dumps(get_machine_history(udi=int(udi), limit=int(limit)))

def get_dataset_summary_and_alerts(limit: int = 10) -> str:
    """
    Provides historical dataset statistics and recorded failure examples.
    Use this whenever the user asks :
    - How many records are in the dataset?
    - What UDI numbers are available?
    - How many failures are recorded?
    - Which  UDI numbers have recorded failures labels?
    """
    df = load_dataset()
    total_records = int(len(df))
    min_udi = int(df["UDI"].min())
    max_udi = int(df["UDI"].max())

    failures_df = df[df["Machine failure"] == 1]
    total_failures = int(len(failures_df))
    limit = max(1, min(int(limit), 100))  
    sample_alerts = []
    for _, r in failures_df.head(limit).iterrows():
        modes = [m for m in ["TWF", "HDF", "PWF", "OSF", "RNF"] if int(r[m]) == 1]
        sample_alerts.append({
            "udi": int(r["UDI"]),
            "product_id": str(r["Product ID"]),
            "product_type": str(r["Type"]),
            "failure_modes": modes,
        })

    return json.dumps({
        "ok": True,
        "total_records": total_records,
        "udi_range": {"min": min_udi, "max": max_udi},
        "total_recorded_failures": total_failures,
        "sample_failed_machines": sample_alerts,
        "note": f"Showing top {len(sample_alerts)} failed records out of {total_failures}. Ask about any specific UDI for full diagnosis.",
    })