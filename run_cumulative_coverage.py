import json
import re
import subprocess
import os
import pandas as pd
import sys

# --- Configuration ---
SOLUTION_FILENAME = "temp_solution.py"
BENCHMARK_TEST_FILENAME = "temp_benchmark_test.py"
COVERAGE_JSON = "coverage.json"
TASKS_FILE = "tasks.jsonl"
COMPLETIONS_FILE = "completions.jsonl"
# ---------------------

def load_jsonl(filename: str) -> dict:
    """Loads a .jsonl file and returns a dictionary keyed by task_id."""
    data = {}
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            item = json.loads(line)
            data[item['task_id']] = item
    return data

def extract_final_code(completion_text: str) -> str:
    """Extracts the *last* Python code block from the completion string."""
    code_blocks = re.findall(r"```(python|Python)\n(.*?)```", completion_text, re.DOTALL)
    if code_blocks:
        return code_blocks[-1][1]
    code_blocks = re.findall(r"```\n(.*?)\n```", completion_text, re.DOTALL)
    if code_blocks:
        return code_blocks[-1]
    return ""

def write_solution_file(task_id: str, tasks: dict, completions: dict):
    """Writes the solution code to the temporary solution file."""
    completion_item = completions[task_id]
    solution_code = extract_final_code(completion_item['completion'])
    
    # This is a fix for HumanEval/12, which needs 'import re'
    if "import re" not in solution_code and "re.sub" in solution_code:
        solution_code = "import re\n" + solution_code
        
    with open(SOLUTION_FILENAME, 'w', encoding='utf-8') as f:
        f.write(solution_code)
    return solution_code

def create_benchmark_test_file(task_id: str, tasks: dict, solution_code: str):
    """Creates a runnable benchmark test file."""
    test_asserts = tasks[task_id]['test']
    test_lines = test_asserts.strip().split('\n')
    indented_asserts = "\n".join([f"    {line}" for line in test_lines])
    
    # Add any imports from the solution file (like 'import math')
    imports = [line for line in solution_code.split(os.linesep) if line.startswith('import ')]
    
    test_file_content = f"""
from {SOLUTION_FILENAME.replace('.py', '')} import *
import pytest
{os.linesep.join(imports)}

def test_benchmark():
{indented_asserts}
"""
    with open(BENCHMARK_TEST_FILENAME, 'w', encoding='utf-8') as f:
        f.write(test_file_content)

def run_tests_and_coverage(test_files_to_run: list) -> tuple:
    """Runs pytest with coverage on a list of test files."""
    
    # Add the benchmark test to the list
    all_tests = [BENCHMARK_TEST_FILENAME] + test_files_to_run
    
    # Run pytest
    result = subprocess.run(
        [
            "pytest",
            f"--cov={SOLUTION_FILENAME.replace('.py', '')}",
            f"--cov-report=json:{COVERAGE_JSON}",
            "--cov-report=html", # Generate browseable HTML report
        ] + all_tests,
        capture_output=True,
        text=True
    )
    
    tests_passed = "All" if result.returncode == 0 else "FAIL"
    
    # Parse coverage JSON
    line_coverage = 0.0
    branch_coverage = 0.0
    missing_lines = ""
    
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
            
        # Get missing lines to help with prompting
        if "files" in cov_data:
            solution_file_data = cov_data["files"].get(SOLUTION_FILENAME, {})
            missing_lines = solution_file_data.get("missing_lines_str", "")
            
    except (FileNotFoundError, json.JSONDecodeError):
        pass

    return tests_passed, round(line_coverage, 1), round(branch_coverage, 1), missing_lines

def cleanup_files():
    """Removes temporary files."""
    for f in [SOLUTION_FILENAME, BENCHMARK_TEST_FILENAME, COVERAGE_JSON, ".pytest_cache"]:
        if os.path.exists(f):
            if os.path.isdir(f):
                import shutil
                shutil.rmtree(f)
            else:
                os.remove(f)

def main():
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} <task_id> [new_test_file1.py] [new_test_file2.py] ...")
        sys.exit(1)

    task_id = sys.argv[1]
    new_test_files = sys.argv[2:]
    
    print(f"--- Running Coverage for: {task_id} ---")
    
    try:
        tasks = load_jsonl(TASKS_FILE)
        completions = load_jsonl(COMPLETIONS_FILE)
    except FileNotFoundError as e:
        print(f"Error: Could not find {e.filename}. Make sure tasks.jsonl and completions.jsonl are in this directory.")
        sys.exit(1)

    if task_id not in tasks or task_id not in completions:
        print(f"Error: {task_id} not found in .jsonl files.")
        sys.exit(1)

    # 1. Write the solution file
    solution_code = write_solution_file(task_id, tasks, completions)
    
    # 2. Create the base benchmark test file
    create_benchmark_test_file(task_id, tasks, solution_code)

    # 3. Run tests and coverage
    passed, line_cov, branch_cov, missing = run_tests_and_coverage(new_test_files)
    
    print(f"Test Files Used: {[BENCHMARK_TEST_FILENAME] + new_test_files}")
    print(f"Tests Passed:  {passed}")
    print(f"Line Coverage: {line_cov}%")
    print(f"Branch Cov:    {branch_cov}%")
    
    if line_cov < 100:
        print(f"Missing Lines: {missing}")
        print("\nTo see details, open the 'htmlcov/index.html' file in your browser.")

    # Note: Cleanup is commented out so you can inspect htmlcov
    # cleanup_files() 
    print("--- Done ---")


if __name__ == "__main__":
    main()