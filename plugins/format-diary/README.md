# format-diary

A Claude Code skill that turns an Obsidian daily note — usually just a list of links
you saved during the day — into a readable diary entry, **rewriting the file in place**.

## What it does

For a note named by date (e.g. `2026-06-04.md`) it produces:

- A heading: `# Diary for 04. June 2026`
- One section per saved link, in original order, each with:
  - a **speaking title** (cleaned of site cruft),
  - a labeled field list — **Source** (linked real URL), **Type** (📄 article / ▶️ video),
    **Published** date when available, and **Tags**,
  - a **summary** (for YouTube, a summary of the transcript),
  - a collapsed Obsidian foldable callout (`> [!quote]- …`) holding the full cleaned
    article text or the full transcript.

`share.google` redirect links are resolved to their real targets and never kept.

## Example

```markdown
## How To Build A Company With AI From The Ground Up

- **Source:** [Y Combinator](https://www.youtube.com/watch?v=EN7frwQIbKc)
- **Type:** ▶️ Video
- **Published:** 2026-04-24
- **Tags:** #ai #startups #ycombinator #company-building

**Summary** — A YC partner argues AI doesn't just speed up building software — it
changes how startups are structured…

> [!quote]- Full transcript
> Hi, I'm Diana and I'm a partner at YC…
```

## Usage

Once installed (`/plugin install format-diary@cantrip`), just ask:

- "Format my Obsidian diary note `2026-06-04.md`."
- "Turn `2026-06-03.md` into a diary entry."

## Bundled scripts

| Script | Purpose | Dependencies |
|--------|---------|--------------|
| `scripts/resolve_share_url.py` | Resolve a `share.google/…` link to its real URL | stdlib only |
| `scripts/youtube_transcript.py` | Fetch a video's metadata + transcript | yt-dlp (run via `uvx`, no install needed) |
| `scripts/format_callout.py` | Wrap long text in a collapsed Obsidian callout with correct `>` prefixing | stdlib only |

Article bodies are fetched with Claude Code's `WebFetch` tool. Pages that block
crawlers (403/429) or sit behind paywalls degrade gracefully — the entry is still
written with a best-effort summary and the callout omitted.

## License

[MIT](../../LICENSE)
