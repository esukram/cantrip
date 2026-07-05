# land-pr

A Claude Code skill that takes a pull request from inspection all the way through
merge and cleanup — running every stage in order and **aborting the moment a gate
fails**, so a PR is never merged unless CI is green, review threads are resolved,
no changes are requested, and the test suite passes. Unchecked task-list items on
the PR are a softer gate: they prompt you and you may explicitly land anyway.

## What it does

Given a PR number, it runs these stages and stops at the first failure:

1. **Inspect the PR** — state is `OPEN`, not a draft, `MERGEABLE`/`CLEAN`, and every
   status check rolled up to `SUCCESS`.
2. **Preflight the PR state** — three checks before any local work:
   - every review thread must be resolved (hard gate, paginated — unresolved ones
     are listed and the run aborts);
   - the review decision must not be `CHANGES_REQUESTED` (hard gate — the
     requesting reviewers are listed and the run aborts);
   - no unchecked task-list items (`- [ ]`) in the PR body, conversation comments,
     or review bodies, ignoring bot-authored content (soft gate — findings are
     listed and you choose between stopping or explicitly landing anyway; in
     non-interactive runs this fails closed and aborts).
3. **Create an isolated worktree** — a sibling checkout of the PR branch so your main
   working copy is never touched.
4. **Install dependencies and run tests** — auto-detects the package manager
   (`pnpm` / `npm` / `yarn`) from the lockfile and runs the test suite.
5. **Merge** — only after stages 1–4 pass; falls back to printing the command for you
   to run if a permission gate blocks the automated merge.
6. **Update the base branch** — fast-forward pull on the base branch.
7. **Clean up** — remove the worktree, delete the local and remote branches (or emit
   exact cleanup commands when the branch is still checked out).

It finishes with a per-stage result table: CI checks, review threads, local tests,
merge commit SHA, base-branch update, and cleanup status.

## Usage

This skill is **manually invoked** (`disable-model-invocation: true`) and takes the
PR number as its argument. Once installed (`/plugin install land-pr@cantrip`):

- `/land-pr 42`
- "Land PR #42 end-to-end."
- "Validate and merge pull request 42."

## Requirements

- The [`gh`](https://cli.github.com) GitHub CLI, authenticated for the repository.
- `git` with worktree support (any modern version).
- A Node project using one of `pnpm` / `npm` / `yarn` for the test stage.

## License

[MIT](../../LICENSE)
