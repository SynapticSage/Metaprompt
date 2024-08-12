#!/usr/bin/env python
"""
METAPROMPT, google ai studio meta prompting

`prompt_cycle.py` is a script that applies a prompt to a list of text files.
The script uses the `google.generativeai` library to generate responses to the
prompt. The script takes the following arguments:

- `text_files`: A list of text files to process.
- `core`: The core conversation script to execute from the `./core` folder.
- `prompt`: The prompt to apply to each file.
- `append`: A string to append to the output filename.
- `interact`: A flag to interactively confirm and edit the output.
- `editor`: The editor to use for interactive mode (default: `nvim`).
- `persist`: The file location to persist the shelve dictionary.
- `ignore_checkpoint`: A flag to ignore the checkpoint file.

# Examples of use cases
- generating readmes for huge sequence of files - we want to apply a certain
  prompt at the start of each file, and then possibly tweak the output.
  [put code files in a folder, and point the cycler to it]
- generating a summaries of a huge sequence of files
- drafting email responses to a huge list of emails we need to respond to
- drafting responses to a huge list of customer reviews
"""


import os
import argparse
import shelve
from rich import print
from metaprompt import utils
from tqdm import tqdm


# Set up argparse
def main(*args):
    """
    see file header for details
    """

    parser = argparse.ArgumentParser(description='Process some files with generative AI.')
    parser.add_argument('text_files', nargs='+', help='List of text files to process')
    parser.add_argument('core', nargs='?', type=str, help='Core conversation script to execute from the ./core folder')
    parser.add_argument('--prompt', required=False, help='Prompt to apply to each file') # TODO: if not provided, check stdin, and if still not, ask for it
    parser.add_argument('--newprompt_on_break', action='store_true', help='Prompt for a new prompt on break')
    parser.add_argument('--append', default="_work", help='String to append to the output filename')
    parser.add_argument('--prepend', default="../output/", help='String/folder to prepend to the output filename')
    parser.add_argument('--yes', '-y', action='store_true', help='Automatically confirm all prompts')
    parser.add_argument('--editor', default='nvim', help='Editor to use for interactive mode (default: nvim)')
    parser.add_argument('--persist', default="database/{CORE}", required=False, help='File location to persist the shelve dictionary')
    parser.add_argument('--ignore_checkpoint', action='store_true', help='Ignore the checkpoint file')
    parser.add_argument('--skipN', type=int, default=0, help='Skip the first N files')
    ynmc_help = """
    y: yes
    m: modify prompt - edit the response and then decision
    c: modify content - and then prompt
    q: quit
    """

    args = parser.parse_args(*args)
    if args.core is None:
        args.core = ("core/default.py" if os.path.exists("core/default.py") else
                     "core/core_example.py")
        # follow links
        args.core = os.path.realpath(args.core)

    # Execute the core script
    # exec(utils.get_core_script(args), globals())
    utils.run_core_script(args)
    chat_session = globals()['chat_session']
    model = globals()['model']
    history = chat_session.history
    globals()['args'] = args

    # Load or create the shelve dictionary, first access of the shelf
    history = utils.load_and_combine_history(args, history)

    # Expand out any folders
    args.text_files = utils.expand_folders(args.text_files)

    # Start chat session with history
    chat_session = model.start_chat(history=history)

    # Process each file
    for iT, text_file in tqdm(enumerate(args.text_files), 
                          desc="Processing files", total=len(args.text_files)):

        if iT < args.skipN:
            print(f"[yellow]Skipping {text_file}[/yellow]")
            continue

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


        args.prompt = args.prompt if args.prompt \
                             else input("Please enter a prompt:\n")

        # Interactively confirm, and if not, edit output
        start_index = len(chat_session.history)
        apply_prompt = True
        is_okay = ''
        skipped = False
        while True:

            iC = len(chat_session.history)

            if apply_prompt:
                # Determine what to say
                inst = "user_request" if iC == start_index else "user_response"
                content = args.prompt if iC == start_index else response_text \
                if 'response_text' in locals() \
                else None
                if content is None:
                    raise ValueError("Content is None. This should not happen.")
                message_to_agent = (
                   f"""
                   {f'<content>{file_content}</content>' if iC == start_index else ''}
                   """
                   f'<{inst}>{content}</{inst}>\n'
                   )
                # import pdb; pdb.set_trace()
                # Say it and get the response
                response = chat_session.send_message(message_to_agent)
                response_text = response.parts[0].text
            
            print(f"[red]{message_to_agent}[/red]")
            print(f"[blue]Token count: {response.usage_metadata.candidates_token_count}[/blue]")
            print(f"[green]{response_text}[/green]")

            print(ynmc_help) if iT == 0 else None
            is_okay = input("Is this okay? (y/m/c/q) [d/p]: ").strip().lower() \
                            if not args.yes else 'y'

            if is_okay.startswith('y'): # if okay, break
                break
            elif is_okay.startswith('m'): # if modify, edit the response
                apply_prompt = False
                response_text = utils.edit_content_with_editor(
                    message_to_agent, response_text, args.editor)
            elif is_okay.startswith('r'): # if return, edit the response and return to prompt
                apply_prompt = True
                prompt = utils.edit_content_with_editor(
                    message_to_agent, response_text, args.editor)
            elif is_okay.startswith('q'):
                print("Quitting...")
                sys.exit()
            elif is_okay.startswith('s'): # if skip, skip this file
                print("Skipping...")
                skipped = True
                break

            if 'd' in is_okay:
                import pdb; pdb.set_trace()
            if 'p' in is_okay:
                # toggle change prompt on break
                args.newprompt_on_break = not args.newprompt_on_break

        # Save the current state to the shelve dictionary
        if not skipped:

            with shelve.open(args.persist) as shelf:
                input_indices = slice(start_index, len(chat_session.history) - 2, 2)
                output_indices = slice(start_index + 1, len(chat_session.history) - 1, 2)
                if len(output_indices) == 0:
                    import warnings
                    warnings.warn(f"Skipping {text_file} as no output was generated.")
                    # TODO: add an option where when this occurs, users can open a
                    # file dialog to select a file to save the output
                shelf['history'] = chat_session.history
                shelf[text_file] = {'input_index':  input_indices,
                                    'output_index': output_indices}

            # Save the output with appended string
            output_filename = utils.create_output_filename(text_file, args)
            if not os.path.exists(output_filename):
                os.makedirs(os.path.dirname(output_filename))
            with open(output_filename, 'w') as out_f:
                divider = ("\n"+(79*"-")+"\n")
                aggregated_response = divider.join(chat_session.history[start_index:len(chat_session.history)])
                out_f.write(response_text) 

        # If prompt on break, display the upcoming `text_file` and ask for a new
        # prompt
        if args.newprompt_on_break:
            print(f"[yellow]Upcoming file: {text_file}[/yellow]")
            args.prompt = input("Please enter a new prompt:\n")


    print("Processing complete. Output files created.")

if __name__ == '__main__':
    import sys
    main(sys.argv[1:])
