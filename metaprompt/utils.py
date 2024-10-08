import os
import shelve
import subprocess
import tempfile
from google.generativeai.generative_models import ChatSession
from rich import print
import argparse

folder = os.path.dirname(__file__)
corefolder = os.path.abspath(os.path.join(folder, '..', 'core'))

def get_core_script(args):
    """
    Get the core script from the specified path.
    """

    if isinstance(args.core, (list, tuple)):
        core = args.core[0]
    else:
        core = args.core
    core_script_path = os.path.join('core', core)
    if os.path.isfile(core_script_path):
        with open(core_script_path) as f:
            file_contents = f.read()
    else:
        raise FileNotFoundError(f"Core script {core_script_path} not found.")

    return file_contents

def run_core_script(args):
    """
    runs core script using IPython run -i 

    and then place the variables into globals()
    """
    from IPython import get_ipython
    core = os.path.join(corefolder, args.core)
    if not os.path.exists(core):
        raise FileNotFoundError(f"Core script {core} not found.")
    try:
        ipython = get_ipython()
        ipython.run_line_magic(f'run', f'-i "{core}"')
        assert 'chat_session' in ipython.user_ns, f"chat_session not found in core script {core}"
        for var in ipython.user_ns:
            globals()[var] = ipython.user_ns[var]
    except Exception as e:
        try:
            exec(open(core).read())
            assert 'chat_session' in locals(), f"chat_session not found in core script {core}"
            for var in locals():
                globals()[var] = locals()[var]
        except Exception as e:
            raise e

def load_and_combine_history(args, 
                history:list=[], 
                append:bool=False, 
                prepend:bool=False)->list:
    """
    Load and combine the history from the shelve file with 
    the core/current history.

    Inputs
    ------
    args : argparse.Namespace
        The command line arguments.
    history : list
        the history to load
    append : bool
        append the history to the existing history
    prepend : bool
        prepend the history to the existing history

    Notes
    -----
    if append and prepend are both True, append takes precedence
    if append and prepend are both False, the longer history takes precedence
    """
    args.persist = string_substitute(args.persist, args)
    args.persist = ".".join(args.persist.split('.')[:-1]) + '.shelve'
    args.persist = os.path.abspath(args.persist)
    if os.path.dirname(args.persist) and not os.path.exists(os.path.dirname(args.persist)): 
        os.makedirs(os.path.dirname(args.persist))
    with shelve.open(args.persist) as shelf:
        import google.ai # used in unpickling
        if 'history' in shelf:
            if append:
                history = shelf['history'] + history
            elif prepend:
                history = history + shelf['history']
            else: # accept the longer history
                shelf_has_more_history = len(shelf['history']) > len(history)
                history = shelf['history'] if shelf_has_more_history else history
    return history

def edit_content_with_editor(prompt, response, editor):
    """
    Edit the content with the specified editor.
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=".tmp") as tmpfile:
        tmpfile.write(f"# {prompt}\n\n{response}".encode('utf-8'))
        tmpfile_path = tmpfile.name

    subprocess.run([editor, tmpfile_path])

    with open(tmpfile_path, 'r') as tmpfile:
        edited_content = "".join([line for line in tmpfile if not line.startswith("#")])

    os.remove(tmpfile_path)
    return edited_content

def expand_folders(text_files, sort=None):
    """
    Expand any folders in the list of files of args.text_files.

    If a folder is folder, use os.walk to get all files in the folder
    """
    expanded_files = []
    for text_file in text_files:
        if os.path.isdir(text_file):
            for root, _, files in os.walk(text_file):
                for file in files:
                    expanded_files.append(os.path.join(root, file))
        else:
            expanded_files.append(text_file)
    if sort == "acc" or sort == "forward" or sort == True:
        expanded_files = sorted(expanded_files)
    elif sort == "dec" or sort == "rev" or sort == "reverse":
        expanded_files = sorted(expanded_files, reverse=True)
    else:
        pass
    return expanded_files

def create_output_filename(text_file, args):
    """
    Create the output filename based on the input filename and the append/prepend strings.
    """
    output_filename = os.path.join(os.path.dirname(text_file), 
                        args.prepend + ".".join(text_file.split('.')[:-1]) + \
                        args.append + '.' + text_file.split('.')[-1])
    output_filename = string_substitute(output_filename, args)
    return output_filename

def string_substitute(string:str, args)->str:
    """
    Substitute the string with the globals() values. Can swap the following:
    {CORE} -> args.core
    {DATE} -> datetime.datetime.now

    Inputs
    ------
    string : str
        The string to substitute.
    args : argparse.Namespace
        The command line arguments.

    """
    import datetime
    if "{CORE}" in string:
        if isinstance(args.core, (list, tuple)):
            core = os.path.basename(args.core[0])
        else:
            core = os.path.basename(args.core)
        string = string.replace("{CORE}", core)
    if "{DATE} " in string:
        date = datetime.datetime.now()
        string = string.replace("{DATE}", date.today().strftime('%Y-%m-%d'))
    return string

def shelf(args):
    return shelve.open(args.persist)

def persist_text_file_conversation(args:argparse.Namespace,
                                   chat_session:ChatSession, 
                                   text_file:str,
                                   start_index:int,
                                   is_final:bool=False):
    """
    Persist the text file conversation to a shelve file.
    """
    with shelve.open(args.persist) as shelf:
        input_indices = slice(start_index, len(chat_session.history) - 2, 2)
        output_indices = slice(start_index + 1, len(chat_session.history) - 1, 2)
        slice_len = (output_indices.stop - 
                     output_indices.start)
        if slice_len < 0:
            # TODO: add an option where when this occurs, users can open a
            # file dialog to select a file to save the output
            import warnings
            warnings.warn("No conversation to save to shelve with slice={}".format(output_indices))
        else:
            print("Saving to shelve...")
            shelf['history'] = chat_session.history
            shelf[text_file] = {'input_index':  input_indices,
                                'output_index': output_indices}
            shelf[text_file]['final'] = is_final


def print_message(response):
    from rich.markdown import Markdown
    from rich.console import Console
    response_text = response.parts[0].text
    with Console() as console:
        console.print(f"[blue]Token count: {response.usage_metadata.candidates_token_count}[/blue]")
        # print(f"[blue]Token cost: {response.usage_metadata.candidates_token_count}[/blue]")
        console.print(f"[green]{response_text}[/green]")
