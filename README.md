# LLM Context Generator

A simple script for generating a structured snapshot of a codebase that can be pasted into an LLM as context.

## What it does

Generates a text file containing a project’s directory tree and file contents, which can be pasted into an LLM.

You can filter out:
- files by extension type (e.g. `.js`, `.py`, etc.)
- files and directories by name using a `.llmignore` file (more details below)

The `.llmignore` file works in a similar way to a `.gitignore` file, hence the name. See more details below.


## How to Use

### 1. Copy the files

Copy `generate.py` and `.llmignore` files to the project root or a subdirectory (e.g. llm/).
- Both files must be in the same directory.
- You can rename `generate.py` to whatever you like but don't rename `.llmignore`.*

### 2. Configuration

Open the `generate.py` file in a text editor and edit the variables at the top of the script:

```bash
OUTPUT_FILE – name of the generated text file
INCLUDE_PROJECT_TREE – include directory tree in output
PROMPT_BEFORE – text prepended to the output
PROMPT_AFTER – text appended to the output
RESTRICT_EXTENSIONS – limit included file types when copying file contents (not in tree)
ALWAYS_IGNORE_FOLDERS – directories which are always excluded (both when copying file contents and in tree)
ROOT_MARKERS – files at project root level that allow the script to identify the project root
```

### 3. Ignore Rules (`.gitignore` & `.llmignore`)

In addition to limiting files by extension type, you can specify files and folders to ignore using `.gitignore` and `.llmignore` files.

The `.gitignore` file is primarily used to specify which files and folders git should ignore, however any files and folders in this file will also **automatically be ignored**, both when generating the project tree and copying file contents.

The `.llmignore` file works in a similar way to a `.gitignore` file (hence the name). Any files and folders in this file will be **ignored when copying file contents**, however, they would **still appear in the generated project tree**.

The `.llmignore` file supports basic glob patterns and negation:

```bash
# Ignore all .log files then re-include a specific file
*.log
!important.log

# Ignore everything directly inside src directory then re-include contents of src/hooks directory
src/*
!src/hooks/
!src/hooks/*
```


### 4. Run the script

Run the script like any other python file, e.g.

```bash
python <path_to_script.py>
```

The output file will be created alongside the script. The contents of this file can now be copied directly into the LLM chat.

The terminal will also show some useful information on running the script:

```bash
✅ Context generated at: C:\path_to_script\output.txt
   ✓ project tree
   ✓ file content: 118 lines of text from 6 files
📊 Prompt is 273 lines | 6,944 characters | ~1,736 tokens
```