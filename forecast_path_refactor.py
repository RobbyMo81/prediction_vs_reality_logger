
import os
import ast
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
CONFIG_LOCATIONS = [
    PROJECT_ROOT / "prediction_logger" / "config.py",
    PROJECT_ROOT / "tests" / "config" / "test_config.py",
]
TARGET_FILES = list(PROJECT_ROOT.glob("prediction_logger/**/*.py")) + list(PROJECT_ROOT.glob("tests/**/*.py"))

def load_config_forecast_folder():
    for config_file in CONFIG_LOCATIONS:
        if config_file.exists():
            with open(config_file, "r") as f:
                contents = f.read()
                if "forecast_folder" in contents:
                    lines = contents.splitlines()
                    for line in lines:
                        if "forecast_folder" in line:
                            parts = line.split("=")
                            if len(parts) > 1:
                                folder = parts[1].strip().replace("'", "").replace('"', '')
                                return folder
    return "forecast"

def add_path_import(content):
    """Add Path import if it's not already present"""
    lines = content.splitlines(keepends=True)
    has_path_import = any("from pathlib import Path" in line for line in lines)
    
    if not has_path_import:
        # Find where to insert import
        import_idx = 0
        for i, line in enumerate(lines):
            if line.startswith("import ") or line.startswith("from "):
                import_idx = i + 1
            elif line.strip() and not line.startswith("#") and import_idx == 0:
                break
                
        # Insert Path import
        lines.insert(import_idx, "from pathlib import Path\n")
        if import_idx + 1 < len(lines) and lines[import_idx + 1].strip():
            lines.insert(import_idx + 1, "\n")
            
    return "".join(lines)

def audit_and_refactor(file_path, forecast_folder):
    changes = []

    with open(file_path, "r", encoding='utf-8') as f:
        content = f.read()
        
    # Add Path import if needed
    new_content = add_path_import(content)
    
    # Split into lines for path fixes
    lines = new_content.splitlines(keepends=True)
    new_lines = []
    
    for i, line in enumerate(lines):
        if "os.path.join" in line and "forecast" in line:
            old_line = line.strip()
            
            # Only refactor specific problematic patterns
            if ("tests/tests" in line or 
                ("tests/forecast" in line and "os.getcwd" in line)):
                indent = len(line) - len(line.lstrip())
                indent_str = " " * indent
                
                if "test_dir" not in line:
                    new_lines.append(f"{indent_str}project_root = Path(__file__).resolve().parents[1]\n")
                    new_lines.append(f"{indent_str}forecast_path = project_root / '{forecast_folder}' / forecast_filename\n")
                else:
                    new_lines.append(f"{indent_str}forecast_path = Path(test_dir).parent / '{forecast_folder}' / forecast_filename\n")
                
                changes.append((file_path.name, i+1, old_line, new_lines[-1].strip()))
                continue
                
        new_lines.append(line)

    # Write back changes
    with open(file_path, "w", encoding='utf-8') as f:
        f.write("".join(new_lines))

    with open(file_path, "w") as f:
        f.writelines(new_lines)

    return changes

def run_tests():
    result = subprocess.run(["pytest", "tests/", "-v"], capture_output=True, text=True)
    return result.stdout

def write_report(refactor_log, test_output):
    report_path = PROJECT_ROOT / "refactor_report.md"
    with open(report_path, "w", encoding='utf-8') as f:
        f.write("# 🛠 Refactor Report\n\n")
        f.write("## 🔄 Refactored Forecast Path References\n")
        for file, line, old, new in refactor_log:
            f.write(f"- `{file}`: Line {line}\n")
            f.write(f"  - Old: `{old}`\n")
            f.write(f"  - New: `{new}`\n\n")
        f.write("---\n")
        f.write("## ✅ Test Outcomes\n")
        f.write("```\n")
        f.write(test_output)
        f.write("\n```\n")

def main():
    print("🔍 Scanning forecast path logic...")
    forecast_folder = load_config_forecast_folder()
    refactor_log = []
    for file_path in TARGET_FILES:
        edits = audit_and_refactor(file_path, forecast_folder)
        refactor_log.extend(edits)

    print("🧪 Running unit tests...")
    test_output = run_tests()

    print("📝 Writing refactor_report.md...")
    write_report(refactor_log, test_output)

    print("✅ Complete. Check refactor_report.md for summary.")

if __name__ == "__main__":
    main()
