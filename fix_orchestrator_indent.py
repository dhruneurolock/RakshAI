"""Fix the orchestrator indentation: indent static checks under else block and remove duplicate endpoint loop."""
import re

filepath = r"d:\NeuroPentWeb_data\NeuroPentWeb\backend\app\services\orchestrator.py"

with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# The old block that needs replacing (from "# Check 1: insecure transport" through the end of form probes)
# Find the markers
old_start_marker = "            # Check 1: insecure transport\r\n        if target_url.lower().startswith"
new_start = "            # Check 1: insecure transport\n            if target_url.lower().startswith"

# Strategy: find line numbers, read lines, fix indentation
lines = content.split("\n")

# Find key line indices
start_idx = None
end_idx = None
dup_loop_start = None
dup_loop_end = None

for i, line in enumerate(lines):
    stripped = line.rstrip("\r")
    if "# Check 1: insecure transport" in stripped and start_idx is None:
        start_idx = i
    if "# Validation phase: keep only findings above minimum confidence" in stripped:
        end_idx = i
        break

if start_idx is None or end_idx is None:
    print(f"Could not find markers: start={start_idx}, end={end_idx}")
    exit(1)

print(f"Static checks block: lines {start_idx+1} to {end_idx}")

# Find the duplicate endpoint collection loop within the block
dup_start = None
dup_end = None
for i in range(start_idx, end_idx):
    stripped = lines[i].rstrip("\r")
    if "# Dynamic endpoint collection + parameter/form extraction" in stripped:
        dup_start = i
    if dup_start and "auth_forms = [f for f in form_candidates" in stripped:
        dup_end = i
        break

print(f"Duplicate endpoint loop: lines {dup_start+1 if dup_start else 'N/A'} to {dup_end if dup_end else 'N/A'}")

# Build the new block
new_lines = []
for i in range(start_idx, end_idx):
    line = lines[i].rstrip("\r")
    
    # Skip the duplicate endpoint collection loop
    if dup_start is not None and dup_end is not None and dup_start <= i < dup_end:
        continue
    
    # Add 4 spaces of indentation to put everything under else:
    if line.strip():  # non-empty line
        new_lines.append("    " + line)
    else:
        new_lines.append(line)

# Replace in the full content
result_lines = lines[:start_idx] + new_lines + lines[end_idx:]
new_content = "\n".join(result_lines)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(new_content)

print(f"Fixed! Indented {len(new_lines)} lines under else block, removed duplicate endpoint loop.")
