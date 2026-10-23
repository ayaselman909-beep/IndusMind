# IndusMind
IndusMind  is an intelligent machine monitoring system that analyzes machine data, predicts malfunctions, and links the results to clear recommendations through AI Agent and Dashboard.

# To Download DataSet "AI4I 2020 Predictive Maintenance Dataset" Locally to run a project fast and without internet.
please Click on the link  
" https://archive.ics.uci.edu/dataset/601/ai4i+2020+predictive+maintenance+dataset "
After Download the zip file create Folder his name is "Dataset" and extract the file in Dataset Folder.

# Data Dictionary

# Operating Parameters:
* **Air temperature [K]:** The temperature of the air surrounding the machine (in Kelvin).
* **Process temperature [K]:** The temperature of the machine during the manufacturing process (in Kelvin).
* **Rotational speed [rpm]:** The rotational speed of the machine (in revolutions per minute).
* **Torque [Nm]:** The turning force applied by the machine (in Newton-meters).
* **Tool wear [min]:** The continuous operational time causing wear and tear on the cutting tool (in minutes).

# Failure Types (Targets):
* **TWF (Tool Wear Failure):** Machine downtime or failure caused by complete wear or breakage of the tool.
* **HDF (Heat Dissipation Failure):** Failure due to severe overheating and the cooling system's inability to dissipate the heat.
* **PWF (Power Failure):** Failure caused by a sudden drop or disruption in the required operational power.
* **OSF (Overstrain Failure):** Failure resulting from excessive load, pressure, or strain beyond the machine's capacity.
* **RNF (Random Failures):** Unpredictable, rare, or random machine failures that do not fall under the other specific categories.

# IndusMind - Week 1: Data & System Design

This repository contains the work for **Week 1** of the IndusMind project, focusing on system architecture, dataset configuration, and pipeline design[cite: 2].

## 🛠️ What Was Done (Week 1 Deliverables)
- **Dataset Setup:** Configured and verified the `2020 AI4I` dataset (`Dataset/ai4i2020.csv`) to ensure all 10,000 records are processed correctly[cite: 2].
- **System Architecture:** Designed the foundational system architecture and processing pipeline (`Code/architecture_pipeline.py`)[cite: 2].
- **Inputs & Outputs Defined:** 
  - **Inputs:** Machine sensor data (Tool Wear, Torque, Rotational Speed, Temperature)[cite: 2].
  - **Outputs:** System analysis results and risk scores (configured to generate locally).

---

## 🚀 How to Run the Pipeline & Generate Results

Since the large result files are excluded from Git to keep the repository lightweight, you can generate the system results report locally on your machine by running the following command:

```bash
python Code/architecture_pipeline.py