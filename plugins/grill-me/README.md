# grill-me

A Claude Code skill that **interviews you into a locked plan, then has codex tear
into it** — before a line of code is written.

Two acts:

1. **Grill.** Claude interviews you about what you're about to build — **one question
   at a time**, each with a recommended answer. It's a *pure human interview*: Claude
   asks, you answer — it does **not** go read the codebase to answer its own questions
   (that grounding is Act 2's job). It chases every branch of the decision tree until
   the plan is concrete and shared, then locks it to `PLAN.md` — recording any
   code-level assumptions for codex to verify.
2. **Review.** That plan goes to [codex](https://github.com/openai/codex) — a
   *different* model, reading the repo fresh in a read-only sandbox **over MCP** — for
   round-by-round adversarial critique. Codex attacks; Claude arbitrates each round
   (accepting good critiques, rejecting weak ones with logged reasons), revising
   `PLAN.md` and resuming the **same codex session** so it keeps full context. The
   exchange is logged to `PLAN-REVIEW-LOG.md`.

It ends when codex returns `VERDICT: APPROVED`, a round cap (`MAX_ROUNDS`, default 5)
is hit, or you sign off. **No implementation code is written until you explicitly sign
off on the final plan** — this skill hardens a plan, it doesn't build it.

## Prerequisites

This skill drives the [Codex CLI](https://github.com/openai/codex) over MCP. You need:

- The `codex` CLI installed and on your `PATH` (`codex --version`), authenticated.
- The bundled [`.mcp.json`](.mcp.json) registers `codex mcp-server` automatically when
  the plugin is installed — approve it when Claude Code prompts.

If codex is unreachable or hits a usage limit, the skill says so and treats the run as
**blocked** — it presents the grilled-but-unreviewed plan clearly labeled as not having
had the second-model pass, rather than fabricating codex's review.

## Usage

Once installed (`/plugin install grill-me@cantrip`), run `/grill-me` or just ask — for
example:

- "Grill me on this — I'm about to rewrite the auth flow."
- "Interview me about this migration plan, then get a second model to poke holes in it."
- "Stress-test this design before I build it."
- "Poke holes in my approach to the caching layer."

It can also offer itself when you're about to commit to something high-stakes.

## How it works

| Step | What happens |
|------|--------------|
| Act 1 | Grill you one question at a time (recommended answer each) — a pure human interview, no codebase digging — until the decision tree resolves; lock the plan to `PLAN.md` with any code assumptions flagged for Act 2. |
| Act 2 · round 1 | Start a codex session (`mcp__codex__codex`, read-only) with an adversarial-review briefing; capture the `threadId`. |
| Act 2 · rounds 2..N | Resume the same session (`mcp__codex__codex-reply`) after each revision; codex re-reviews with full context. |
| Each round | Log codex's critique + Claude's arbitration; parse the terminal `VERDICT:` line; revise or converge. |
| Resolution | Present the final plan; **get explicit sign-off before any code is written.** |

See [`skills/grill-me/references/codex-review-prompt.md`](skills/grill-me/references/codex-review-prompt.md)
for the adversarial-review briefing structure.

## License

[MIT](../../LICENSE)
