import jsonlines

with jsonlines.open("results/llama3_cot.jsonl") as reader:
    for i, record in enumerate(reader):
        print(f"{record['task_id']}:\n{record['completion']}\n{'-'*50}")
