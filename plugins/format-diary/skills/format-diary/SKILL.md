---
name: format-diary
description: >-
  Turn an Obsidian daily note of raw saved links into a formatted diary entry.
  For each link it writes a speaking title, the real URL (resolving
  share.google redirects), a brief summary (a transcript summary for YouTube),
  fitting hashtags, and a collapsed Obsidian callout holding the full page text
  or transcript. Use this whenever the user wants to format, clean up, expand,
  or "make a diary out of" their daily notes / saved links — e.g. "format my
  diary for today", "process 2026-06-04.md", "turn these links into a diary
  entry", or points you at a dated note file (YYYY-MM-DD.md) full of URLs. Also
  triggers on Obsidian daily-note tidying, link-summarizing, and
  share.google link resolution even when "skill" or "diary" is not said.
---

# Format Diary

Convert a raw Obsidian daily note — usually just a list of links the user saved
during the day — into a readable diary entry, **rewriting the file in place**.

## What a finished entry looks like

```markdown
# Diary for 04. June 2026

## How Anthropic enables self-service data analytics with Claude

- **Source:** [claude.com](https://claude.com/blog/how-anthropic-enables-self-service-data-analytics)
- **Type:** 📄 Article
- **Published:** 2026-06-02
- **Tags:** #ai #anthropic #data-analytics #self-service

**Summary** — Anthropic's data team replaced a backlog of ad-hoc SQL requests with a
Claude-powered analytics assistant that lets non-technical staff ask questions in plain
English. Skills took eval accuracy from 21% to consistently above 95%.

> [!quote]- Page content
> How Anthropic enables self-service data analytics with Claude
> ...full cleaned article text, every line prefixed...

## How To Build A Company With AI From The Ground Up

- **Source:** [Y Combinator](https://www.youtube.com/watch?v=EN7frwQIbKc)
- **Type:** ▶️ Video
- **Published:** 2026-05-28
- **Tags:** #ai #startups #ycombinator #company-building

**Summary** — A YC partner argues AI doesn't just speed up building software — it changes
how startups are structured, from which roles exist to how small teams can stay. She
covers org design, where humans stay in the loop, and pitfalls of over-automating early.

> [!quote]- Full transcript
> Hi, I'm Diana and I'm a partner at YC. Over the past few months...
> ...full transcript, every line prefixed...
```

### Per-entry structure

Each link section is a `## Speaking Title` followed by a **labeled field list**, then
the summary, then the collapsed callout. This makes entries scannable and consistent:

1. `## Speaking Title`
2. A bullet list of labeled metadata fields, in this order, **omitting any field whose
   value you couldn't find** (don't print "unknown" or empty fields):
   - `- **Source:** [display name](real URL)` — the real URL is the link target. Use the
     site/domain for articles (e.g. `claude.com`) and the channel name for videos (e.g.
     `Y Combinator`). This is where the URL lives — no separate bare-URL line.
   - `- **Type:** 📄 Article` or `- **Type:** ▶️ Video`
   - `- **Published:** YYYY-MM-DD` — the article's publish date or the video's upload date,
     only when the page/metadata exposes it.
   - `- **Tags:** #tag #tag …` — 3–6 topical tags (see step 5).
3. `**Summary** — ` followed by 2–4 sentences (see step 5).
4. The collapsed callout (see step 6).

Sections are separated by a blank line. Keep links in their original order. If an entry
is plain journal prose rather than a link, keep it verbatim under the heading.

## Workflow

### 1. Derive the date for the heading

The filename is the date: `2026-06-04.md` → `# Diary for 04. June 2026`.
Format is `DD. MonthName YYYY` — zero-padded day, full English month name, year.
If the user gives you content but no filename, ask for the date or infer it.

### 2. Read the note and pick out each entry

Read the file and identify each saved link in order. The notes are messy: a line
may be `Speaking title https://share.google/xxx`, or the title and URL may sit on
separate lines (e.g. `Source: Harvard Business Review` then the URL beneath it),
or it may be a bare URL with no title. Use judgment to pair each URL with whatever
title text the user left near it. Blank lines are just separators.

