import jsonlines
import tqdm

def extract_code(raw_text: str) -> str:
    """
    Extracts the first Python code block from a string that may contain markdown.
    """
    if "```python" in raw_text:
        start_marker = "```python\n"
    elif "```" in raw_text:
        start_marker = "```\n"
    else:
        # If no markdown fences are found, assume the whole text is code
        return raw_text.strip()

    try:
        # Take the content after the start marker
        code_part = raw_text.split(start_marker, 1)[1]
        # Take the content before the end marker
        clean_code = code_part.split("```", 1)[0]
        return clean_code.strip()
    except IndexError:
        # Handle cases where the format is unexpected
        return raw_text.strip()

# --- Main Script Logic ---
if __name__ == "__main__":
    input_file = "results/llama3_cot.jsonl"
    output_file = "results/llama3_cot_cleaned.jsonl"
    

    print(f"Reading from: {input_file}")
    print(f"Writing to:   {output_file}")

    cleaned_samples = []
    with jsonlines.open(input_file) as reader:
        for sample in reader:
            # Get the raw, messy completion string
            raw_completion = sample['completion']
            
            # Clean it using our function
            clean_completion = extract_code(raw_completion)
            
            # Update the 'completion' field in the sample
            sample['completion'] = clean_completion
            
            cleaned_samples.append(sample)

    # Write all the cleaned samples to the new file
    with jsonlines.open(output_file, mode='w') as writer:
        writer.write_all(cleaned_samples)

    print(f"\nDone! Created '{output_file}' with cleaned code.")