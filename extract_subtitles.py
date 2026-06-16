#!/usr/bin/env python3
"""
Extract and clean subtitles from a YouTube video URL.
Outputs JSON with deduplicated subtitle entries, each with timestamp and text.

Usage:
    python3 extract_subtitles.py <youtube_url> [--output <path>] [--lang <lang>]

Output JSON format:
    [{"t": "mm:ss", "s": <seconds_float>, "text": "<content>"}, ...]
"""

import sys
import re
import json
import subprocess
import tempfile
import os
import argparse
from collections import defaultdict


def ensure_yt_dlp():
    try:
        import yt_dlp  # noqa
    except ImportError:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "yt-dlp", "-q", "--break-system-packages"],
            stderr=subprocess.DEVNULL
        )


def download_subtitles(url: str, lang: str = "en") -> str | None:
    """Download subtitles via yt-dlp, return path to .srt file or None."""
    with tempfile.TemporaryDirectory() as tmpdir:
        out_tmpl = os.path.join(tmpdir, "sub")
        cmd = [
            sys.executable, "-m", "yt_dlp",
            "--write-auto-subs",
            "--skip-download",
            "--sub-langs", lang,
            "--convert-subs", "srt",
            "-o", out_tmpl,
            "--quiet",
            url,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        # find produced .srt
        for f in os.listdir(tmpdir):
            if f.endswith(".srt"):
                path = os.path.join(tmpdir, f)
                with open(path) as fh:
                    return fh.read()
    return None


def parse_srt(content: str) -> list[dict]:
    """Parse SRT content into list of {s, t, text} dicts, deduplicated."""
    blocks = re.split(r"\n\n+", content.strip())
    entries = []
    for block in blocks:
        lines = block.strip().split("\n")
        ts_line = next((l for l in lines if re.match(r"\d{2}:\d{2}:\d{2}", l)), None)
        if not ts_line:
            continue
        start = ts_line.split("-->")[0].strip()
        h, m, s = start.replace(",", ".").split(":")
        sec = int(h) * 3600 + int(m) * 60 + float(s)
        ts_idx = lines.index(ts_line)
        text_lines = [re.sub(r"<[^>]+>", "", l) for l in lines[ts_idx + 1:] if l.strip()]
        text = " ".join(text_lines).strip()
        if text:
            entries.append((sec, text))

    # Group into ~4s buckets, keep longest text per bucket
    chunks = defaultdict(list)
    for sec, text in entries:
        chunks[int(sec / 4)].append((sec, text))

    result = []
    last_text = ""
    for key in sorted(chunks):
        sec, text = max(chunks[key], key=lambda x: len(x[1]))
        text = re.sub(r"\s+", " ", text).strip()
        text = re.sub(r">>\s*\[.*?\]\s*>>", "", text).strip()
        if len(text) < 5 or text == last_text:
            continue
        # deduplicate by first 50 chars
        total = int(sec)
        ts_fmt = f"{total // 60:02d}:{total % 60:02d}"
        result.append({"t": ts_fmt, "s": round(sec, 1), "text": text})
        last_text = text

    # Final pass: remove near-duplicates
    seen, final = set(), []
    for e in result:
        key = e["text"][:50]
        if key in seen:
            continue
        seen.add(key)
        final.append(e)

    return final


def main():
    parser = argparse.ArgumentParser(description="Extract YouTube subtitles to JSON")
    parser.add_argument("url", help="YouTube video URL")
    parser.add_argument("--output", "-o", help="Output JSON file path (default: stdout)")
    parser.add_argument("--lang", default="en", help="Subtitle language code (default: en)")
    args = parser.parse_args()

    ensure_yt_dlp()

    print(f"[extract_subtitles] Downloading subtitles for: {args.url}", file=sys.stderr)
    srt_content = download_subtitles(args.url, args.lang)
    if not srt_content:
        print("[extract_subtitles] ERROR: No subtitles found. Video may not have auto-generated captions.", file=sys.stderr)
        sys.exit(1)

    entries = parse_srt(srt_content)
    print(f"[extract_subtitles] Extracted {len(entries)} entries (original SRT deduped)", file=sys.stderr)

    output = json.dumps(entries, ensure_ascii=False, indent=2)
    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        print(f"[extract_subtitles] Saved to: {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
