import json
import re
import subprocess
import os
import pandas as pd

# --- Configuration ---
# 1. ADD YOUR 4 JSONL FILENAMES HERE
COMPLETION_FILES_TO_TEST = [
    "deepseek_cot_output.jsonl",
    "deepseek_selfdebug_output.jsonl",
    "results/llama_cot.jsonl",
    "results/llama_selfdebug.jsonl",
]

TASKS_FILE = "tasks.jsonl"
SOLUTION_FILENAME = "temp_solution.py"
TEST_FILENAME = "temp_test.py"
COVERAGE_JSON = "coverage.json"
# ---------------------

def load_jsonl(filename: str) -> dict:
    """Loads a .jsonl file and returns a dictionary keyed by task_id."""
    data = {}
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                item = json.loads(line)
                data[item['task_id']] = item
            except json.JSONDecodeError as e:
                print(f"Skipping bad line in {filename}: {e}")
    return data

def extract_final_code(completion_text: str) -> str:
    """
    Extracts the *last* Python code block from the completion string.
    """
    code_blocks = re.findall(r"```(python|Python)\n(.*?)```", completion_text, re.DOTALL)
    if code_blocks:
        return code_blocks[-1][1]
    code_blocks = re.findall(r"```\n(.*?)\n```", completion_text, re.DOTALL)
    if code_blocks:
        return code_blocks[-1]
    if "def " in completion_text and "```" not in completion_text:
        return completion_text
    print(f"Warning: Could not extract code from completion text: {completion_text[:50]}...")
    return ""

def create_test_file(solution_code: str, test_asserts: str):
    """
    Creates a runnable test file and the solution file it imports.
    """
    with open(SOLUTION_FILENAME, 'w', encoding='utf-8') as f:
        f.write(solution_code)

    test_lines = test_asserts.strip().split('\n')
    indented_asserts = "\n".join([f"    {line}" for line in test_lines])
    
    test_file_content = f"""
from {SOLUTION_FILENAME.replace('.py', '')} import *
{os.linesep.join([line for line in solution_code.split(os.linesep) if line.startswith('import ')])}

def test_main():
{indented_asserts}
"""
    with open(TEST_FILENAME, 'w', encoding='utf-8') as f:
        f.write(test_file_content)

def run_tests_and_coverage() -> tuple:
    """
    Runs pytest with coverage, parses the JSON report, and returns results.
    """
    result = subprocess.run(
        [
            "pytest",
            f"--cov={SOLUTION_FILENAME.replace('.py', '')}",
            f"--cov-report=json:{COVERAGE_JSON}",
            TEST_FILENAME
        ],
        capture_output=True,
        text=True
    )
    
    tests_passed = result.returncode == 0
    line_coverage = 0.0
    branch_coverage = 0.0
    
    try:
        with open(COVERAGE_JSON, 'r') as f:
            cov_data = json.load(f)
        totals = cov_data.get("totals", {})
        if totals.get("num_statements", 0) > 0:
            line_coverage = totals.get("percent_covered", 0.0)
        if totals.get("num_branches", 0) > 0:
            branch_coverage = totals.get("percent_covered_branches", 0.0)
        else:
            branch_coverage = 100.0
    except (FileNotFoundError, json.JSONDecodeError):
        if tests_passed:
            with open(SOLUTION_FILENAME, 'r') as sf:
                if not sf.read().strip():
                    line_coverage = 100.0
                    branch_coverage = 100.0

    return tests_passed, round(line_coverage, 1), round(branch_coverage, 1)

def cleanup_files():
    """Removes temporary files."""
    for f in [SOLUTION_FILENAME, TEST_FILENAME, COVERAGE_JSON, ".pytest_cache"]:
        if os.path.exists(f):
            if os.path.isdir(f):
                import shutil
                shutil.rmtree(f)
            else:
                os.remove(f)

def main():
    print("Loading tasks...")
    try:
        tasks = load_jsonl(TASKS_FILE)
    except FileNotFoundError:
        print(f"Error: Could not find {TASKS_FILE}. Make sure it's in the same directory.")
        return
        
    all_report_data = []

    # --- Outer loop for each completion file ---
    for completion_filename in COMPLETION_FILES_TO_TEST:
        print(f"\n--- Processing File: {completion_filename} ---")
        try:
            completions = load_jsonl(completion_filename)
        except FileNotFoundError:
            print(f"Warning: Could not find file {completion_filename}. Skipping.")
            continue
            
        if not completions:
            print(f"Warning: No completions found in {completion_filename}. Skipping.")
            continue

        # --- Inner loop for each problem in the file ---
        for task_id, completion_item in completions.items():
            if task_id not in tasks:
                print(f"Skipping {task_id}: No matching task found in {TASKS_FILE}.")
                continue
            
            task_item = tasks[task_id]
            
            solution_code = extract_final_code(completion_item['completion'])
            if not solution_code:
                print(f"Skipping {task_id}: Could not extract solution code.")
                continue
                
            test_asserts = task_item['test']
            create_test_file(solution_code, test_asserts)
            
            passed, line_cov, branch_cov = run_tests_and_coverage()
            
            # Add the result to our master list
            all_report_data.append({
                "Source File": completion_filename, # <-- NEW COLUMN
                "Problem": task_id,
                "Tests Passed": "All" if passed else "FAIL",
                "Line %": line_cov,
                "Branch %": branch_cov,
            })
            
            print(f"  Processed {task_id}: Passed={passed}, Line={line_cov}%, Branch={branch_cov}%")

    # 5. Clean up temporary files
    cleanup_files()
    
    # 6. Generate final report
    if not all_report_data:
        print("No results to report. Did you update COMPLETION_FILES_TO_TEST?")
        return

    print("\n--- Combined Baseline Coverage Report ---")
    
    df = pd.DataFrame(all_report_data)
    
    df["Notes"] = "" # You can fill this in manually later if needed
    
    def calculate_metric(row):
        test_pct = 100.0 if row['Tests Passed'] == 'All' else 0.0
        return abs(test_pct - row['Branch %']) * (test_pct / 100.0)
        
    df['Selection Metric'] = df.apply(calculate_metric, axis=1)
    
    # Sort by the file, then by the metric
    df = df.sort_values(by=["Source File", "Selection Metric"], ascending=[True, False])

    print(df.to_markdown(index=False))
    print("\n")


if __name__ == "__main__":
    main()