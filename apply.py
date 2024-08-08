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
import shelve
from rich import print

# Set up argparse
parser = argparse.ArgumentParser(description='Process some files with generative AI.')
parser.add_argument('text_files', nargs='+', help='List of text files to process')
parser.add_argument('core', nargs=1, required=True, help='Core conversation script to execute from the ./core folder')
parser.add_argument('--prompt', required=True, help='Prompt to apply to each file')
parser.add_argument('--append', default="_work", help='String to append to the output filename')
parser.add_argument('--interact', action='store_true', help='Interactively confirm and edit output')
parser.add_argument('--editor', default='nvim', help='Editor to use for interactive mode (default: nvim)')
parser.add_argument('--persist', default="{CORE}", required=True, help='File location to persist the shelve dictionary')

args = parser.parse_args()

# Execute the core script
core_script_path = os.path.join('core', args.core)
if os.path.isfile(core_script_path):
    with open(core_script_path) as f:
        exec(f.read(), globals())
else:
    raise FileNotFoundError(f"Core script {core_script_path} not found.")

# Load or create the shelve dictionary
if args.persist == "{CORE}":
    args.persist = f"{os.path.basename(args.core).split('.')[0]}.shelve"
if os.path.dirname(args.persist) and not os.path.exists(os.path.dirname(args.persist)): 
    os.makedirs(os.path.dirname(args.persist))
with shelve.open(args.persist) as shelf:
    if 'history' in shelf:
        history = shelf['history']
    else:
        # Ensure `history` is defined in the core script
        if 'history' not in globals():
            raise ValueError("The core script must define a `history` variable.")
        history = globals()['history']

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

# Start chat session with history
chat_session = model.start_chat(history=history)

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

    # Save the current state to the shelve dictionary
    with shelve.open(args.persist) as shelf:
        shelf['history'] = chat_session.history
        shelf[text_file] = {'input_index': len(chat_session.history) - 2, 'output_index': len(chat_session.history) - 1}

print("Processing complete. Output files created.")
