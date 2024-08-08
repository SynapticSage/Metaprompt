"""
Install the Google AI Python SDK

$ pip install google-generativeai

See the getting started guide for more information:
https://ai.google.dev/gemini-api/docs/get-started/python
"""

import os
import argparse
import tempfile
import subprocess
from rich import print
import google.generativeai as genai

# Configure the API key
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# Create the model
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
    model_name="gemini-1.5-pro-exp-0801",
    generation_config=generation_config,
    # safety_settings = Adjust safety settings
    # See https://ai.google.dev/gemini-api/docs/safety-settings
    system_instruction="You are a professional software engineer whose role is to grok code libraries you are given. You created a nested hierarchical list of sections of the code where the leaves of the tree are functions and classes. After grokking your job is to create a README.md overviewing the set of scripts a user can run, but not going into too much detail about any one script. Thereafter, you will be called upon to create one README per script.",
)

chat_session = model.start_chat(
    history=[...]
)

# Set up argparse
parser = argparse.ArgumentParser(description='Process some files with generative AI.')
parser.add_argument('text_files', nargs='+', help='List of text files to process')
parser.add_argument('--prompt', required=True, help='Prompt to apply to each file')
parser.add_argument('--append', required=True, help='String to append to the output filename')
parser.add_argument('--interact', action='store_true', help='Interactively confirm and edit output')
parser.add_argument('--editor', default='nvim', help='Editor to use for interactive mode (default: nvim)')

args = parser.parse_args()

# Function to write content to a temporary file and open it with an editor
def edit_content_with_editor(prompt, response, editor):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".tmp") as tmpfile:
        tmpfile.write(f"# {prompt}\n\n{response}".encode('utf-8'))
        tmpfile_path = tmpfile.name

    subprocess.run([editor, tmpfile_path])

    with open(tmpfile_path, 'r') as tmpfile:
        edited_content = "".join([line for line in tmpfile if not line.startswith("#")])

    os.remove(tmpfile_path)
    return edited_content

# Process each file
for text_file in args.text_files:
    with open(text_file, 'r') as f:
        file_content = f.read()
    
    # Apply the prompt to the file content
    prompt_with_content = f"{args.prompt}\n\n{file_content}"
    response = chat_session.send_message(prompt_with_content)
    response_text = response.parts[0].text

    if args.interact:
        while True:
            print(f"[red]{prompt_with_content}[/red]")
            print(f"[green]{response_text}[/green]")
            is_okay = input("Is this okay? (y/N): ").strip().lower()
            if is_okay == 'y':
                break
            else:
                response_text = edit_content_with_editor(prompt_with_content, response_text, args.editor)
    
    # Save the output with appended string
    output_filename = f"{os.path.splitext(text_file)[0]}{args.append}{os.path.splitext(text_file)[1]}"
    with open(output_filename, 'w') as out_f:
        out_f.write(response_text)

print("Processing complete. Output files created.")
