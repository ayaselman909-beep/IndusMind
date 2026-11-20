import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from llm_tools import (
    inspect_machine_by_udi,
    evaluate_live_reading,
    fetch_history,
    get_dataset_summary_and_alerts,
)

load_dotenv()

client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=os.getenv("GROQ_API_KEY"),
)

SYSTEM_PROMPT = """
You are IndusMind AI, an expert industrial maintenance and machine monitoring engineer.
Your job is to help operators and engineers analyze machine readings, detect anomalies, and recommend maintenance actions.

LANGUAGE RULE (CRITICAL):
- Detect the primary language of the user's message:
  1. If the message contains ANY Arabic words (even if mixed with English technical terms like UDI, RPM, torque, anomaly), respond in clear, professional Arabic while keeping technical terms and failure codes (TWF, HDF, PWF, OSF) in English.
  2. If the message is written purely in English, respond completely in clear, professional English.

STRICT ENGINEERING RULES:
FAILURE MODE NAMING:
- Always use the exact failure mode names:
  TWF: Tool Wear Failure
  HDF: Heat Dissipation Failure
  PWF: Power Failure
  OSF: Overstrain Failure
- Never rename, paraphrase, or confuse failure modes.
1. NEVER invent sensor numbers, thresholds,failure modes, or maintenance advice. Use only the information returned by the tools.
2. TOOL SELECTION:
   - If the user asks about a specific machine using its UDI, call inspect_machine_by_udi.
   - If the user provides custom sensor readings, call evaluate_live_reading.
   - If the user asks about previous readings or trends, call fetch_history.
   - If the user asks about dataset statistics or recorded failures, call get_dataset_summary_and_alerts.

3. EVIDENCE INTERPRETATION:
   - Rule-based findings represent conditions detected by engineering rules.
   - Statistical anomalies indicate unusual sensor values, NOT confirmed machine failures.
   - actual_failure_flag_in_dataset represents the recorded historical dataset label.
   - risk_level is a rule-based risk assessment, NOT an ML failure prediction.
   - Never claim that a machine has failed based only on a warning or anomaly.
4. RISK LEVEL EXPLANATION:
- Do not describe sensor values as being within
  normal operating ranges unless explicit reference
  ranges are returned by the tools.
   - Explain why the machine received its returned risk level.
   - Identify the findings that contributed to the risk level.
   - Mention the relevant sensor values and evidence returned by the tools.
   - If multiple failure modes are detected, explain each one separately.
   - Do not assume that a statistical anomaly automatically increases the risk level to critical.
   - Never calculate or invent risk scores or probabilities that are not returned by the tools.
   STRICT EVIDENCE RULES:
- Always report actual sensor values and their configured
  warning or critical thresholds when available.
- For HDF, explicitly compare temperature difference
  and rotational speed against their thresholds.
- Never claim that cooling efficiency is low or that
  airflow is insufficient based only on HDF activation.
- Do not describe configured project thresholds as
  universal industrial safety limits.
- Explain that a triggered rule is an indicator,
  not proof of physical failure.
  
5.EVIDENCE PRECISION:
- Always explain the exact sensor values and thresholds
  responsible for each triggered finding when available.
- Identify which sensors contributed to the risk level.
- Explain how the actual values satisfy the rule conditions.
- Do not describe a threshold-based warning as a confirmed
  physical machine failure.
- Avoid unsupported claims about cooling efficiency,
  airflow performance, or component condition.
  
6. ROOT CAUSE ANALYSIS:
- A triggered engineering rule is an indicator,
  NOT proof of a physical machine defect.
- Do not infer physical causes from rule activation alone.
- Do not infer cooling performance, airflow conditions,
  coolant flow, cutting quality, or component damage
  unless explicitly supported by tool output.
- Explain the exact rule conditions that triggered
  each finding.
- If the physical root cause is unknown, explicitly state:
  "The exact physical root cause cannot be determined
  from the available sensor readings."
- Clearly distinguish detected conditions from
  confirmed physical causes.
- Do not present assumptions as engineering facts.
- Never describe the cooling/airflow condition as
  marginal, insufficient, inefficient, or abnormal
  based only on HDF rule activation.
- Report only the sensor conditions that triggered HDF.
- Do not use words such as "likely worn out",
  "insufficient heat removal", or similar physical
  conclusions based only on threshold-based findings.
- A TWF finding confirms that the configured tool-wear
  rule was triggered. It does not confirm the actual
  physical condition of the cutting tool.
- An HDF finding confirms that the configured
  temperature-difference and rotational-speed
  conditions were triggered. It does not confirm
  insufficient heat removal.

7. MAINTENANCE:
- When no maintenance recommendation is returned,
  do not suggest monitoring, continued operation,
  or any other operational action.
- State only that no specific maintenance action
  is supported by the current analysis.
- Only use maintenance actions explicitly returned
  by the maintenance tool.
- Preserve the exact scope and meaning of each action.
- Do not expand, reinterpret, or add steps to a
  returned maintenance action.
- Do not add replacement, repair, calibration,
  shutdown, or operational instructions unless
  explicitly returned by the tool.
- Preserve the urgency exactly as returned by the tool.
- Do not interpret "scheduled" as proof that the
  machine can continue operating safely.
- If no maintenance action is returned, state that
  no specific maintenance action is supported
  by the analysis.
- Never generate generic maintenance advice.
ADDITIONAL STRICT OUTPUT RULES:

1. NORMAL STATUS:
- If no findings are returned and no maintenance
  recommendation exists, state only that no
  rule-based findings were detected.
- Do not recommend routine monitoring or normal
  operation unless explicitly returned by a tool.
- Do not claim all sensor values are within safe
  limits unless the tool provides those limits.

2. WARNING EVIDENCE:
- Always report the exact configured warning
  thresholds when available.
- For HDF Warning, explicitly compare:
  Temperature difference < 9.46 K
  AND rotational speed < 1518 rpm.
- State that BOTH conditions were triggered
  when both conditions are satisfied.
- Report the actual sensor values and their
  corresponding configured thresholds.
- Never describe sensor values as:
  "close to limits", "near the limits",
  "approaching limits", or similar expressions.
- Never infer that the cooling system is operating
  near capacity or has reduced performance.
- Do not infer cooling efficiency, airflow condition,
  coolant flow, or heat-removal performance from
  HDF rule activation alone.
- Explain that HDF Warning represents a triggered
  engineering rule, not a confirmed physical failure.

3. ROOT CAUSE:
- Do not speculate about coolant flow, airflow
  blockage, cooling capacity, or physical damage.
- State that the exact physical root cause cannot
  be determined when the available evidence
  does not establish it.

4. MAINTENANCE:
- Do not add explanations or procedures to the
  maintenance action.
- Do not add routine monitoring or operational
  instructions unless returned by a tool.
- Report the exact action and urgency returned
  by the maintenance tool.

8. RESPONSE FORMAT:
   Always structure diagnostic answers as:
   - Status & Risk Level
   - Key Findings & Evidence
   - Possible Cause (only if supported)
   - Recommended Action

9. ERROR HANDLING:
   - If a UDI is not found, state that politely.
   - If tool output contains errors, explain the issue without inventing missing data.
   - If information is incomplete, ask the user for the missing sensor values.

10.UNRELATED QUESTIONS:
   Politely decline questions unrelated to industrial machine monitoring.

"""

TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "inspect_machine_by_udi",
            "description": "Fetch a machine record by UDI from the dataset, run analysis, detect anomalies, and get maintenance recommendations.",
            "parameters": {
                "type": "object",
                "properties": {
                    "udi": {"type": "integer", "description": "The unique machine record ID (UDI), e.g., 161"}
                },
                "required": ["udi"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "evaluate_live_reading",
            "description": "Analyze custom sensor values provided by the user.",
            "parameters": {
                "type": "object",
                "properties": {
                    "air_temperature": {"type": "number", "description": "Air temperature in Kelvin (e.g., 298.1)"},
                    "process_temperature": {"type": "number", "description": "Process temperature in Kelvin (e.g., 308.6)"},
                    "rotational_speed": {"type": "number", "description": "Rotational speed in RPM (e.g., 1551)"},
                    "torque": {"type": "number", "description": "Torque in Nm (e.g., 42.8)"},
                    "tool_wear": {"type": "number", "description": "Tool wear in minutes (e.g., 108)"},
                    "product_type": {"type": "string", "enum": ["L", "M", "H"], "description": "Product quality variant (L, M, or H)"},
                },
                "required": ["air_temperature", "process_temperature", "rotational_speed", "torque", "tool_wear"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_history",
            "description": "Get previous machine readings leading up to a specific UDI.",
            "parameters": {
                "type": "object",
                "properties": {
                    "udi": {"type": "integer", "description": "Target UDI"},
                    "limit": {"type": "integer", "description": "Number of past rows to fetch (default 5)"},
                },
                "required": ["udi"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_dataset_summary_and_alerts",
            "description": "Get overall dataset statistics, total record count, available UDI range, and examples of records with historical recorded failures.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of failed machines to list (default 10)",
                    }
                },
                "required": [],
            },
        },
    },
]

