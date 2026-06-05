---
name: grill-me
description: Interview the user relentlessly about something they're about to build, then have codex adversarially review the resulting plan. Act 1 — grill: ask the user one sharp question at a time (each with a recommended answer), chasing the decision tree until it's resolved and the plan is locked to PLAN.md. This is a pure human interview — Claude asks, the user answers; no codebase digging yet. Act 2 — review: codex (an external model, read-only, over MCP) reads the repo fresh and adversarially critiques the plan round by round, with Claude arbitrating revisions, until codex approves, a round cap is hit, or the user signs off. The codebase grounding lives here, in Act 2, where codex verifies the plan against the real code. Reach for it when the user is about to commit to something high-stakes and says "grill me", "stress-test this plan", "interview me about this then get a second model on it", "poke holes in this before I build it", or wants a plan hardened by questioning plus an outside model before any code is written. Plans and reviews only — it writes no implementation code until the user signs off.
argument-hint: "[what you're about to build]"
---

# Grill Me: interview to a locked plan, then codex tears into it

Two acts. **Act 1** is a relentless interview that turns a vague intention into a
concrete, locked plan — Claude asks the user questions; it is *not* Claude
answering its own questions from the codebase. That codebase grounding is **Act 2's**
job: Act 2 hands the plan to codex — a *different* model, reading the repo fresh in a
read-only sandbox — for adversarial review across as many rounds as it takes to
converge, with you as the final arbiter. The point is to find the holes *before*
writing code, not after.

This skill **plans and reviews — it does not implement**. No code is written until
the user explicitly signs off on the final plan.

## Tunables

Echo the resolved values before starting Act 2:

| Variable     | Default              | Purpose |
|--------------|----------------------|---------|
| `MAX_ROUNDS` | `5`                  | Hard cap on codex review rounds, counting Round 1. So up to 5 total codex turns, not 5 revisions. |
| `PLAN_FILE`  | `PLAN.md`            | The locked plan. |
| `LOG_FILE`   | `PLAN-REVIEW-LOG.md` | Append-only transcript of every round. |
| `model`      | `gpt-5.5`            | Codex model. See the note in Act 2 — omit it to let codex pick its default if pinning fails. |

## Act 1 — Grill

