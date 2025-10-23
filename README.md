tasks.jsonl is the dataset that i have extracted from humaneval github repo (https://github.com/openai/human-eval)

generate_llm.py contains the main code which uses the task.json and input prompt to get the output for llama model
you may need to install the ollama locally before running this file 

change the prompts and file names according to the user standards 
you can use command "python generate_llm.py" to run the above code and generate json files 

generate_solutions.py contains the main code to generate the output jsonl file for deepseek model 

python generate_solutions.py \                                                    
    --model_name "deepseek-ai/deepseek-coder-1.3b-instruct" \
    --tasks_file "tasks.jsonl" \
    --output_file "deepseek_cot_output.jsonl" \
    --prompt_style "cot"

you can change the above for self-debug or cot style prompting strategies 

Note: I have used deepseek 1.3B parameter lower model cause of laptop capacity

The output jsonl files will be stored in /result/ dir 

check.py can be used to check if the json files have the proper code solutions to the prompt given that we have provided 
to check if json file is generated properly

clean_results.py is used to clean the json files generated after LLM has generated the output for any additional lines of text before code to prevent syntax errors 

to calculate pass@1 metric we can use the json file that is generated and run on any LLM to see which all evaluations are failing 

Results


<img width="427" height="202" alt="image" src="https://github.com/user-attachments/assets/51ed7b23-33db-4823-9f77-fa7e36c8899b" />

<img width="333" height="260" alt="image" src="https://github.com/user-attachments/assets/110945d1-f5ab-49a3-b375-5cc883dc5db0" />


