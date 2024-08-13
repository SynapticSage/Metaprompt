# Metaprompt

Metaprompt is a repository for productivity-enhancing metaprompts. This repository will expand over time to include various forms of metaprompting. 

Currently, it includes:

- `apply` - a script for applying prompts to a list of text files using the `google.generativeai` library.

## Features

- Generate responses to prompts for a list of text files.
- Interactively confirm and edit the output.
- Save and load history using shelve.
- Expand folders to process all files within them.

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/yourusername/metaprompt.git
    cd metaprompt
    ```

2. Install the required dependencies:
    ```sh
    pip install .
    ```

## Usage

The main script in this repository is `apply.py`. It applies a prompt to a list of text files and generates responses using the `google.generativeai` library.

### Examples of Use Cases

- Generating READMEs for a sequence of files by applying a specific prompt at the start of each file.
- Generating summaries for a sequence of files.
- Drafting email responses to a list of emails.
- Drafting responses to customer reviews.

### Command Line Arguments

- `text_files`: A list of text files to process.
- `core`: The core conversation script to execute from the `./core` folder  - these are files exported from 'aistudio.google.com'.
- `prompt`: The prompt to apply to each file.
- `append`: A string to append to the output filename.
- `newprompt_on_break`: A flag to prompt for a new prompt on break.
- `prepend`: A string/folder to prepend to the output filename.
- `yes`: Automatically confirm all prompts.
- `editor`: The editor to use for interactive mode (default: `nvim`).
- `persist`: The file location to persist the shelve dictionary.
- `ignore_checkpoint`: A flag to ignore the checkpoint file.

### Example Usage

```sh
python apply.py data/text.txt core_example.py --prompt "Generate a response to this text" --yes --newprompt_on_break 
```

This command processes the `data/text.txt` file using the `core_example.py` script and applies the prompt "Generate a response to this text". The `--yes` flag automatically confirms all prompts.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or new features.

## License

This project is licensed under the MIT License.
