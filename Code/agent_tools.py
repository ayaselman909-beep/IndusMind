"""
IndusMind - Agent Tools 

Tools:
    analyze_machine(reading)        -> derived values, rule findings, and risk level
    detect_anomaly(reading)         -> statistical outlier check (IQR + Z-score)
    get_machine_history(udi, limit) -> previous readings ordered by UDI
    recommend_maintenance(analysis) -> recommendations backed only by findings
"""
from functools import lru_cache
import math

from data_loader import SENSOR_COLUMNS, load_dataset

WARNING_MARGIN = 0.10
TWF_WEAR_MIN = 200
HDF_TEMP_DIFF_K = 8.6
HDF_RPM = 1380
PWF_POWER_LOW_W = 3500
PWF_POWER_HIGH_W = 9000
OSF_LIMITS = {"L": 11000, "M": 12000, "H": 13000}

SEVERITY_ORDER = {"normal": 0, "warning": 1, "critical": 2}

RECOMMENDATIONS = {
    "TWF": "Replace or inspect the cutting tool.",
    "HDF": "Check the cooling system and airflow; reduce load until the temperature difference recovers.",
    "PWF": "Check the power supply and motor load; torque/speed combination is outside the safe power range.",
    "OSF": "Reduce the load or torque and inspect the tool; wear x torque is near/over the strain limit.",
    "STATISTICAL": "Re-check the sensors and recent readings; values are unusual compared with the dataset.",
}

def validate_reading(reading):
    """Return (clean_reading, errors); clean_reading is None when invalid."""
    if not isinstance(reading, dict):
        return None, ["reading must be a dict of sensor values"]

    errors, clean = [], {}
    for key in SENSOR_COLUMNS:
        value = reading.get(key)
        if value is None:
            errors.append(f"missing value: {key}")
            continue
        try:
            value = float(value)
        except (TypeError, ValueError):
            errors.append(f"not a number: {key}")
            continue
        if math.isnan(value) or math.isinf(value):
            errors.append(f"invalid number: {key}")
            continue
        clean[key] = value

    if "rotational_speed" in clean and clean["rotational_speed"] <= 0:
        errors.append("rotational_speed must be > 0")
    if "torque" in clean and clean["torque"] < 0:
        errors.append("torque must be >= 0")
    if "tool_wear" in clean and clean["tool_wear"] < 0:
        errors.append("tool_wear must be >= 0")

    ptype = str(reading.get("product_type") or "").upper() or None
    if ptype not in (None, "L", "M", "H"):
        errors.append("product_type must be L, M or H")
    clean["product_type"] = ptype

    return (None, errors) if errors else (clean, [])

@lru_cache(maxsize=1)
def _reference():
    df = load_dataset()
    ref = {}
    for key, col in SENSOR_COLUMNS.items():
        s = df[col]
        q1, q3 = s.quantile(0.25), s.quantile(0.75)
        iqr = q3 - q1
        ref[key] = {
            "mean": float(s.mean()),
            "std": float(s.std()),
            "lower": float(q1 - 1.5 * iqr),
            "upper": float(q3 + 1.5 * iqr),
        }
    return ref

def _anomalies(clean):
    found = []
    for key, ref in _reference().items():
        value = clean[key]
        z = (value - ref["mean"]) / ref["std"] if ref["std"] else 0.0
        methods = []
        if value < ref["lower"] or value > ref["upper"]:
            methods.append("IQR")
        if abs(z) > 3:
            methods.append("Z-score")
        if methods:
            found.append({
                "feature": key,
                "value": value,
                "z_score": round(z, 2),
                "normal_range_iqr": [round(ref["lower"], 2), round(ref["upper"], 2)],
                "detected_by": methods,
            })
    return found

