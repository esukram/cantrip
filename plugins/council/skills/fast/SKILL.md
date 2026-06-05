---
name: fast
description: Use this skill for a quick, single-pass independent second opinion before acting on something — a plan, a technical or architectural decision, a code review or audit you've produced, or a choice between approaches — when you want the outside check fast and autonomous, with no back-and-forth. It convenes a "council" in one pass: sends the artifact to codex (an external model, read-only) plus a separate independent Claude critique, reconciles both against the actual code, and reports conflicts as prose for you to settle. This is the quick escape hatch; for the thorough multi-pass review with interactive human arbitration of judgment calls, use `council:council` instead. Reach for `council:fast` on a small or low-stakes decision, a fast gut-check, or any headless/unattended run where a single autonomous pass is all you want.
---

# Council (fast): a quick independent second opinion

This is the **single-pass, fully autonomous** version of the council. It gathers
two genuinely outside voices, reconciles them against the real code in one pass,
and reports — no iterative loop, no interactive questions. When you want the
thorough multi-pass review that re-attacks its own draft and pulls you in to
arbitrate judgment-owned conflicts, reach for **`council:council`** instead.

The value of a council is **independence**. The Claude that just produced a
review or plan is invested in it and will tend to defend it. So this skill
gathers two genuinely outside voices, then reconciles them against the real
code instead of trusting either one:

1. **Codex** (`mcp__codex__codex`, GPT-5.5) — a different model, reading the
   repo fresh in a read-only sandbox.
2. **A cold-read Claude critic** — a subagent that never saw this conversation
   and forms its own opinion from the artifact and the code alone.

Where two independent reviewers using different reasoning both flag the same
thing, that's a strong signal. Where they disagree, that's where you most need
to look. Your job as orchestrator is not to relay their output — it's to weigh
it against the actual code and tell the user what's worth acting on.

## When to convene

Trigger explicitly when asked for a *quick* second opinion, sanity-check,
cross-check, or outside review of code/a review/an audit/a plan/a decision —
especially on a small or low-stakes call, or in a headless/unattended run where
a single autonomous pass is what's wanted. For a high-stakes or contested
artifact where it's worth iterating and arbitrating with the human, prefer
**`council:council`**.

Offer proactively (don't just launch it — **ask first**, it costs tokens and a
minute or two) right after you finish something consequential that's about to
be acted on: a code review, a security audit, an architecture proposal, a
migration plan. A good nudge: *"Want me to run this past the council
(codex + an independent critic) before you act on it?"*

## Step 0 — Check the council is reachable

Confirm `mcp__codex__codex` is in your available tools. If it isn't, say so
plainly — and offer to proceed with just the cold-read Claude critic as a
degraded single-voice review.

A second, sneakier failure mode: codex is *present as a tool* but **errors at
call time** — a usage/quota limit ("you've hit your usage limit"), an auth
failure, or a sandbox error. Treat that exactly like an absent voice: don't
retry blindly, don't fabricate what codex "would have said." Fall back to the
critic-only review and tell the user *why* the second voice dropped out (quota
vs. config) so they know whether it's worth retrying later. A council that
quietly shrinks to one voice while still claiming two is the one outcome to
avoid — the whole point is honest independence.

Note the **repo root** you're reviewing in (absolute path). Codex needs it as
`cwd`, and the critic needs it to find files.

## Step 1 — Frame the artifact once

Write a single, self-contained briefing you can hand to both reviewers. It must
stand alone — neither reviewer can see your conversation. Include:

- **What the artifact is** (a PR, a review you produced, a plan, a decision)
  and where it lives (PR number + repo URL, file paths, commit).
- **The artifact itself** — paste the review/plan/decision text, or point to
  the exact files and diff for code.
- **What you want checked** — verify claims against the actual code; flag
  anything wrong, overstated, missed, or where a failure scenario is
  implausible; call out better alternatives.

See `references/codex-prompt-template.md` for the structure that has worked
well (role framing → Context → the artifact → specific asks). Reuse it for both
reviewers so their inputs are identical and their disagreements are real.

## Step 2 — Convene both voices in parallel

These are independent and slow-ish, so launch them in the **same turn**.

**Codex** — call `mcp__codex__codex`:

```
mcp__codex__codex({
  prompt: "<the briefing from Step 1>",
  model: "gpt-5.5",
  sandbox: "read-only",
  "approval-policy": "never",
  cwd: "<repo root>"
})
```

`sandbox: "read-only"` + `approval-policy: "never"` let codex read the repo and
run read-only commands autonomously without ever editing or prompting.

**Cold-read Claude critic** — spawn a subagent (e.g. `Explore` or
`general-purpose`) with the *same* briefing. Tell it explicitly: you did not
write this, read the relevant code yourself, form your own view, and return
your findings as a list with file:line evidence and a confidence level per
point. The independence only holds if it actually opens the code rather than
trusting the briefing.

The critic must be a *separate* subagent, not you re-reading your own work — a
fresh agent has no stake in the briefing and will disagree where you'd
rationalize. If you genuinely can't spawn one (e.g. you're already running
inside a subagent with no Agent tool), don't silently substitute your own
second pass and call it a second voice — note the limitation, the same way you
would for codex. Two real voices or an honest count of how many you got.

## Step 3 — Triage and reconcile (the real work)

Don't paste both reports and call it done. Go through every point each reviewer
raised and judge it **against the actual code**, then bucket it:

- **Consensus** — both flagged it (or one flagged, the other implicitly agrees)
  and you've confirmed it's real. Highest priority.
- **Conflict** — they disagree, or one flags something the other explicitly
  dismisses. Investigate and say who's right and why.
- **Codex-only / Critic-only** — a real point only one caught. Often the most
  valuable part; different reasoning catches different things.
- **Dismissed** — raised but wrong, overstated, or based on a misread. Say so
  and show the code that refutes it. Reviewers are sometimes confidently wrong;
  protecting the user from a bad "fix" is as useful as surfacing a real one.

For each kept point, verify the claim yourself before promoting it — cite
`file:line`. A second opinion that's wrong is worse than none, so the triage is
where this skill earns its keep.

## Step 4 — Report the verdict

Present a reconciled report, not a transcript. Use this shape:

```
# Council verdict: <artifact>

**Consensus (act on these)**
- <point> — <file:line>, <one-line why it's real>

**Conflicts (your call)**
- <point> — codex says X, critic says Y; my read: <which, why>

**Worth considering (single-source)**
- <point> — <source>, <file:line>

**Dismissed**
- <point> — <why it doesn't hold, with code reference>

**Recommended next actions**
- <ordered, concrete>
```

Conflicts are reported as **prose for the user to settle** — this fast path does
not stop to ask. If a conflict genuinely hinges on user judgment (intent, risk,
scope, priority) and you'd want the human to actually adjudicate it
interactively, that's the signal to reach for **`council:council`**, which turns
those into a structured, auditable arbitration.

Then stop and let the user decide. This skill reconciles and recommends — it
does **not** auto-apply changes. If the user then says "do it", implement the
agreed actions as normal work.

For follow-up questions to codex (e.g. "you flagged X — does it still hold given
Y?"), continue the same session with `mcp__codex__codex-reply` using the session
id from Step 2 rather than starting fresh, so codex keeps its context.
