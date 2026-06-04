# skill-foundry

A personal [Claude Code](https://code.claude.com) plugin **marketplace** — a small
foundry of practical, well-tested skills.

## Install

Add the marketplace, then install the plugin you want:

```
/plugin marketplace add esukram/skill-foundry
/plugin install format-diary@skill-foundry
```

(Equivalent non-interactive CLI: `claude plugin marketplace add esukram/skill-foundry`
then `claude plugin install format-diary@skill-foundry`.)

## Plugins

| Plugin | What it does |
|--------|--------------|
| [`format-diary`](plugins/format-diary) | Turns an Obsidian daily note of raw saved links into a formatted diary entry — speaking titles, resolved `share.google` URLs, summaries (YouTube transcript summaries included), hashtags, and collapsed callouts holding the full page text or transcript. |
| [`council`](plugins/council) | Convenes a "council" for an independent second opinion before you act — sends a plan, decision, code review, or audit to codex (an external model, read-only) plus a separate independent Claude critique, reconciles both against the actual code, and reports a verdict (consensus, conflicts, dismissed false positives). Requires the [`codex`](https://github.com/openai/codex) CLI. |

## Repository layout

```
skill-foundry/
├── .claude-plugin/
│   └── marketplace.json        # marketplace manifest
└── plugins/
    ├── format-diary/
    │   ├── .claude-plugin/
    │   │   └── plugin.json     # plugin manifest
    │   └── skills/
    │       └── format-diary/
    │           ├── SKILL.md
    │           └── scripts/    # bundled helpers (stdlib + yt-dlp via uvx)
    └── council/
        ├── .claude-plugin/
        │   └── plugin.json     # plugin manifest
        ├── .mcp.json           # registers the codex MCP server
        └── skills/
            └── council/
                ├── SKILL.md
                └── references/ # codex briefing template
```

## License

[MIT](LICENSE)
