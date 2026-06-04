# Codex briefing template

A council briefing has to stand on its own — the reviewer cannot see your
conversation, the repo's history, or what you already concluded. The structure
below is what has reliably produced sharp, code-grounded reviews. Use the *same*
briefing for codex and for the cold-read Claude critic so any disagreement
between them is a real difference of judgment, not a difference of input.

## Structure

```
You are doing an independent <second-opinion / second-opinion review> of
<what>. <One sentence on what you want: verify against the actual code and flag
anything wrong, overstated, missed, or where a failure scenario is implausible.>

# Context

<Where the artifact lives — PR number + repo URL + commit, or file paths.
Enough that the reviewer can locate everything on disk. State the stack briefly
if it matters (e.g. "Vite + React 19.2 SPA").>

# <The artifact>

<Paste the review / plan / decision in full, or for code, the diff and the
exact files and line ranges. If you're handing over your own findings, list
them ranked, each with its file:line and the evidence you based it on — the
reviewer's job is to check your reasoning, so show it.>

# What I want from you

- Verify each claim against the actual code; don't take my word for it.
- Flag findings that are wrong, overstated, or rest on a misread.
- Flag anything important I missed.
- Call out where a failure scenario I describe is implausible in practice.
- Where there's a materially better approach, say so concretely.
```

## What makes these work

- **Point at real code, not summaries.** "verify by running `pnpm build` and
  `pnpm vitest list`" beats "check whether tests double-run." The reviewers have
  read-only repo access — invite them to use it.
- **Show your reasoning, not just your conclusions.** When the artifact is your
  own review, include *why* you flagged each item. A reviewer can only catch a
  flawed inference if they can see it.
- **Invite disagreement explicitly.** "flag anything wrong, overstated, or
  missed" gives permission to push back, which is the entire point of a second
  opinion. Without it, reviewers tend to agree politely.
- **Keep scope tight.** One artifact per convening. A briefing that bundles
  three unrelated questions gets three shallow answers.

## Codex call parameters

Defaults that match a read-only review (from real usage):

| param             | value          | why |
|-------------------|----------------|-----|
| `model`           | `"gpt-5.5"`    | the strong reviewer model |
| `sandbox`         | `"read-only"`  | reads + read-only commands, never edits |
| `approval-policy` | `"never"`      | runs autonomously, never blocks on a prompt |
| `cwd`             | repo root      | absolute path; codex resolves files from here |

`cwd` may also be passed as `config: { cwd: "<repo root>" }` — both forms appear
in practice and behave the same. Continue a started review with
`mcp__codex__codex-reply` and the session id rather than re-sending the briefing.
