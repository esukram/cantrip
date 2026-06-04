# cantrip

A personal [Claude Code](https://code.claude.com) plugin **marketplace** — a small
collection of practical, well-tested skills you summon at will.

## Install

Add the marketplace, then install the plugin you want:

```
/plugin marketplace add esukram/cantrip
/plugin install format-diary@cantrip
```

(Equivalent non-interactive CLI: `claude plugin marketplace add esukram/cantrip`
then `claude plugin install format-diary@cantrip`.)

## Plugins

| Plugin | What it does |
|--------|--------------|
| [`format-diary`](plugins/format-diary) | Turns an Obsidian daily note of raw saved links into a formatted diary entry — speaking titles, resolved `share.google` URLs, summaries (YouTube transcript summaries included), hashtags, and collapsed callouts holding the full page text or transcript. |
| [`council`](plugins/council) | Convenes a "council" for an independent second opinion before you act — sends a plan, decision, code review, or audit to codex (an external model, read-only) plus a separate independent Claude critique, reconciles both against the actual code, and reports a verdict (consensus, conflicts, dismissed false positives). Requires the [`codex`](https://github.com/openai/codex) CLI. |
| [`land-pr`](plugins/land-pr) | Lands a GitHub PR end-to-end in an isolated worktree — verifies CI is green and review threads are resolved, runs the test suite, merges, updates the base branch, and cleans up. Aborts at any failing gate and never merges unless every check passes. Requires the [`gh`](https://cli.github.com) CLI. |

## License

[MIT](LICENSE)
