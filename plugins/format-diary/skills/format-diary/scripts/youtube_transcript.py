#!/usr/bin/env python3
"""Fetch a YouTube video's metadata and transcript using yt-dlp.

Usage:
    python youtube_transcript.py "https://youtube.com/watch?v=EN7frwQIbKc"

Prints a JSON object to stdout:
    {
      "id": "EN7frwQIbKc",
      "title": "...",
      "uploader": "...",
      "duration": 612,
      "url": "https://www.youtube.com/watch?v=EN7frwQIbKc",
      "transcript": "Plain-text transcript, paragraphs separated by blank lines.",
      "transcript_source": "subs" | "auto" | null
    }

If no transcript is available, "transcript" is "" and "transcript_source" is null;
metadata is still returned so a summary can be written from title/description.

yt-dlp is located automatically: a `yt-dlp` on PATH is preferred, otherwise the
script falls back to `uvx yt-dlp` and then `python -m yt_dlp`, so it works even
when yt-dlp is not permanently installed.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile


def _yt_dlp_runner() -> list[str] | None:
    """Return the command prefix that invokes yt-dlp, or None if unavailable."""
    if shutil.which("yt-dlp"):
        return ["yt-dlp"]
    if shutil.which("uvx"):
        return ["uvx", "yt-dlp"]
    # python -m yt_dlp, only if importable
    try:
        subprocess.run(
            [sys.executable, "-m", "yt_dlp", "--version"],
            check=True,
            capture_output=True,
            timeout=60,
        )
        return [sys.executable, "-m", "yt_dlp"]
    except Exception:
        return None


_VTT_TS_RE = re.compile(r"^\d{2}:\d{2}:\d{2}\.\d{3}\s+-->\s")
_VTT_TAG_RE = re.compile(r"<[^>]+>")  # inline <00:00:01.234> word timing tags


def _vtt_to_text(vtt: str) -> str:
    """Convert WebVTT subtitle text to deduplicated plain text.

    Auto-generated captions repeat lines as they scroll; we drop consecutive
    duplicate lines so the result reads like prose rather than a karaoke roll.
    """
    lines: list[str] = []
    for raw in vtt.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line == "WEBVTT" or line.startswith(("Kind:", "Language:", "NOTE")):
            continue
        if _VTT_TS_RE.match(line) or "-->" in line:
            continue
        if line.isdigit():  # cue number
            continue
        line = _VTT_TAG_RE.sub("", line)
        line = line.replace("&nbsp;", " ").strip()
        if not line:
            continue
        if lines and lines[-1] == line:
            continue
        lines.append(line)

    # Collapse into ~sentence-ish paragraphs every few lines for readability.
    text = " ".join(lines)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def fetch(url: str, timeout: float = 300.0) -> dict:
    runner = _yt_dlp_runner()
    if runner is None:
        raise RuntimeError(
            "yt-dlp not found. Install it (`pip install yt-dlp`) or make `uvx` "
            "available so `uvx yt-dlp` can run."
        )

    with tempfile.TemporaryDirectory() as tmp:
        out_tmpl = os.path.join(tmp, "%(id)s.%(ext)s")
        cmd = runner + [
            "--skip-download",
            "--write-info-json",
            "--write-subs",
            "--write-auto-subs",
            "--sub-langs",
            "en.*,en,en-orig",
            "--sub-format",
            "vtt/best",
            "-o",
            out_tmpl,
            url,
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if proc.returncode != 0 and not os.listdir(tmp):
            raise RuntimeError(
                f"yt-dlp failed (exit {proc.returncode}): {proc.stderr.strip()[:500]}"
            )

        info: dict = {}
        info_files = [f for f in os.listdir(tmp) if f.endswith(".info.json")]
        if info_files:
            with open(os.path.join(tmp, info_files[0]), encoding="utf-8") as fh:
                info = json.load(fh)

        # Prefer human subs over auto-generated ones.
        vtts = [f for f in os.listdir(tmp) if f.endswith(".vtt")]
        manual = [f for f in vtts if "auto" not in f.lower()]
        auto = [f for f in vtts if "auto" in f.lower()]
        chosen, source = None, None
        if manual:
            chosen, source = manual[0], "subs"
        elif auto:
            chosen, source = auto[0], "auto"
        elif vtts:
            chosen, source = vtts[0], "subs"

        transcript = ""
        if chosen:
            with open(os.path.join(tmp, chosen), encoding="utf-8", errors="replace") as fh:
                transcript = _vtt_to_text(fh.read())
            if not transcript:
                source = None

    upload_date = info.get("upload_date")  # yt-dlp gives YYYYMMDD
    published = None
    if upload_date and len(str(upload_date)) == 8:
        s = str(upload_date)
        published = f"{s[0:4]}-{s[4:6]}-{s[6:8]}"

    return {
        "id": info.get("id"),
        "title": info.get("title"),
        "uploader": info.get("uploader") or info.get("channel"),
        "published": published,
        "duration": info.get("duration"),
        "url": info.get("webpage_url") or url,
        "description": (info.get("description") or "")[:2000],
        "transcript": transcript,
        "transcript_source": source if transcript else None,
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Fetch YouTube transcript + metadata via yt-dlp.")
    parser.add_argument("url", help="the YouTube video URL")
    parser.add_argument(
        "-t", "--timeout", type=float, default=300.0, metavar="SECONDS",
        help="overall timeout in seconds (default: 300)",
    )
    args = parser.parse_args(argv[1:])
    try:
        data = fetch(args.url, timeout=args.timeout)
    except Exception as exc:  # noqa: BLE001 - surface failure to caller
        print(f"error: {exc}", file=sys.stderr)
        return 1
    json.dump(data, sys.stdout, ensure_ascii=False, indent=2)
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
