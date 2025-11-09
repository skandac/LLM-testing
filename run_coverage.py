import json
import re
import subprocess
import os
import pandas as pd

# --- Configuration ---
SOLUTION_FILENAME = "temp_solution.py"
TEST_FILENAME = "temp_test.py"
COVERAGE_JSON = "coverage.json"
TASKS_FILE = "tasks.jsonl"
COMPLETIONS_FILE = "completions.jsonl"
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
    This is designed to get the "final corrected function."
    """
    # Regex to find all Python code blocks
    code_blocks = re.findall(r"```(python|Python)\n(.*?)```", completion_text, re.DOTALL)
    
    if code_blocks:
        # Return the content of the last code block found
        return code_blocks[-1][1]
    
    # Fallback: if no ```python``` block, look for simple ``` blocks
    code_blocks = re.findall(r"```\n(.*?)\n```", completion_text, re.DOTALL)
    if code_blocks:
        return code_blocks[-1]
        
    # Fallback: assume the completion is *just* code if no blocks
    # This is a bit risky but can work for simple cases
    if "def " in completion_text and "```" not in completion_text:
        return completion_text
        
    print(f"Warning: Could not extract code from completion text: {completion_text[:50]}...")
    return ""

def create_test_file(solution_code: str, test_asserts: str):
    """
    Creates a runnable test file and the solution file it imports.
    """
    # 1. Write the solution file to be tested
    with open(SOLUTION_FILENAME, 'w', encoding='utf-8') as f:
        f.write(solution_code)

    # 2. Create the test file content
    # We need to import all functions from the solution
    # and wrap the asserts in a test function.
    test_lines = test_asserts.strip().split('\n')
    indented_asserts = "\n".join([f"    {line}" for line in test_lines])
    
    test_file_content = f"""
from {SOLUTION_FILENAME.replace('.py', '')} import *

# Imports from solution might be needed here (e.g., math, re)
# We can add them from the solution code
{os.linesep.join([line for line in solution_code.split(os.linesep) if line.startswith('import ')])}

def test_main():
{indented_asserts}
"""
    
    # 3. Write the test file
    with open(TEST_FILENAME, 'w', encoding='utf-8') as f:
        f.write(test_file_content)

def run_tests_and_coverage() -> tuple:
    """
    Runs pytest with coverage, parses the JSON report, and returns results.
    """
    # Run pytest
    # --cov=temp_solution: Target the solution file for coverage
    # --cov-report=json:Output coverage data as JSON
    # We use capture_output=True to hide pytest's output unless it fails
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
    
    # Did the tests pass?
    tests_passed = result.returncode == 0
    
    # Initialize coverage results
    line_coverage = 0.0
    branch_coverage = 0.0
    
    # Parse coverage JSON
    try:
        with open(COVERAGE_JSON, 'r') as f:
            cov_data = json.load(f)
            
        totals = cov_data.get("totals", {})
        
        # Line Coverage
        if totals.get("num_statements", 0) > 0:
            line_coverage = totals.get("percent_covered", 0.0)
        
        # Branch Coverage
        if totals.get("num_branches", 0) > 0:
            branch_coverage = totals.get("percent_covered_branches", 0.0)
        else:
            # If no branches, it's 100% "covered" (or N/A)
            branch_coverage = 100.0 
            
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error parsing coverage file: {e}")
        if tests_passed:
            # Code might have 100% coverage but no statements (e.g., empty file)
            # Check if solution file was empty
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
    print("Loading tasks and completions...")
    tasks = load_jsonl(TASKS_FILE)
    completions = load_jsonl(COMPLETIONS_FILE)
    
    if not tasks or not completions:
        print(f"Error: Could not load {TASKS_FILE} or {COMPLETIONS_FILE}.")
        print("Please make sure these files exist and are in the correct .jsonl format.")
        return

    print(f"Found {len(tasks)} tasks and {len(completions)} completions.")
    
    report_data = []

    for task_id, completion_item in completions.items():
        if task_id not in tasks:
            print(f"Skipping {task_id}: No matching task found in {TASKS_FILE}.")
            continue
        
        task_item = tasks[task_id]
        
        # 1. Extract code
        solution_code = extract_final_code(completion_item['completion'])
        if not solution_code:
            print(f"Skipping {task_id}: Could not extract solution code.")
            continue
            
        test_asserts = task_item['test']
        
        # 2. Create files
        create_test_file(solution_code, test_asserts)
        
        # 3. Run tests and coverage
        passed, line_cov, branch_cov = run_tests_and_coverage()
        
        # 4. Store results
        report_data.append({
            "Problem": task_id,
            "Tests Passed": "All" if passed else "FAIL",
            "Line %": line_cov,
            "Branch %": branch_cov,
        })
        
        print(f"Processed {task_id}: Passed={passed}, Line={line_cov}%, Branch={branch_cov}%")

    # 5. Clean up temporary files
    cleanup_files()
    
    # 6. Generate final report
    if not report_data:
        print("No results to report.")
        return

    df = pd.DataFrame(report_data)
    
    # Add the interpretation column (as a placeholder)
    df["Notes"] = "" # You will fill this in manually
    
    # Calculate the metric from the assignment for choosing problems
    # Metric: |(%test - %branch-coverage)| * %test
    # Let's assume %test = 100.0 if "All", 0.0 if "FAIL"
    def calculate_metric(row):
        test_pct = 100.0 if row['Tests Passed'] == 'All' else 0.0
        return abs(test_pct - row['Branch %']) * (test_pct / 100.0)
        
    df['Selection Metric'] = df.apply(calculate_metric, axis=1)
    df = df.sort_values(by="Selection Metric", ascending=False)

    print("\n--- Baseline Coverage Report ---")
    print(df.to_markdown(index=False))
    print("\n")
    
    # Recommend the top 2 problems
    print("Based on your metric, the best problems to choose for the next part are:")
    print(f"1. {df.iloc[0]['Problem']} (Metric: {df.iloc[0]['Selection Metric']:.1f})")
    print(f"2. {df.iloc[1]['Problem']} (Metric: {df.iloc[1]['Selection Metric']:.1f})")


if __name__ == "__main__":
    main()