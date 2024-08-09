"""
Install the Google AI Python SDK

$ pip install google-generativeai

See the getting started guide for more information:
https://ai.google.dev/gemini-api/docs/get-started/python
"""

import os
import argparse
import shelve
from rich import print
from src import utils

test = True
if test:
    import sys
    sys.argv = ["apply.py", "data/text.txt", "core_example.py", "--prompt", "Prompt text", "--append", "_work", "--interact", "--editor", "nvim", "--persist", "test.shelve"]

# Set up argparse
parser = argparse.ArgumentParser(description='Process some files with generative AI.')
parser.add_argument('text_files', nargs='+', help='List of text files to process')
parser.add_argument('core', nargs=1, type=str, help='Core conversation script to execute from the ./core folder')
parser.add_argument('--prompt', required=True, help='Prompt to apply to each file') # TODO: if not provided, check stdin, and if still not, ask for it
parser.add_argument('--append', default="_work", help='String to append to the output filename')
parser.add_argument('--interact', action='store_true', help='Interactively confirm and edit output')
parser.add_argument('--editor', default='nvim', help='Editor to use for interactive mode (default: nvim)')
parser.add_argument('--persist', default="{CORE}", required=True, help='File location to persist the shelve dictionary')
parser.add_argument('--ignore_checkpoint', action='store_true', help='Ignore the checkpoint file')

args = parser.parse_args()

# Execute the core script
exec(utils.get_core_script(args), globals())
history = locals()['history']
model = locals()['model']
chat_session = locals()['chat_session']

# Load or create the shelve dictionary
history = utils.load_and_combine_history(args, history)

# Start chat session with history
chat_session = model.start_chat(history=history)

# Process each file
for i_file, text_file in enumerate(args.text_files):

    # Check if the file has been processed before
    with shelve.open(args.persist) as shelf:
        if not args.ignore_checkpoint and text_file in shelf:
            input_index = shelf[text_file]['input_index']
            output_index = shelf[text_file]['output_index']
            input_text = chat_session.history[input_index].parts[0].text
            output_text = chat_session.history[output_index].parts[0].text
            print(f"[yellow]Processing {text_file}[/yellow]")
            print(f"Input: {input_text}")
            print(f"Output: {output_text}")
            print(f"[yellow]Skipping {text_file} as it has already been processed.[/yellow]")
            continue

    with open(text_file, 'r') as f:
        file_content = f.read()

    # APPLY the prompt to the file content
    prompt_with_content = f"{args.prompt}\n\n{file_content}"
    response = chat_session.send_message(prompt_with_content)
    response_text = response.parts[0].text

    # Interactively confirm, and if not, edit output
    if args.interact:
        while True:
            print(f"[red]{prompt_with_content}[/red]")
            print(f"[green]{response_text}[/green]")
            is_okay = input("Is this okay? (y/N): ").strip().lower()
            if is_okay == 'y':
                break
            elif is_okay.lower() == 'n':
                response_text = utils.edit_content_with_editor(
                    prompt_with_content, response_text, args.editor)
            else:
                continue

    # Save the output with appended string
    output_filename = f"{os.path.splitext(text_file)[0]}{args.append}{os.path.splitext(text_file)[1]}"
    with open(output_filename, 'w') as out_f:
        out_f.write(response_text)

    # Save the current state to the shelve dictionary
    with shelve.open(args.persist) as shelf:
        shelf['history'] = chat_session.history
        shelf[text_file] = {'input_index': len(chat_session.history) - 2, 'output_index': len(chat_session.history) - 1}

print("Processing complete. Output files created.")
