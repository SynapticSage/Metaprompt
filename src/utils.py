import os
import shelve
import subprocess
import tempfile


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
    if isinstance(args.core, (list, tuple)):
        core = args.core[0]
    else:
        core = args.core
    if args.persist == "{CORE}":
        args.persist = f"{os.path.basename(core).split('.')[0]}.shelve"
    if os.path.dirname(args.persist) and not os.path.exists(os.path.dirname(args.persist)): 
        os.makedirs(os.path.dirname(args.persist))
    with shelve.open(args.persist) as shelf:
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
    with tempfile.NamedTemporaryFile(delete=False, suffix=".tmp") as tmpfile:
        tmpfile.write(f"# {prompt}\n\n{response}".encode('utf-8'))
        tmpfile_path = tmpfile.name

    subprocess.run([editor, tmpfile_path])

    with open(tmpfile_path, 'r') as tmpfile:
        edited_content = "".join([line for line in tmpfile if not line.startswith("#")])

    os.remove(tmpfile_path)
    return edited_content
