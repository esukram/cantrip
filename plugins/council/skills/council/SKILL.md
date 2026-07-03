---
name: council
description: Use this skill to get a thorough independent second opinion before acting on something — a plan, a technical or architectural decision, a code review or audit you've produced, or a choice between approaches. It convenes a "council": sends the artifact to codex (an external model, read-only) plus a separate independent Claude critique, then runs a multi-pass loop where the voices re-attack council's own draft verdict until it converges, reconciles everything against the actual code, expands the disagreements that survive into an explored option map, and reports what's worth acting on. When voices still disagree on something only the human can settle — intent, risk, scope, priority — it pulls the human in to arbitrate (interactive contexts only). Reach for it when the user is about to commit and wants to be sure ("is this plan sound?", "am I missing anything?", "before I merge", "the right call?"), wants findings verified ("cross-check these audit findings", "any false positives?"), is torn between options, or asks to "get a second opinion", "sanity-check this", or "have codex/the council look at it". Offer it proactively after a significant review, audit, or plan. For a quick single-pass read with no loop and no questions, use `council:fast` instead. For vetting existing work or a pending decision — not a first-pass code review, bug hunt, or research.
---

# Council: a thorough independent second opinion

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

This is the **thorough default**. It does three things a single pass can't:

- **Multi-pass review** — after reconciling once, it hands its *own draft
  verdict* back to the voices to attack, and loops until a pass surfaces nothing
  new (always ≥2 passes, capped at `MAX_PASSES`). First-pass blind spots get a
  second look.
- **Divergence expansion** — a disagreement that *survives* the loop between
  two strong voices signals unexplored design space. Instead of flattening it
  to A-vs-B, council expands the human-bound conflicts into an option map:
  the hidden assumption driving the split plus 2–4 alternatives with tradeoffs.
- **Human arbitration** — when, after the loop settles, the voices still
  disagree on something **only the human can settle** (intent, risk, scope,
  priority), it pulls the human in to decide rather than synthesizing a verdict
  on its own — in interactive contexts only.

For a quick, fully autonomous single pass with no loop and no questions, reach
for **`council:fast`** instead.

## Tunables

| Variable           | Default | Purpose |
|--------------------|---------|---------|
| `MAX_PASSES`       | `3`     | Hard cap on review passes, counting Pass 1. Always run ≥2. |
| `MAX_ARBITRATIONS` | `3`     | Hard cap on `AskUserQuestion` arbitration prompts per run. Past the cap, remaining judgment-owned conflicts are listed under "Human decision needed". |
| `MAX_DEEP_DIVES`   | `5`     | Max surviving human-bound conflicts given the divergence-expansion treatment per run. `0` disables the step. |

## When to convene

Trigger explicitly when asked for a second opinion, sanity-check, cross-check,
or outside review of code/a review/an audit/a plan/a decision. For a quick or
low-stakes gut-check — or any headless/unattended run where a single autonomous
pass is all that's wanted — reach for **`council:fast`** instead; this skill is
the thorough, iterate-and-arbitrate path.

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

## Step 2 — Pass 1: convene both voices in parallel

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
**Capture the `threadId` from the response** — the later passes (Step 4) resume
this same codex session so its critique carries full prior context. If no
`threadId` comes back, note it; codex's later passes will have to be fresh,
non-session-aware calls (see loop failure handling).

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

## Step 3 — Triage and reconcile into a draft verdict (the real work)

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

This reconciliation is your **draft verdict** — not the final report yet. It's
what the voices attack in the next step.

## Step 4 — The multi-pass loop (autonomous, voices only)

Instead of stopping at one reconciliation, hand the draft verdict back to the
voices and let them attack it. This loop is **fully autonomous** — voices only,
no human — so it runs in *every* context, interactive or not.

**Always run at least 2 passes.** Loop until a pass surfaces nothing new, or
until `MAX_PASSES` (default 3) is hit.

### Each pass-2+ turn

Hand each voice council's *current draft verdict* and ask it to attack:
confirm what holds, push back, surface what the prior pass missed.