Interview the user about **$ARGUMENTS** (what they're about to build). If invoked
with no argument, open by asking what they're about to build, then proceed.

Act 1 is a **pure human interview**: Claude asks, the user answers. You are
extracting the user's intent, priorities, tradeoffs, constraints, and scope — the
things only they can settle. **Do not read the codebase to answer your own questions
in Act 1.** Resist the urge to go investigate and self-resolve; if a factual
assumption matters, capture it in the plan as a stated assumption and let codex
verify it against the real code in Act 2. Act 1 is questions *to the human*, not
Claude answering them.

The rules of the grill:

- **One question at a time.** Never batch. Ask via the `AskUserQuestion` tool —
  exactly one question per call — wait for the answer, let it shape the next. A
  grill is a sequence, not a form.
- **Always include a recommended answer.** Make the first option your
  recommendation, label it `(Recommended)`, and put the *why* in its description —
  give the user something to push against, not a blank prompt. The tool's automatic
  **"Other"** option keeps it a real interview: it's there for the branch you
  didn't foresee, so the user can always answer outside your options.
- **Ask the human; don't go digging.** Direct every question at the user. Don't
  open files, grep, or otherwise investigate the repo to pre-empt a question —
  that codebase grounding is Act 2's job (codex reads the repo fresh). Where a fact
  about the code matters to the plan, ask the user or record it as an explicit
  assumption for codex to check; don't spend a round of the grill resolving it
  yourself.
- **Chase every branch.** Each decision opens new ones. Follow the decision tree
  until it's resolved: dependencies clarified, ambiguities settled, the risky
  corners poked. Stress-test rather than affirm — the goal is shared understanding
  you've both pressure-tested, not polite agreement.

### Asking via AskUserQuestion

`AskUserQuestion` is the native surface for this loop: one question, a recommended
answer to push against, and an "Other" escape hatch for free-form replies. One
question per call:

```
AskUserQuestion({
  questions: [{
    header: "Cache",
    question: "Should the cache invalidate on write, or expire on a TTL?",
    multiSelect: false,
    options: [
      { label: "Invalidate on write (Recommended)",
        description: "Strong consistency — every write busts the key. Why: reads must never go stale, and write volume is low enough the extra cost is negligible." },
      { label: "TTL expiry",
        description: "Simpler, but serves stale data up to the TTL window." }
    ]
  }]
})
```

The tool allows up to four questions per call — don't; one at a time is the
mechanic. Where the answer space is genuinely open (e.g. an opening "what are you
building?"), plain prose is fine — lean on the tool for the concrete tradeoff
questions that make up most of the grill.

**Stop when** the decision tree is resolved and you and the user share a concrete
understanding of the plan — no major open branches, dependencies clear.

### Lock the plan

First, **resolve the working directory** and **echo its absolute path**. This is
load-bearing: in Act 2 codex reads `PLAN.md` from disk with this same path as its
`cwd`. Write `PLAN_FILE` and `LOG_FILE` into *this* directory (the user's project /
repo root) so the write path and codex's `cwd` provably match. If `PLAN.md` already
exists, **warn the user before overwriting it**.

Write `PLAN_FILE`:

```
# Plan: <task>
_Locked via grill — by Claude + <user>_

## Goal
<one paragraph reflecting the grilled settlement>

## Approach
<numbered, concrete steps>

## Key decisions & tradeoffs
<the contestable choices — exactly what you want codex to attack>

## Assumptions to verify
<facts about the codebase the grill took on the user's word, not by reading —
list them explicitly so codex can check each against the real code in Act 2>

## Risks / open questions
<genuinely open items>

## Out of scope
<bounds the grill established>
```

Then initialize `LOG_FILE`:

```
# Plan Review Log: <task>
Act 1 (grill) complete — plan locked with the user. MAX_ROUNDS=<n>.
```

## Act 2 — Codex adversarial review (over MCP, session-aware)

Codex is driven **over MCP** (`mcp__codex__codex` / `mcp__codex__codex-reply`), not
as a subprocess. The same codex *session* is reused across rounds so it keeps full
context — codex and Claude genuinely converse, round to round.

### Step 0 — Is codex reachable?

Confirm `mcp__codex__codex` is in your available tools. A sneakier failure: codex is
present as a tool but **errors at call time** — a usage/quota limit, an auth failure,
a sandbox error. Treat that exactly like an absent voice: don't retry blindly, don't
fabricate what codex "would have said."

Because this skill's whole premise is that codex *always* reviews the plan, a
codex-absent run is a **blocked / degraded** run — not a normal completion. Say so
plainly (quota vs. config, so the user knows whether it's worth retrying), and let
the user decide whether to proceed on the un-reviewed plan. Do not quietly present an
un-reviewed plan as if it went through the grill *and* the review.

### Round 1 — start the session

Call `mcp__codex__codex` with the adversarial-reviewer briefing from
`references/codex-review-prompt.md`:

```
mcp__codex__codex({
  prompt: "<the adversarial-review briefing>",
  model: "gpt-5.5",
  sandbox: "read-only",
  "approval-policy": "never",
  cwd: "<the absolute working dir from Act 1>"
})
```

`sandbox: "read-only"` + `approval-policy: "never"` let codex read the repo and run
read-only commands autonomously without ever editing or prompting. The briefing tells
codex to read `PLAN.md`, find concrete flaws, and end with **exactly one line**:
`VERDICT: APPROVED` or `VERDICT: REVISE`.

**Capture the `threadId` from the response.** The codex MCP response has the shape
`{ "threadId": "...", "content": "..." }` — `threadId` is what preserves session
awareness. If no `threadId` comes back, report it and treat Act 2 as failed rather
than silently losing continuity.

**On `model` (read this before pinning):** `gpt-5.5` matches the local convention
(the `council` skill pins it too). But pinning a model can 400 on codex CLIs
authenticated through a ChatGPT account. If the Round-1 call errors with a
model/4xx, **retry once with `model` omitted** to let codex pick its default, and
note the fallback. Don't keep retrying a failing pin.

### Read-only is locked at session start (safety)

`mcp__codex__codex-reply` accepts **only** `threadId` + `prompt` — it *cannot*
re-assert `sandbox` or `approval-policy`. Read-only is therefore set on the Round-1
`mcp__codex__codex` call and inherited by every resume. (This is the MCP analogue of
the upstream subprocess caveat that `codex exec resume` doesn't take `-s`.) Never try
to "re-enable" read-only on a reply — it's already locked; just don't start a fresh
session that drops it.

### Rounds 2..MAX_ROUNDS — resume the same session

After each revision, continue the *same* thread:

```
mcp__codex__codex-reply({
  threadId: "<captured id>",
  prompt: "I revised PLAN.md. Re-review it — re-check your prior findings, confirm what's fixed, flag anything still open or newly introduced. End with exactly one line: VERDICT: APPROVED or VERDICT: REVISE."
})
```

Because it's the same thread, codex keeps full context — no re-sending the plan.

### Per-round loop

For each codex turn:

1. **Log it.** Append a `## Round <n> — Codex` section to `LOG_FILE` with codex's
   full critique.
2. **Parse the verdict.** Read the terminal `VERDICT:` line. This is a control-flow
   gate over free-text output, so harden it: if there is **no** unambiguous
   `VERDICT: APPROVED` / `VERDICT: REVISE` line — it's missing, buried, or hedged —
   treat it as **REVISE** (or reply once asking codex for just the verdict line).
   Never read approval into ambiguous output.
3. **Act on the verdict:**
   - **`APPROVED`** → converged. Go to Resolution.
   - **`REVISE`** → **you are the arbiter.** Decide what's actionable: accept good
     critiques, reject weak ones *with logged justification*. Append a
     `### Claude's response` block under the round explaining what you changed, what
     you rejected, and why. Then:
     - For **factual / technical** fixes, revise `PLAN.md` directly.
     - Where a critique would change a **product-intent or scope decision the user
       settled in Act 1**, **ask the user** before mutating the locked plan — don't
       let codex silently override the grill.
     Increment the round and resume the thread (Rounds 2..MAX).
4. **Cap.** If the round count would exceed `MAX_ROUNDS` without approval, stop and
   go to Resolution as a deadlock.

This accept/reject/justify back-and-forth — codex attacks, Claude defends or
concedes in writing — is the heart of the skill. Neither blind acceptance nor blind
dismissal.

## Resolution

- **Converged** (`APPROVED`): present the final `PLAN.md` and a short summary of how
  the grill and the review rounds improved it.
- **Deadlock** (`MAX_ROUNDS` hit): list the unresolved points and your position on
  each; the user breaks the tie.
- **Blocked** (codex unreachable): present the grilled-but-unreviewed plan, clearly
  labeled as not having had the second-model pass.

Then **stop and get explicit user sign-off before any code is written.** This skill
hardens a plan; it does not implement it. If the user then says "do it," build the
agreed plan as normal work.