def _rule_findings(c, d, assumptions):
    findings = []
    m = WARNING_MARGIN

    def add(mode, severity, evidence):
        findings.append({"failure_mode": mode, "severity": severity, "evidence": evidence})

    if c["tool_wear"] >= TWF_WEAR_MIN:
        add("TWF", "critical", f"tool wear {c['tool_wear']:.0f} min >= {TWF_WEAR_MIN} min")
    elif c["tool_wear"] >= TWF_WEAR_MIN * (1 - m):
        add("TWF", "warning", f"tool wear {c['tool_wear']:.0f} min is close to {TWF_WEAR_MIN} min")

    diff, rpm = d["temp_difference_k"], c["rotational_speed"]
    if diff < HDF_TEMP_DIFF_K and rpm < HDF_RPM:
        add("HDF", "critical", f"temp difference {diff} K < {HDF_TEMP_DIFF_K} K and speed {rpm:.0f} rpm < {HDF_RPM} rpm")
    elif diff < HDF_TEMP_DIFF_K * (1 + m) and rpm < HDF_RPM * (1 + m):
        add("HDF", "warning", f"temp difference {diff} K and speed {rpm:.0f} rpm are close to heat-dissipation limits")

    p = d["power_w"]
    if p < PWF_POWER_LOW_W or p > PWF_POWER_HIGH_W:
        add("PWF", "critical", f"power {p} W outside [{PWF_POWER_LOW_W}, {PWF_POWER_HIGH_W}] W")
    elif p < PWF_POWER_LOW_W * (1 + m) or p > PWF_POWER_HIGH_W * (1 - m):
        add("PWF", "warning", f"power {p} W is close to allowed limits")

    ptype = c["product_type"]
    if ptype is None:
        ptype = "L"
        assumptions.append("product_type not given: used strictest overstrain limit (type L)")
    limit = OSF_LIMITS[ptype]
    strain = d["strain_minnm"]
    if strain > limit:
        add("OSF", "critical", f"strain {strain} min*Nm > {limit} (type {ptype})")
    elif strain > limit * (1 - m):
        add("OSF", "warning", f"strain {strain} min*Nm is close to {limit} (type {ptype})")

    return findings

def detect_anomaly(reading):
    """Statistical check of one reading against the dataset (IQR + Z-score)."""
    clean, errors = validate_reading(reading)
    if errors:
        return {"ok": False, "errors": errors}
    anomalies = _anomalies(clean)
    return {"ok": True, "is_anomalous": bool(anomalies), "anomalies": anomalies}

def analyze_machine(reading):
    """Derived values, rule-based findings, and overall risk level."""
    clean, errors = validate_reading(reading)
    if errors:
        return {"ok": False, "errors": errors}

    assumptions = []
    derived = {
        "temp_difference_k": round(clean["process_temperature"] - clean["air_temperature"], 2),
        "power_w": round(clean["torque"] * clean["rotational_speed"] * 2 * math.pi / 60, 1),
        "strain_minnm": round(clean["tool_wear"] * clean["torque"], 1),
    }
    findings = _rule_findings(clean, derived, assumptions)
    anomalies = _anomalies(clean)

    if anomalies:
        names = ", ".join(a["feature"] for a in anomalies)
        findings.append({
            "failure_mode": "STATISTICAL",
            "severity": "warning",
            "evidence": f"unusual values (outliers): {names}",
        })

    risk = max((f["severity"] for f in findings), key=lambda s: SEVERITY_ORDER[s], default="normal")
    return {
        "ok": True,
        "readings": clean,
        "derived": derived,
        "findings": findings,
        "risk_level": risk,
        "assumptions": assumptions,
        "note": "RNF (random failures) cannot be predicted from sensor readings.",
    }

def get_machine_history(udi, limit=10):
    """Last `limit` readings up to and including `udi` (UDI used as time order)."""
    df = load_dataset()
    try:
        udi = int(udi)
        limit = max(1, min(int(limit), 100))
    except (TypeError, ValueError):
        return {"ok": False, "errors": ["udi and limit must be integers"]}
    if udi not in set(df["UDI"]):
        return {"ok": False, "errors": [f"UDI {udi} not found"]}

    rows = df[df["UDI"] <= udi].tail(limit)
    history = []
    for _, r in rows.iterrows():
        entry = {
            "udi": int(r["UDI"]),
            "product_id": str(r["Product ID"]),
            "product_type": str(r["Type"]),
            "machine_failure": int(r["Machine failure"]),
        }
        for key, col in SENSOR_COLUMNS.items():
            entry[key] = float(r[col])
        history.append(entry)

    return {
        "ok": True,
        "count": len(history),
        "history": history,
        "note": "simulated history: UDI is used as time order",
    }

def recommend_maintenance(analysis):
    """Recommendations built strictly from the findings of analyze_machine()."""
    if not isinstance(analysis, dict) or not analysis.get("ok"):
        return {"ok": False, "errors": ["need a successful analyze_machine() result"]}

    findings = analysis.get("findings", [])
    if not findings:
        return {
            "ok": True,
            "urgency": "none",
            "recommendations": [],
            "message": "No rule was triggered, so no maintenance action is supported by the data.",
        }

    actions = [
        {
            "failure_mode": f["failure_mode"],
            "severity": f["severity"],
            "action": RECOMMENDATIONS[f["failure_mode"]],
            "based_on": f["evidence"],
        }
        for f in findings
    ]
    urgency = "immediate" if analysis["risk_level"] == "critical" else "scheduled"
    return {"ok": True, "urgency": urgency, "recommendations": actions}

TOOLS = {
    "analyze_machine": analyze_machine,
    "detect_anomaly": detect_anomaly,
    "get_machine_history": get_machine_history,
    "recommend_maintenance": recommend_maintenance,
}