- **Codex** resumes the **same session** via `mcp__codex__codex-reply` using the
  `threadId` from Step 2, so its critique carries full prior context:

  ```
  mcp__codex__codex-reply({
    threadId: "<captured id>",
    prompt: "<council's current draft verdict>\n\nThis is my reconciled draft from the prior pass. Attack it: confirm what holds, push back where I'm wrong, and surface anything we missed. Structure your reply as — New material objections / Disagreements with my draft / Restatements (no change) / Verdict: stable | unstable."
  })
  ```

  `codex-reply` accepts only `threadId` + `prompt`; read-only is locked at
  session start (Step 2) and inherited by every resume.
- **The cold-read critic** is a spawned subagent. If the Agent tooling lets you
  continue the same subagent thread, reuse it. **Otherwise spawn a fresh critic
  each pass and feed it council's current draft + the prior pass's objections as
  context** — informed, even when not session-continuous. Don't claim "same
  critic" where continuity isn't available — **label it fresh in the log.**

### Required pass-2+ response shape

Each voice must return a structured reply so you can reconcile and detect
convergence consistently:

- **New material objections** — points not yet covered that change the verdict.
- **Disagreements with council's draft** — where the voice thinks your draft is
  wrong.
- **Restatements (no change)** — points already covered; no new information.
- **Verdict: stable | unstable.**

### Convergence rule

After each pass, classify **every** objection raised as one of:

- `new-material` — a genuinely new point that bears on the verdict.
- `restated / already-covered` — already in the draft, just reworded.
- `non-material` — doesn't change the verdict (style, taste, noise).

**Verify the code-checkable ones yourself** before accepting them — same bar as
Step 3. Re-reconcile the draft to absorb anything real.

**Converged = a pass yields zero `new-material` objections** (the draft is
stable). Otherwise loop. Stop unconditionally at `MAX_PASSES`. Record, per pass,
what changed — or "converged — no new objections."

### Loop failure handling

Pass-2+ voice calls can fail. Extend the Step-0 codex-absent handling to these
later calls:

- **Codex can't resume** (`threadId` missing, reply errors) → fall back to a
  **fresh codex call marked non-session-aware** for that pass.
- **A voice is entirely unreachable mid-loop** → degrade to the remaining
  voice(s) and note the missing one.
- **No voice can run pass 2** → stop and report the loop as **incomplete**. The
  ≥2 floor is best-effort, never a hang.

Classification, divergence expansion, and human arbitration (Steps 5–7) fire
**once, on the conflicts that survive the stopped loop** (converged or
`MAX_PASSES`) — never on transient conflicts a later pass might dissolve.
Expansion is additionally skipped when the loop ended incomplete.

## Step 5 — Decide which surviving conflicts need the human

Council auto-reconciles everything it can. After the loop stops, escalate a
conflict to the human **only when the disagreement hinges on user-owned
judgment** — intent, risk tolerance, scope, or priority — something council
cannot settle by reading the code. **Code-verifiable disagreements council
investigates and decides itself; it does not escalate them.**

### Rubric — escalate or decide?

| Conflict | Owner | Action |
|----------|-------|--------|
| Voices disagree on whether a helper already exists, or whether a call can throw | Code-settleable | **Council decides** — read the code and rule. |
| Voices disagree on whether a regex actually matches the input | Code-settleable | **Council decides** — test it. |
| Voices disagree on whether to optimize for latency or simplicity here | User-owned | **Escalate** — depends on what the user values. |
| Voices disagree on whether this edge case is in scope for this PR | User-owned | **Escalate** — scope is the user's call. |

**Tie-breaker — when unsure, do not call `AskUserQuestion`. Report council's
lean** under "Human decision needed" and move on.

Apply a **hard cap** (`MAX_ARBITRATIONS`, default 3) on arbitration questions
per run. Past the cap, list remaining judgment-owned conflicts under "Human
decision needed" rather than firing more prompts.

## Step 6 — Expand surviving disagreements (divergence expansion)

