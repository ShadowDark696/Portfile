#!/usr/bin/env python3
"""Sanitize commit message: remove emojis/unicode pictographs from stdin and print cleaned message.

Usage from git-filter-branch:
 git filter-branch --msg-filter 'python scripts/sanitize_commit_msg.py' -- <ref>
"""
import sys
import re


def remove_emoji(text: str) -> str:
 # remove many unicode emoji/pictograph ranges
 emoji_pattern = re.compile(
 "["
 "\U0001F600-\U0001F64F" # emoticons
 "\U0001F300-\U0001F5FF" # symbols & pictographs
 "\U0001F680-\U0001F6FF" # transport & map symbols
 "\U0001F1E0-\U0001F1FF" # flags (iOS)
 "\U00002700-\U000027BF"
 "\U000024C2-\U0001F251"
 "\U0001F900-\U0001F9FF"
 "\U0001FA70-\U0001FAFF"
 "]+",
 flags=re.UNICODE,
 )
 return emoji_pattern.sub('', text)


def main() -> None:
 # Read raw bytes and decode as UTF-8 to avoid mojibake on Windows
 data_bytes = sys.stdin.buffer.read()
 try:
 data = data_bytes.decode('utf-8')
 except Exception:
 data = data_bytes.decode('utf-8', errors='ignore')
 cleaned = remove_emoji(data)
 # Trim excessive whitespace left after removals
 cleaned = re.sub(r"[ \t]+", " ", cleaned)
 cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
 sys.stdout.write(cleaned)


if __name__ == '__main__':
 main()
