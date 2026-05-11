import ast
import re
from pathlib import Path

root = Path(__file__).resolve().parents[1]
out = root / "CODEFILE_SUMMARY.md"

exclude_dirs = {
    ".git", ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache",
    "dist", "build", ".next", "coverage", "site-packages"
}
code_exts = {".py", ".ts", ".tsx", ".js", ".jsx", ".ps1", ".sh", ".bat"}


def iter_code_files(base: Path):
    for p in base.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(base)
        if any(part in exclude_dirs for part in rel.parts):
            continue
        if p.suffix.lower() in code_exts:
            yield p


def summarize_py(text: str):
    purpose = ""
    functions = []
    classes = []
    imports = 0
    try:
        tree = ast.parse(text)
        purpose = ast.get_docstring(tree) or ""
        for node in tree.body:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                imports += 1
            elif isinstance(node, ast.FunctionDef):
                functions.append(node.name)
            elif isinstance(node, ast.AsyncFunctionDef):
                functions.append(f"{node.name} (async)")
            elif isinstance(node, ast.ClassDef):
                classes.append(node.name)
    except Exception:
        pass
    return purpose, imports, functions, classes


def summarize_ts_js(text: str):
    lines = text.splitlines()
    purpose = ""
    for l in lines[:20]:
        t = l.strip().lstrip("/").strip()
        if t and not t.startswith("import") and not t.startswith("export"):
            purpose = t
            break

    funcs = re.findall(r"(?:export\s+)?function\s+([A-Za-z_][A-Za-z0-9_]*)", text)
    classes = re.findall(r"(?:export\s+)?class\s+([A-Za-z_][A-Za-z0-9_]*)", text)
    hooks = re.findall(r"(?:const|let)\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*\(", text)
    imports = len(re.findall(r"^\s*import\s+", text, flags=re.MULTILINE))
    return purpose, imports, funcs, classes, hooks


def summarize_ps(text: str):
    lines = text.splitlines()
    purpose = next((ln.strip() for ln in lines[:20] if ln.strip()), "")
    funcs = re.findall(r"(?im)^\s*function\s+([A-Za-z_][A-Za-z0-9_-]*)", text)
    return purpose, funcs


files = sorted(iter_code_files(root), key=lambda p: str(p.relative_to(root)).lower())

md = []
md.append("# Code File Summary")
md.append("")
md.append("Auto-generated summary of project code files (excluding dependency/build folders).")
md.append("")
md.append(f"Total code files summarized: **{len(files)}**")
md.append("")

for p in files:
    rel = p.relative_to(root).as_posix()
    text = p.read_text(encoding="utf-8", errors="ignore")

    md.append(f"## {rel}")

    suffix = p.suffix.lower()
    if suffix == ".py":
        purpose, imports, funcs, classes = summarize_py(text)
        md.append("- Type: Python module")
        if purpose:
            md.append(f"- Purpose: {' '.join(purpose.split())[:240]}")
        md.append(f"- Imports: {imports}")
        if classes:
            md.append(f"- Classes: {', '.join(classes[:12])}" + (" ..." if len(classes) > 12 else ""))
        if funcs:
            md.append(f"- Functions: {', '.join(funcs[:15])}" + (" ..." if len(funcs) > 15 else ""))
        if not purpose and not classes and not funcs:
            md.append("- Summary: Minimal/non-standard Python file.")

    elif suffix in {".ts", ".tsx", ".js", ".jsx"}:
        purpose, imports, funcs, classes, hooks = summarize_ts_js(text)
        md.append("- Type: Frontend/Node script")
        if purpose:
            md.append(f"- Purpose: {' '.join(purpose.split())[:240]}")
        md.append(f"- Imports: {imports}")
        if classes:
            md.append(f"- Classes: {', '.join(classes[:10])}" + (" ..." if len(classes) > 10 else ""))
        if funcs:
            md.append(f"- Functions: {', '.join(funcs[:12])}" + (" ..." if len(funcs) > 12 else ""))
        if hooks:
            md.append(f"- Key declarations: {', '.join(hooks[:12])}" + (" ..." if len(hooks) > 12 else ""))
        if not purpose and not funcs and not classes and not hooks:
            md.append("- Summary: Utility/config/source file with minimal declarations.")

    else:
        purpose, funcs = summarize_ps(text)
        md.append("- Type: Script/automation")
        if purpose:
            md.append(f"- Purpose: {' '.join(purpose.split())[:240]}")
        if funcs:
            md.append(f"- Functions: {', '.join(funcs[:12])}" + (" ..." if len(funcs) > 12 else ""))
        if not purpose and not funcs:
            md.append("- Summary: Script without explicit function declarations.")

    md.append("")

out.write_text("\n".join(md), encoding="utf-8")
print(f"WROTE={out}")
print(f"COUNT={len(files)}")
