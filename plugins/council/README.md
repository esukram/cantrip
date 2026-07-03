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
a reconciled verdict — in `council:council`, disagreements that survive the loop are
first expanded into an option map. It **recommends — it does not auto-apply changes**.

## Two modes

The plugin ships two skills — pick by stakes:

- **`council:council`** (the thorough default) — runs a **multi-pass loop**: after
  reconciling once, it hands its *own draft verdict* back to the voices to attack and
  loops until a pass surfaces nothing new (always ≥2 passes, capped at `MAX_PASSES`).
  When the stopped loop (converged or capped) leaves a conflict that only the human
  can settle — intent, risk, scope, priority — it first **expands** those surviving
  disagreements into an option map (the hidden assumption behind the split plus 2–4
  alternatives with tradeoffs, capped at `MAX_DEEP_DIVES`), then pulls you in to
  **arbitrate** one question at a time, with the explored options on the ballot
  (interactive contexts only; in headless/auto runs it lists them under "Human
  decision needed" instead, maps included). The human's call is binding and recorded.
- **`council:fast`** — a quick, fully autonomous **single pass**: gather both voices,
  reconcile once, report conflicts as prose for you to settle. No loop, no questions.
  Reach for it on a small or low-stakes decision, a fast gut-check, or any
  headless/unattended run.

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
| 2 | Pass 1 — convene both voices in parallel: codex (read-only) **and** an independent critic subagent. |
| 3 | Triage every point against the actual code into a **draft verdict**; verify each kept claim at `file:line`. |
| 4 | **Multi-pass loop** (`council:council`) — hand the draft back to the voices to attack; re-reconcile until it converges (≥2 passes, capped at `MAX_PASSES`). `council:fast` stops after the single pass. |
| 5 | **Divergence expansion** (`council:council` only) — surviving human-bound conflicts get expanded into an option map: the hidden assumption driving the split plus 2–4 alternatives with tradeoffs (capped at `MAX_DEEP_DIVES`). |
| 6 | **Arbitrate** (`council:council`, interactive only) — put any surviving judgment-owned conflict to the human, one question at a time, with the explored options on the ballot; the call is binding and recorded. |
| 7 | Report a reconciled verdict (consensus / conflict / single-source / dismissed, plus Human-arbitrated / Human decision needed, with the full option maps), then stop. |

See [`skills/council/references/codex-prompt-template.md`](skills/council/references/codex-prompt-template.md)
for the briefing structure.

## License

[MIT](../../LICENSE)
