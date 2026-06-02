import re

with open("d:/NeuroPentWeb_data/NeuroPentWeb/backend/app/services/orchestrator.py", "r", encoding="utf-8") as f:
    lines = f.readlines()
    
for i, line in enumerate(lines):
    if "timeout" in line.lower() or "wait_for" in line.lower() or "25" in line:
        print(f"Line {i+1}: {line.strip()}")