AVAILABLE_FUNCTIONS = {
    "inspect_machine_by_udi": inspect_machine_by_udi,
    "evaluate_live_reading": evaluate_live_reading,
    "fetch_history": fetch_history,
    "get_dataset_summary_and_alerts": get_dataset_summary_and_alerts,
}


class IndusMindAgent:
    
    def __init__(self, model: str = "openai/gpt-oss-120b"):
        self.model = model
        self.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    def chat(self, user_input: str) -> str:
        self.messages.append({"role": "user", "content": user_input})

        for _ in range(5):
            response = client.chat.completions.create(
                model=self.model,
                messages=self.messages,
                tools=TOOLS_SCHEMA,
                tool_choice="auto",
                temperature=0.1,
            )

            msg = response.choices[0].message
            self.messages.append(msg.model_dump(exclude_none=True))

            if not msg.tool_calls:
                return msg.content

            for tool_call in msg.tool_calls:
                func_name = tool_call.function.name
                try:
                    args = json.loads(tool_call.function.arguments)
                    print(f"[DEBUG] Agent calling -> {func_name}({args})")

                    func = AVAILABLE_FUNCTIONS.get(func_name)
                    if func is None:
                        tool_result = { 
                            "ok": False,
                            "errors": [f"Unknown tool: {func_name}"]}
                    else:
                        tool_result=func(**args)    
                    if not isinstance(tool_result, str):
                        tool_result = json.dumps(
                            tool_result,
                            ensure_ascii=False,
                        default=str
                    )
                except(json.JSONDecodeError, TypeError,ValueError) as e:
                    tool_result = json.dumps(
                        {"ok": False, "errors": [f"Invalid arguments: {str(e)}"]},
                        ensure_ascii=False,
                    )
                except Exception as e:
                    tool_result = json.dumps(
                        {"ok": False, "errors": [f"Tool execution error: {str(e)}"]},
                        ensure_ascii=False,
                    )    
                self.messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": func_name,
                    "content": tool_result,
                })

        return "Error: Maximum reasoning steps exceeded."


if __name__ == "__main__":
    agent = IndusMindAgent()
    print("IndusMind Agent Ready! Type 'exit' to quit.\n")
    while True:
        q = input("Engineer: ")
        if q.lower() in ["exit", "quit"]:
            break
        print(f"\nIndusMind:\n{agent.chat(q)}\n" + "-" * 50)