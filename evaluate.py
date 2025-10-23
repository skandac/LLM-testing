import json
import jsonlines
import math

def safe_exec(code, test):
    try:
        local_env = {}
        exec(code, {}, local_env)
        exec(test, {}, local_env)
        return True, None
    except Exception as e:
        return False, str(e)

def compute_passk(results, k=1):
    n = len(results)
    correct = sum(r["passed"] for r in results)
    if correct == n:
        return 1.0
    return 1 - math.comb(n - correct, k) / math.comb(n, k)

def evaluate_model(generated_file, tasks_file, report_file, k_values=[1, 5]):
    tasks = {t["task_id"]: t for t in jsonlines.open(tasks_file)}
    results = []
    with jsonlines.open(generated_file) as reader:
        for record in reader:
            task = tasks[record["task_id"]]
            passed, error = safe_exec(record["completion"], task["test"])
            results.append({
                "task_id": task["task_id"],
                "passed": passed,
                "error": error
            })
    metrics = {f"pass@{k}": compute_passk(results, k) for k in k_values}
    with open(report_file, "w") as f:
        json.dump({"metrics": metrics, "results": results}, f, indent=2)
    print(metrics)

if __name__ == "__main__":
    evaluate_model("results/llama3_cot.jsonl", "tasks.jsonl", "results/report_llama3_cot.json")
    evaluate_model("results/llama3_selfdebug.jsonl", "tasks.jsonl", "results/report_llama3_selfdebug.json")
