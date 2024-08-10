# Metaprompt

Metaprompt is a repository for productivity-enhancing metaprompts. This repository will expand over time to include various metaprompting endeavors. Currently, it includes a script for applying prompts to a list of text files using the `google.generativeai` library.

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
    pip install -r requirements.txt
    ```

## Usage

The main script in this repository is `prompt_cycle.py`. It applies a prompt to a list of text files and generates responses using the `google.generativeai` library.

### Command Line Arguments

- `text_files`: A list of text files to process.
- `core`: The core conversation script to execute from the `./core` folder.
- `prompt`: The prompt to apply to each file.
- `append`: A string to append to the output filename.
- `interact`: A flag to interactively confirm and edit the output.
- `editor`: The editor to use for interactive mode (default: `nvim`).
- `persist`: The file location to persist the shelve dictionary.
- `ignore_checkpoint`: A flag to ignore the checkpoint file.

### Examples of Use Cases

- Generating READMEs for a sequence of files by applying a specific prompt at the start of each file.
- Generating summaries for a sequence of files.
- Drafting email responses to a list of emails.
- Drafting responses to customer reviews.

### Example Usage

```sh
python prompt_cycle.py data/text.txt core_example.py --prompt "Generate a response to this text" --yes
```

This command processes the `data/text.txt` file using the `core_example.py` script and applies the prompt "Generate a response to this text". The `--yes` flag automatically confirms all prompts.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or new features.

## License

This project is licensed under the MIT License.