A disagreement that survives the stopped loop between two strong voices is a
signal: the design space there is probably richer than either position. Before
arbitration, expand the human-bound conflicts into an explored option map
instead of flattening them to A-vs-B.

**Selection.** From the surviving **human-bound** conflicts — the interactive
arbitration queue first (the first `MAX_ARBITRATIONS`), then the remaining
"Human decision needed" entries; on noninteractive runs, order by the severity
of council's lean — pick up to `MAX_DEEP_DIVES`. Log which conflicts were
expanded and which were skipped for the cap — no silent truncation.
`MAX_DEEP_DIVES` (5) > `MAX_ARBITRATIONS` (3) is intentional: overflow maps
enrich the "Human decision needed" entries, and the step runs equally on
noninteractive runs — there, the report is the whole output. Conflicts council
decides itself (code-settleable) are **not** expanded.

**One position-neutral prompt, both voices.** Embed the full conflict context
(both positions and the evidence each rests on) so neither voice needs session
memory to work on it:

> Two reviewers durably split on the conflicts below. For each: diagnose the
> hidden assumption driving the split, then map the option space this
> disagreement points at — 2–4 concrete alternatives (including positions
> neither took), each with what it trades away and when it's the right choice.

Each option comes back structured — **label / what it trades away + when it's
right / any claim needing verification** — so arbitration options can be built
without synthesizing from loose prose.

**Mechanics.** One call per voice. **Codex gets a fresh, non-session call by
design** — not `codex-reply`. Resuming would hand one voice full memory of the
position it defended for up to `MAX_PASSES` passes while the critic starts
cold: structural anchoring at the exact step whose purpose is de-anchoring,
and asymmetric inputs break the "identical inputs, real disagreements"
doctrine (Step 1). The loop is different — there, attacking the draft benefits
from context, so resume is right. The critic is a fresh subagent, labeled
fresh as usual.

**Reconcile the maps.** Merge both voices' options per conflict and dedupe.
Verify the load-bearing feasibility claims of **every option that appears
anywhere** — in the arbitration question or the report — or label the option
explicitly unverified. Pruning to the question's 4-option cap (Step 7) affects
only which options reach `AskUserQuestion`, never which are verified.

**Non-reopening rule.** Expansion never reopens the loop and never escalates a
new conflict in the same run. New material surfaced here lands under "Worth
considering" marked *(late expansion finding, \<actual source(s)\>, not
loop-tested)* — honest source attribution even when both voices raised it. An
option that exposes a genuinely distinct conflict is logged the same way.

**Failure handling.** Best-effort — expansion never blocks the verdict. One
voice down → single-voice expansion, noted. No voice reachable → skip the
step, fall back to the binary conflict presentation, and log the reason.

## Step 7 — Arbitrate (interactive contexts only)

Whether council may call `AskUserQuestion` is **context-gated, not
failure-detected.** `AskUserQuestion` is a blocking primitive with no
headless/timeout contract — depending on its failure would hang an unattended
run. So decide *up front* by this rule:

> **Council may call `AskUserQuestion` only if the current user request
> explicitly invoked council, OR the user explicitly opted into council
> arbitration earlier in this same chat.**

In every other case — including the auto-fired-after-`/review` /
before-planning path, and any headless/cron/piped run — council takes the
**noninteractive path**: it **never calls the tool**, lists each judgment-owned
conflict under "Human decision needed" with its lean (unresolved pending user
input), and proceeds to synthesize only the parts it legitimately can
(consensus + code-settleable conflicts it decided itself). **When the gate is
uncertain, err toward the noninteractive path — fail safe, never hang.**

### The interactive mechanic

For each escalated conflict (up to `MAX_ARBITRATIONS`), make **one
`AskUserQuestion` call** — a sequence, never a batched form. One conflict per
call. The first option is council's **lean / suggested default**, labelled
`(Recommended)`, framed as "default if you value X" — a recommendation to push
against, *not* an authoritative verdict (these conflicts hinge on user judgment
by construction). A competing option states the dissenting voice's position; the
tool's automatic **"Other"** is the escape hatch.

