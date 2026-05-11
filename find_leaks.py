import os
import re

def search_files():
    for root, _, files in os.walk(r"d:\NeuroPentWeb_data\NeuroPentWeb\backend\app"):
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                    if "next(get_db())" in content:
                        print(f"Found next(get_db()) in {path}")
                        # Print the surrounding lines
                        lines = content.split('\n')
                        for i, line in enumerate(lines):
                            if "next(get_db())" in line:
                                print(f"Line {i+1}: {line.strip()}")
                    if "get_db()" in content and "next" not in content and "Depends" not in content:
                        print(f"Found other get_db() usage in {path}")

search_files()
