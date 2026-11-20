import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from llm_tools import inspect_machine_by_udi, evaluate_live_reading, fetch_history
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
1. NEVER guess or invent sensor numbers, thresholds, or maintenance advice. Always rely strictly on the JSON outputs returned by your tools.
2. When a user asks about a machine by UDI, call `inspect_machine_by_udi`.
3. When a user provides raw sensor numbers (temperature, RPM, torque, tool wear), call `evaluate_live_reading`.
4. Always structure your response clearly:
   - **Status & Risk Level** (Normal / Warning / Critical — or الحالة ومستوى الخطر)
   - **Key Findings & Evidence** (Exact numbers and failure modes if any — النتائج والأدلة)
   - **Recommended Action** (Strictly from the tool output — الإجراء الموصى به)
5. If a machine UDI is not found, state that politely in the user's language. If the user asks about unrelated topics, politely decline in the user's language.
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
            "description": "Get overall dataset statistics, total machine count, available UDI range, and a list of machines with recorded failures needing maintenance.",
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
            self.messages.append(msg)

            if not msg.tool_calls:
                return msg.content

            for tool_call in msg.tool_calls:
                func_name = tool_call.function.name
                args = json.loads(tool_call.function.arguments)
                print(f"[DEBUG] Agent calling -> {func_name}({args})")

                func = AVAILABLE_FUNCTIONS.get(func_name)
                tool_result = func(**args) if func else json.dumps({"error": "Unknown tool"})

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