If an entry is plain prose rather than a link (a journal sentence), keep it
verbatim under the heading — don't invent a section for it.

### 3. Resolve and classify each URL

- **`share.google/...` links** are redirects the user does NOT want kept. Resolve
  each to its real target before doing anything else:
  ```bash
  python scripts/resolve_share_url.py "https://share.google/63KCWNHaYSbAF4hgJ"
  ```
  Use the resolved URL everywhere in the output. Never keep a `share.google` link.
- A URL that already points somewhere real (e.g. a `youtube.com`/`youtu.be` link)
  is used as-is.
- Classify the resolved URL as **YouTube** (youtube.com / youtu.be) or **article**
  (everything else).

### 4. Get the content

**YouTube** — fetch transcript + metadata (uses yt-dlp via `uvx`, no install needed):
```bash
python scripts/youtube_transcript.py "https://www.youtube.com/watch?v=EN7frwQIbKc"
```
Returns JSON with `title`, `uploader`, `transcript`, `description`. The collapsed
section holds the **full transcript**; the summary summarizes it. If `transcript`
is empty, summarize from `title` + `description` and say the transcript wasn't
available (skip the callout or note it's unavailable).

**Article** — use the `WebFetch` tool on the resolved URL to get the cleaned main
text (the readable article body, not nav/ads/cookie banners). The collapsed
section holds that cleaned text; the summary summarizes it.

If a fetch fails (paywall, network, removed page), don't abort the whole file:
write the best title you can from the link text, a one-line summary noting it
couldn't be fetched, sensible hashtags, and omit the callout for that entry.

### 5. Write the human parts

- **Speaking title** — a clean, readable title. Start from the page/video title and
  trim site cruft like `| Claude`, `- 24/7 Wall St.`, `| Microsoft Learn`. It
  should read like something a person would name the link, not a raw `<title>`.
- **Source** — for articles, the site/domain as display text (`claude.com`,
  `Harvard Business Review`); for videos, the channel/uploader name. The real URL is
  the link target.
- **Published date** — pull the publish date from the article (often near the byline or
  in the page metadata) or the video's upload date (the `published` field from
  `youtube_transcript.py`). Format `YYYY-MM-DD`. If you can't find it, omit the field
  rather than guessing.
- **Summary** — 2–4 sentences capturing what the piece actually says and why it might
  have been worth saving, written after the `**Summary** — ` prefix. For videos,
  summarize the transcript's content, not just its title.
- **Tags** — 3–6 topical tags that fit the entry, lowercase, multi-word tags hyphenated
  (`#ai-agents`, `#machine-learning`), placed on the `- **Tags:**` line. Prefer
  specific, reusable tags over generic ones; they're for finding related entries later
  in Obsidian.

### 6. Build the collapsed callout

Wrap the full transcript / cleaned page text in a collapsed Obsidian foldable
callout. Every body line must be prefixed with `>` (blank lines become a bare
`>`), and the trailing `-` in `[!quote]-` is what makes it collapsed by default.
Do this with the helper rather than by hand so long content stays correctly
prefixed:
```bash
python scripts/format_callout.py --title "Full transcript" --file transcript.txt
# or pipe content in:
echo "$content" | python scripts/format_callout.py --title "Page content"
```
Use the title **"Full transcript"** for videos and **"Page content"** for articles.

### 7. Assemble and overwrite

Concatenate the heading and all sections in original order, then write the result
back to the same file, replacing the raw note. Show the user what you produced.

## Notes

- Process links in parallel where you can (resolve + fetch are independent per
  link) to keep it fast, but keep the final order matching the source note.
- The scripts use only standard tooling: `resolve_share_url.py` and
  `format_callout.py` are pure stdlib; `youtube_transcript.py` runs yt-dlp,
  preferring a `yt-dlp` on PATH and falling back to `uvx yt-dlp`.
- Paths above are relative to this skill directory; run them from here or use
  absolute paths.
