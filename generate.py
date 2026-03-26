import os  # for walk
import fnmatch
from pathlib import Path


# ==================== CONFIGURATION ====================
OUTPUT_FILE = "output.txt"
INCLUDE_PROJECT_TREE = True

PROMPT_BEFORE = """
I am bulding a react dashboard. Here is my codebase.
"""
PROMPT_AFTER = """
Await further instructions
"""

RESTRICT_EXTENSIONS = {".py", ".js", ".ts", ".tsx", ".html", ".css"}

ALWAYS_IGNORE_FOLDERS = {
    ".git",
    "__pycache__",
    ".vscode",
    "node_modules",
    "llm",
    ".venv",
    "dist",
    "build",
}

ROOT_MARKERS = {".git", ".llmroot"}


# ==================== HELPER FUNCTIONS ====================
def get_project_root(start_path=None):
    current = Path(start_path or __file__).resolve().parent

    while True:
        if any((current / m).exists() for m in ROOT_MARKERS):
            return current

        if current.parent == current:
            raise RuntimeError("Project root not found")

        current = current.parent


def get_ignore_patterns(root: Path, ignore_files):
    patterns = [(p, False) for p in ALWAYS_IGNORE_FOLDERS]
    patterns.append((OUTPUT_FILE, False))

    for item in ignore_files:
        path = Path(item) if Path(item).is_absolute() else root / item

        if not path.exists():
            continue

        try:
            with path.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue

                    is_negation = line.startswith("!")
                    pattern = line[1:] if is_negation else line

                    patterns.append((pattern, is_negation))
        except (OSError, UnicodeDecodeError):
            continue
    return patterns


def matches(pattern, name, rel_path):
    pattern = pattern.rstrip("/")

    return (
        fnmatch.fnmatch(name, pattern)
        or fnmatch.fnmatch(rel_path, pattern)
        or rel_path.startswith(pattern + "/")
    )


def is_ignored(path: Path, root: Path, patterns):
    name = path.name
    rel_path = path.relative_to(root).as_posix()

    # Hard ignores
    if name in ALWAYS_IGNORE_FOLDERS or name == OUTPUT_FILE:
        return True

    ignored = False

    for pattern, is_negation in patterns:
        if matches(pattern, name, rel_path):
            ignored = not is_negation

    return ignored


def print_output(output_path, stats, line_count, char_count, est_tokens):
    # SUCCESS
    print(f"✅ Context generated at: {output_path}")

    # PROJECT TREE
    if INCLUDE_PROJECT_TREE:
        print("   ✓ project tree")

    # FILE STATS
    print(
        "   ✓ file content: "
        f"{stats['lines']:,} lines of text from {stats['files']} files"
    )

    # OUTPUT STATS
    print(
        f"📊 Prompt is {line_count:,} lines | {char_count:,} characters | "
        f"~{est_tokens:,} tokens"
    )

    # LARGE TOKEN WARNING
    if est_tokens > 100000:
        print(
            "⚠️  Warning: This prompt is large (>100k tokens) "
            "and may exceed some model limits."
        )


# ==================== MAIN ====================
def main():
    # ----- SETUP -----
    project_root = get_project_root()
    base_dir = Path(__file__).resolve().parent
    output_path = base_dir / OUTPUT_FILE

    skipped_actual = set()
    stats = {"files": 0, "lines": 0}

    tree_ignore_patterns = get_ignore_patterns(project_root, [".gitignore"])

    ignore_sources = [
        project_root / ".gitignore",
        base_dir / ".llmignore",
    ]
    content_ignore_patterns = get_ignore_patterns(project_root, ignore_sources)

    # ----- OPEN FILE TO WRITE -----
    with output_path.open("w", encoding="utf-8") as out:

        if PROMPT_BEFORE.strip():
            out.write(PROMPT_BEFORE.strip() + "\n\n")

        # ----- PROJECT TREE -----
        if INCLUDE_PROJECT_TREE:
            out.write("=" * 40 + "\n\nPROJECT STRUCTURE:\n")

            # Building the Tree (Excluding ignored folders)
            for root, dirs, files in os.walk(project_root):
                root_path = Path(root)

                # Track skipped dirs
                for d in list(dirs):
                    dir_path = root_path / d
                    if is_ignored(dir_path, project_root, tree_ignore_patterns):
                        skipped_actual.add(
                            dir_path.relative_to(project_root).as_posix()
                        )

                # Prune directories
                dirs[:] = [
                    d
                    for d in dirs
                    if not is_ignored(root_path / d, project_root, tree_ignore_patterns)
                ]

                level = len(root_path.relative_to(project_root).parts)
                indent = "  " * level
                out.write(f"{indent}{root_path.name}/\n")

                for f in files:
                    file_path = root_path / f
                    if not is_ignored(file_path, project_root, tree_ignore_patterns):
                        out.write(f"{indent}  ├── {f}\n")

            if skipped_actual:
                out.write(
                    "\nNOTE: The following folders were omitted: "
                    f"{', '.join(sorted(skipped_actual))}\n"
                )

        # ----- FILE CONTENTS -----
        out.write("\n\nFILE CONTENTS:\n")

        # Adding Contents
        for root, dirs, files in os.walk(project_root):
            root_path = Path(root)

            dirs[:] = [
                d
                for d in dirs
                if not is_ignored(root_path / d, project_root, content_ignore_patterns)
            ]

            for f in files:
                path = root_path / f

                if is_ignored(path, project_root, content_ignore_patterns):
                    continue

                if RESTRICT_EXTENSIONS and path.suffix not in RESTRICT_EXTENSIONS:
                    continue

                try:
                    content = path.read_text(encoding="utf-8")
                    lines = content.splitlines()

                    stats["files"] += 1
                    stats["lines"] += len(lines)

                    out.write(
                        f"--- FILE: {path.relative_to(project_root).as_posix()} ---\n"
                    )
                    out.write(content + "\n\n")

                except (UnicodeDecodeError, PermissionError, OSError):
                    continue

        if PROMPT_AFTER.strip():
            out.write("\n" + PROMPT_AFTER.strip() + "\n")

    # ----- STATS -----
    if output_path.exists():
        full_content = output_path.read_text(encoding="utf-8")
        char_count = len(full_content)
        line_count = len(full_content.splitlines())
        est_tokens = char_count // 4  # Rough heuristic: 1 token ≈ 4 characters

        print_output(
            output_path,
            stats,
            line_count,
            char_count,
            est_tokens,
        )


if __name__ == "__main__":
    main()
