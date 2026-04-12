#!/usr/bin/env python3
"""Sanitize files in the repo by removing emoji/pictograph characters.

This script walks the workspace root, excluding common dependency dirs
and `.git`, and removes emoji characters from text files with certain
extensions. It prints a list of changed files.

DO NOT run this on binary files.
"""
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

EXCLUDE_DIRS = {'.git', '.venv', 'node_modules', 'dist', 'build'}
TEXT_EXTS = {
 '.html', '.htm', '.md', '.py', '.js', '.css', '.json', '.yml', '.yaml',
 '.txt', '.ps1', '.bat', '.sh', '.xml', '.toml', '.cfg', '.ini', '.jsx',
 '.tsx', '.ts', '.php', '.java', '.c', '.cpp', '.h', '.cs', '.rb', '.go',
 '.rs', '.swift'
}

EMOJI_RE = re.compile(
 "["
 "\U0001F600-\U0001F64F" # emoticons
 "\U0001F300-\U0001F5FF" # symbols & pictographs
 "\U0001F680-\U0001F6FF" # transport & map symbols
 "\U0001F1E0-\U0001F1FF" # flags
 "\U00002700-\U000027BF"
 "\U000024C2-\U0001F251"
 "\U0001F900-\U0001F9FF"
 "\U0001FA70-\U0001FAFF"
 "]+",
 flags=re.UNICODE,
)


def is_text_file(path: Path) -> bool:
 return path.suffix.lower() in TEXT_EXTS


def sanitize_text(text: str) -> str:
 new = EMOJI_RE.sub('', text)
 # collapse multiple spaces and tidy newlines
 new = re.sub(r'[ \t]+', ' ', new)
 new = re.sub(r'\n{3,}', '\n\n', new)
 return new


def main() -> int:
 changed = []
 for dirpath, dirnames, filenames in os.walk(ROOT):
 # skip excluded dirs
 parts = Path(dirpath).parts
 if any(p in EXCLUDE_DIRS for p in parts):
 continue

 for fname in filenames:
 path = Path(dirpath) / fname
 if not is_text_file(path):
 continue
 try:
 raw = path.read_bytes()
 try:
 text = raw.decode('utf-8')
 except Exception:
 text = raw.decode('utf-8', errors='ignore')
 new_text = sanitize_text(text)
 if new_text != text:
 path.write_text(new_text, encoding='utf-8')
 changed.append(str(path.relative_to(ROOT)))
 except Exception as e:
 print(f"Skipping {path}: {e}")

 if changed:
 print("Changed files:")
 for p in changed:
 print(p)
 else:
 print("No files changed.")

 return 0


if __name__ == '__main__':
 raise SystemExit(main())
