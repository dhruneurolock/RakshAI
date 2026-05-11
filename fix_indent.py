"""Fix orchestrator: indent static checks under else, remove duplicate endpoint loop."""
filepath = r"d:\NeuroPentWeb_data\NeuroPentWeb\backend\app\services\orchestrator.py"

with open(filepath, "r", encoding="utf-8") as f:
    lines = f.readlines()

# Find key markers
check1_idx = None
dup_loop_start = None
dup_loop_end = None  # line with auth_forms
validation_idx = None

for i, line in enumerate(lines):
    if "# Check 1: insecure transport" in line and check1_idx is None:
        check1_idx = i
    if "# Dynamic endpoint collection + parameter/form extraction" in line:
        dup_loop_start = i
    if dup_loop_start and "auth_forms = [f for f in form_candidates" in line:
        dup_loop_end = i
        break

for i, line in enumerate(lines):
    if "# Validation phase: keep only findings above minimum confidence" in line:
        validation_idx = i
        break

print(f"check1={check1_idx+1}, dup_loop={dup_loop_start+1}-{dup_loop_end}, validation={validation_idx+1}")

if not all([check1_idx, validation_idx]):
    print("ERROR: Could not find markers")
    exit(1)

# Build new lines: indent everything from check1 to validation, skip dup loop
new_lines = []
for i in range(check1_idx, validation_idx):
    # Skip duplicate endpoint collection loop (already moved above)
    if dup_loop_start is not None and dup_loop_end is not None:
        if dup_loop_start <= i < dup_loop_end:
            continue

    line = lines[i]
    stripped = line.rstrip('\r\n')

    if stripped.strip():  # non-empty
        new_lines.append("    " + stripped + "\n")
    else:
        new_lines.append("\n")

# Reconstruct
result = lines[:check1_idx] + new_lines + lines[validation_idx:]

with open(filepath, "w", encoding="utf-8") as f:
    f.writelines(result)

print(f"Done! Indented {len(new_lines)} lines, removed duplicate endpoint loop.")
