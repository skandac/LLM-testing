import jsonlines
import subprocess
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
from tqdm import tqdm

def get_prompt(task, mode="rim"):
    base_prompt = task["prompt"]
    if mode == "rim":
        return (
    "You are an expert Python programmer. Your task is to solve the following problem.\n"
            "Before writing any code, provide an inner monologue that follows these steps:\n"
            "1.  **Analyze the Request:** What is the core task? What are all the explicit requirements?\n"
            "2.  **Identify Potential Pitfalls:** What are the common edge cases, hidden assumptions, or tricky parts of this problem that a novice might miss?\n"
            "3.  **Draft a Solution with Commentary:** Write the code, explaining your logic and choices in comments.\n"
            "4.  **Critically Test the Draft:** Mentally run through the test cases, especially those targeting the pitfalls you identified, and confirm your draft works.\n\n"
            "After your inner monologue, provide only the final, clean, and correct Python function.\n\n"
            f"**Problem:**\n{base_prompt}"
    )
    else:
        return base_prompt

def generate_ollama(model, prompt):
    cmd = ["ollama", "run", model, prompt]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout.strip()

def generate_hf(model_name, prompt):
    pipe = pipeline("text-generation", model=model_name, device_map="auto")
    return pipe(prompt, max_new_tokens=256, temperature=0.2)[0]["generated_text"]

def run_eval(input_file, output_file, model="llama3", mode="cot", backend="ollama"):
    with jsonlines.open(input_file) as reader, jsonlines.open(output_file, mode='w') as writer:
        for task in tqdm(reader, desc=f"{model}-{mode}"):
            prompt = get_prompt(task, mode)
            if backend == "ollama":
                completion = generate_ollama(model, prompt)
            else:
                completion = generate_hf(model, prompt)
            writer.write({
                "task_id": task["task_id"],
                "prompt": prompt,
                "completion": completion
            })

if __name__ == "__main__":
    run_eval("tasks.jsonl", "results/llama3_rim.jsonl", model="llama3", mode="rim", backend="ollama")
