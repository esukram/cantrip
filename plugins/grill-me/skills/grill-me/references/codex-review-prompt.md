# Codex adversarial-review briefing

In Act 2, codex reviews the locked `PLAN.md` as an **adversary** — its job is to find
what's wrong, not to bless the plan. The briefing has to stand on its own: codex
cannot see the grill, the conversation, or what you and the user already settled. It
*can* read the repo (read-only). The structure below produces sharp, code-grounded
critique that the per-round loop can parse.

Use it verbatim-ish for Round 1; on resume (`mcp__codex__codex-reply`) you only send a
short "I revised PLAN.md, re-review" prompt — the session already has this context.

## Round 1 briefing structure

```
You are an adversarial reviewer of an implementation PLAN. The plan is locked in
PLAN.md in your working directory. Your job is to find concrete flaws before any
code is written — not to approve it. Be skeptical; a plausible-sounding plan that
breaks in practice is exactly what you're here to catch.

# Context

<One or two sentences on what's being built and the stack, enough to orient. Point
at PLAN.md on disk — you have read-only repo access, so verify claims against the
actual code rather than taking the plan's word.>

# What I want from you

- Read PLAN.md in full.
- Attack the "Key decisions & tradeoffs" — that's where the contestable choices are.
- Verify the plan's assumptions against the real code: does the util it relies on
  exist? is the integration point shaped the way the plan assumes? will the approach
  actually work here?
- Flag concrete flaws: wrong assumptions, missed edge cases, simpler alternatives,
  steps that won't work, risks the plan under-rates or ignores.
- Where there's a materially better approach, say so concretely.

# How to end

End your response with EXACTLY ONE line, on its own, nothing after it:

VERDICT: APPROVED   — the plan is sound enough to implement
VERDICT: REVISE     — material problems remain (list them above)
```

## What makes this work

- **Point at real code, not summaries.** "verify `PLAN.md`'s claim that `formatDate`
  exists in `src/utils`" beats "check the assumptions." Codex has read-only access —
  invite it to use it.
- **Name the target.** "Attack the Key decisions & tradeoffs section" focuses the
  critique on the choices that actually matter instead of bikeshedding wording.
- **Demand the verdict line, exactly.** The per-round loop parses the terminal
  `VERDICT:` line as a control-flow gate. Make the format non-negotiable so parsing
  is reliable; the loop treats anything ambiguous as `REVISE`.
- **Invite disagreement.** "find concrete flaws… not to approve it" gives codex
  permission to push, which is the entire point. Without it, reviewers agree politely.

## Codex MCP call parameters

| param             | value          | why |
|-------------------|----------------|-----|
| `model`           | `"gpt-5.5"`    | the strong reviewer model (local convention; omit it to fall back to codex's default if pinning 4xxs on a ChatGPT-auth account) |
| `sandbox`         | `"read-only"`  | reads + read-only commands, never edits |
| `approval-policy` | `"never"`      | runs autonomously, never blocks on a prompt |
| `cwd`             | working dir    | absolute path — the same directory `PLAN.md` was written to, so codex finds it |

## Resuming the session

Continue the *same* review with `mcp__codex__codex-reply({ threadId, prompt })` using
the `threadId` captured from the Round-1 response — don't start a fresh session.
`codex-reply` takes only `threadId` + `prompt`; it cannot re-set `sandbox`, so
read-only is inherited from Round 1. Keeping one session means codex remembers its
prior findings and can confirm what your revision actually fixed.
