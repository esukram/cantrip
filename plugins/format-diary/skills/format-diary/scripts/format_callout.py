#!/usr/bin/env python3
"""Wrap text in a collapsed Obsidian foldable callout.

Obsidian callouts require EVERY line of the body to be prefixed with `> `,
including blank lines (as a bare `>`). Doing this by hand for a long transcript
or article is error-prone, so this script does it deterministically.

Usage:
    python format_callout.py --title "Full transcript" --file content.txt
    cat content.txt | python format_callout.py --title "Page content"

The trailing `-` after the callout type (e.g. `[!quote]-`) is what makes the
section collapsed by default in Obsidian.
"""
from __future__ import annotations

import argparse
import sys


def wrap(text: str, title: str, kind: str = "quote") -> str:
    header = f"> [!{kind}]- {title}"
    lines = [header]
    body = text.replace("\r\n", "\n").replace("\r", "\n").rstrip("\n")
    if body == "":
        lines.append(">")
        return "\n".join(lines)
    for line in body.split("\n"):
        lines.append(f"> {line}" if line.strip() else ">")
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Wrap text in a collapsed Obsidian callout.")
    parser.add_argument("--title", required=True, help="callout title / summary line")
    parser.add_argument("--kind", default="quote", help="callout type (default: quote)")
    parser.add_argument("--file", help="read body from this file (default: stdin)")
    args = parser.parse_args(argv[1:])

    text = open(args.file, encoding="utf-8").read() if args.file else sys.stdin.read()
    print(wrap(text, args.title, args.kind))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
