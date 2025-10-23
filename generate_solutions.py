import argparse
import json
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

# Define the prompt templates
PROMPT_TEMPLATES = {
    "cot": """{base_prompt}

# Let's think step by step and then write a correct Python function.
""",
    "self-debug": """{base_prompt}
# Step 1: Write a draft solution.
# Step 2: Check it against test cases, including edge cases, and fix any mistakes.
# Step 3: Return the final corrected function.
"""
}

def main():
    # --- 1. Set up command-line argument parsing ---
    parser = argparse.ArgumentParser(description="Generate model completions for HumanEval tasks.")
    parser.add_argument("--model_name", type=str, required=True, help="Name or path of the Hugging Face model (e.g., 'codellama/CodeLlama-7b-hf').")
    parser.add_argument("--tasks_file", type=str, required=True, help="Path to the input tasks.jsonl file.")
    parser.add_argument("--output_file", type=str, required=True, help="Path to save the output jsonl file.")
    parser.add_argument("--prompt_style", type=str, choices=['cot', 'self-debug'], required=True, help="The prompt style to use ('cot' or 'self-debug').")
    args = parser.parse_args()

    # --- 2. Load Model and Tokenizer ---
    print(f"Loading model: {args.model_name}...")
    # Check if GPU is available and set the device
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")
    
    # New code with 4-bit quantization

    # Old code
    tokenizer = AutoTokenizer.from_pretrained(args.model_name)
    model = AutoModelForCausalLM.from_pretrained(args.model_name).to(device)
    
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # --- 3. Process Tasks and Generate Completions ---
    print(f"Processing tasks from {args.tasks_file}...")
    prompt_template = PROMPT_TEMPLATES[args.prompt_style]

    with open(args.tasks_file, 'r') as infile, open(args.output_file, 'w') as outfile:
        for line in infile:
            task = json.loads(line)
            task_id = task["task_id"]
            base_prompt = task["prompt"]
            
            # Format the full prompt using the chosen template
            full_prompt = prompt_template.format(base_prompt=base_prompt)
            
            # Tokenize the input
            inputs = tokenizer(full_prompt, return_tensors="pt").to(device)

            # Generate the completion
            outputs = model.generate(
                **inputs,
                max_new_tokens=512, # Adjust as needed
                temperature=0.7,
                do_sample=True
            )
            
            # Decode the generated text, removing the prompt part
            full_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
            completion = full_text[len(full_prompt):].strip()

            # Prepare the result and write to the output file
            result = {
                "task_id": task_id,
                "prompt": full_prompt,
                "completion": completion
            }
            outfile.write(json.dumps(result) + "\n")
            print(f"Generated completion for {task_id}")

    print(f"\n✅ All tasks processed. Output saved to {args.output_file}")

if __name__ == "__main__":
    main()