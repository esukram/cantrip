# council

A Claude Code skill that convenes a **"council"** for an independent second opinion
before you act on something — a plan, an architectural or technical decision, a code
review or audit you've produced, or a choice between two approaches.

The premise is **independence**. The Claude that just produced a review or plan is
invested in it and tends to defend it. So the council gathers two genuinely outside
voices and reconciles them against the real code:

1. **Codex** (`mcp__codex__codex`, an external model) — reads the repo fresh in a
   read-only sandbox.
2. **A cold-read Claude critic** — a subagent that never saw your conversation and
   forms its own opinion from the artifact and the code alone.

It then triages every point against the actual code into **consensus / conflict /
single-source / dismissed** (false positives refuted with a code reference) and reports
a reconciled verdict. It **recommends — it does not auto-apply changes**.

## Prerequisites

This skill drives the [Codex CLI](https://github.com/openai/codex) over MCP. You need:

- The `codex` CLI installed and on your `PATH` (`codex --version`), authenticated.
- The bundled [`.mcp.json`](.mcp.json) registers `codex mcp-server` automatically when
  the plugin is installed — approve it when Claude Code prompts.

If codex is unreachable or hits a usage limit, the skill says so and degrades to a
single-voice (critic-only) review rather than fabricating a second opinion.

## Usage

Once installed (`/plugin install council@cantrip`), just ask — for example:

- "Get a second opinion on this migration plan before I commit to it."
- "Cross-check these security-audit findings against the real code — flag false positives."
- "Is this plan sound? Am I missing anything?"
- "Have the council pressure-test my reasoning on switching to Postgres."

It also offers itself proactively right after you finish a significant review, audit,
or implementation plan — the moment work is about to be acted on.

It is **not** a first-pass code reviewer, bug hunter, or research tool — it vets work
that already exists or a decision about to be made.

## How it works

| Step | What happens |
|------|--------------|
| 0 | Confirm codex is reachable; note the repo root. |
| 1 | Frame one self-contained briefing (works standalone — neither reviewer sees the chat). |
| 2 | Convene both voices in parallel: codex (read-only) **and** an independent critic subagent. |
| 3 | Triage every point against the actual code; verify each kept claim at `file:line`. |
| 4 | Report a reconciled verdict (consensus / conflict / single-source / dismissed), then stop. |

See [`skills/council/references/codex-prompt-template.md`](skills/council/references/codex-prompt-template.md)
for the briefing structure.

## License

[MIT](../../LICENSE)