For an **expanded** conflict (Step 6), build the options from its map instead:
up to 4 options, council's lean still first and `(Recommended)`, each
description carrying the tradeoff ("choose this if you value X; gives up Y")
and voice attribution where an option came from one voice. **Both original
split positions are guaranteed slots** — map alternatives fill the remainder —
so the human is never shown a durable two-voice split with one side missing.
The full map still appears in the report (Step 8) even when the question was
pruned to 4. Un-expanded conflicts (past the cap, or expansion failed/skipped)
keep the binary form above.

```
AskUserQuestion({
  questions: [{
    header: "Scope",
    question: "Voices split on whether the empty-input case belongs in this PR. Settle it?",
    multiSelect: false,
    options: [
      { label: "Defer to a follow-up (Recommended)",
        description: "Default if you value keeping this PR tight. Codex's view: it's a separate concern and untested here. Why recommended: nothing in this diff depends on it." },
      { label: "Handle it here",
        description: "Critic's view: shipping the path without the guard leaves a latent crash. Pulls the fix into this PR." }
    ]
  }]
})
```

The human's choice **settles that conflict — it is binding, not advisory.** If
we interrupt the human, their decision governs the output. Record it (Step 8).

## Step 8 — Report the verdict

Present a reconciled report, not a transcript. Use this shape:

```
# Council verdict: <artifact>

**Consensus (act on these)**
- <point> — <file:line>, <one-line why it's real>

**Conflicts (council's call)**
- <point> — codex says X, critic says Y; my read: <which, why>

**Human-arbitrated**
- <point> — codex said X, critic said Y; my lean: Z. You decided: <decision>.
  Justification: <why>.
  Options explored (if expanded): <full map, one-line tradeoffs; chosen
  option marked; unverified options labeled>

**Human decision needed** (unresolved — pending user input)
- <point> — codex says X, critic says Y; my lean: Z. Hinges on <intent/risk/
  scope/priority>; not put to you (noninteractive run / past the cap).
  Options explored (if expanded): <full map, one-line tradeoffs; recommended
  option marked; unverified options labeled>

**Worth considering (single-source / late expansion)**
- <point> — <source>, <file:line>
- <point> — (late expansion finding, <actual source(s)>, not loop-tested)

**Dismissed**
- <point> — <why it doesn't hold, with code reference>

**Passes run**
- <n> (converged / hit MAX_PASSES / incomplete) — <one line per pass on what
  changed>
- Expansion: expanded <n> of <m> surviving human-bound conflicts
  (MAX_DEEP_DIVES=<k>) — or "Expansion skipped: <reason>"

**Recommended next actions**
- <ordered, concrete>
```

Two named buckets carry the human-judgment conflicts, and **each
escalation-worthy conflict appears in exactly one of them** — never both, never
duplicated back under Conflicts:

- **Human-arbitrated** — interactive path: the conflict was put to the human and
  *decided*. Records which voice said what, council's lean, the decision, and
  the justification — mirroring an accept/reject/justify-in-writing trail.
- **Human decision needed** — noninteractive path (or past the cap): the
  conflict hinges on user judgment but was *not* put to the human. Records
  council's lean and is flagged **unresolved pending user input**.

A "Human decision needed" entry is an explicit **still-open item**, not a
settled result — the parent `/review` or planning flow must treat it as a
genuine open question, not just rendered text.

Then stop and let the user decide. This skill reconciles and recommends — it
does **not** auto-apply changes. If the user then says "do it", implement the
agreed actions as normal work.

For further follow-up questions to codex outside the loop, continue the same
session with `mcp__codex__codex-reply` using the `threadId` rather than starting
fresh, so codex keeps its context.

## Scaling to the task

This skill is the thorough path — every run is multi-pass, and it will arbitrate
judgment calls with you when the context allows. A quick gut-check on a small or
low-stakes decision doesn't need that ceremony: reach for **`council:fast`**,
which does one autonomous pass with a light triage and reports conflicts as
prose. Match the effort to the stakes — `fast` for a quick read, `council` for a
pre-merge review of a risky migration.
