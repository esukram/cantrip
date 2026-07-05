---
name: land-pr
description: Land a GitHub PR end-to-end in an isolated worktree — verify CI is green, review threads are resolved, no changes are requested, and no open tasks remain (unchecked task-list items gate through a user-overrulable prompt), run the test suite, merge, update the base branch, and clean up. Use when the user asks to land, validate-and-merge, or fully process a pull request by number.
disable-model-invocation: true
argument-hint: "<PR-number>"
allowed-tools: Bash(gh:*), Bash(git:*), Bash(pnpm:*), Bash(npm:*), Bash(yarn:*), Bash(cat:*), Bash(ls:*), Read, AskUserQuestion
---

# Land PR end-to-end

Process pull request **#$ARGUMENTS** from inspection through merge and cleanup.
Run the stages in order. **Abort and report** at any stage that fails — never
merge unless every gate passes. The only exception is the open-tasks soft gate
(stage 2c), which the user may explicitly overrule.

## 1. Inspect the PR

```
gh pr view $ARGUMENTS --json number,title,state,isDraft,mergeable,mergeStateStatus,statusCheckRollup,headRefName,baseRefName,url
```

Gates:
- `state` is `OPEN` and `isDraft` is `false`
- `mergeable` is `MERGEABLE` and `mergeStateStatus` is `CLEAN`
- every `statusCheckRollup` entry has `conclusion: SUCCESS` (no `PENDING`/`FAILURE`)

Note `headRefName` and `baseRefName` — later steps need them.

## 2. Preflight: review threads, review decision, open tasks

Derive `<OWNER>/<REPO>` from `git remote get-url origin`. Run all three checks
before any local work. 2a and 2b are **hard gates** — if the check fails *or
cannot be completed* (API error, missing scope), abort; no overrule. 2c is a
**soft gate** the user may overrule.

### 2a. Review threads resolved (hard gate)

```
gh api graphql --paginate -f query='
query($endCursor: String) {
  repository(owner: "<OWNER>", name: "<REPO>") {
    pullRequest(number: $ARGUMENTS) {
      reviewThreads(first: 100, after: $endCursor) {
        pageInfo { hasNextPage endCursor }
        nodes { isResolved path } } } } }'
```

Every review thread must have `isResolved: true`. If any is unresolved, list
their paths and abort — ask the user to resolve them first.

### 2b. No changes requested (hard gate)

```
gh pr view $ARGUMENTS --json reviewDecision,latestReviews
```

If `reviewDecision` is `CHANGES_REQUESTED`, abort — list the reviewers whose
entry in `latestReviews` has `state: CHANGES_REQUESTED` and ask the user to
get the reviews re-approved or dismissed first.

### 2c. No open tasks (soft gate — user may overrule)

Scan exactly three surfaces for unticked task-list items (`- [ ]`, `* [ ]`):
the PR body, conversation comments, and top-level review bodies. Skip any
surface authored by a bot (`user.type == "Bot"`) — including the PR body when
the PR author is a bot. Inline review-thread comments are deliberately not
scanned; stage 2a governs those.

```
gh api repos/<OWNER>/<REPO>/pulls/$ARGUMENTS --jq '{author_type: .user.type, body: .body}'
gh api --paginate repos/<OWNER>/<REPO>/issues/$ARGUMENTS/comments --jq '.[] | {author: .user.login, type: .user.type, body: .body}'
gh api --paginate repos/<OWNER>/<REPO>/pulls/$ARGUMENTS/reviews --jq '.[] | {author: .user.login, type: .user.type, body: .body}'
```

- **No unchecked items** → continue silently to stage 3.
- **Unchecked items found** → print the full list (item text + source), then
  ask via `AskUserQuestion` — first option (recommended) **"Stop — resolve
  these first"** aborts the land; second option **"Land anyway (overrule)"**
  continues. Truncate the list inside the question text ("…and N more") if
  it is long. If the scan itself fails, ask the same question stating which
  surface could not be verified.
- If the question cannot be asked (non-interactive run), **abort** — the soft
  gate fails closed.

## 3. Create an isolated worktree

```
git fetch origin
git worktree add ../<repo>-pr$ARGUMENTS <headRefName>
```

Use a sibling directory so the main checkout is untouched.

## 4. Install dependencies and run tests

In the worktree, detect the package manager:
- `pnpm-lock.yaml` → `pnpm install --frozen-lockfile` then `pnpm test`
- `package-lock.json` → `npm ci` then `npm test`
- `yarn.lock` → `yarn install --frozen-lockfile` then `yarn test`

Abort and show output if install or tests fail.

## 5. Merge

Only when stages 1–4 all passed. Do not ask for confirmation — proceed automatically:
```
gh pr merge $ARGUMENTS --merge
gh pr view $ARGUMENTS --json state,mergedAt,mergeCommit
```

Confirm `state` is `MERGED`.

**Permission fallback:** If the merge is blocked by permission classifier, show:
```
gh pr merge $ARGUMENTS --merge
```
and ask the user to run it manually. Then continue to stage 6 only after user confirms the merge succeeded.

## 6. Update the base branch

```
git checkout <baseRefName>
git pull --ff-only
```

## 7. Clean up

Check if `<headRefName>` is currently checked out (in this worktree or any other):
```
git branch --show-current
git worktree list
```

If the branch is checked out:
- Skip the local branch deletion with a clear message explaining the worktree is using it.
- Emit the exact cleanup commands for the user to run after exiting the worktree:
  ```
  cd /path/to/main/repo
  git worktree remove ../<repo>-pr$ARGUMENTS
  git branch -D <headRefName>
  ```

If the branch is not checked out:
```
git worktree remove ../<repo>-pr$ARGUMENTS
git branch -D <headRefName>
```

Then delete the remote branch automatically (do not ask for confirmation):
```
git push origin --delete <headRefName>
```

## Summary

Report a per-stage result table: CI checks, review threads, review decision,
open tasks (noting an overrule if one happened), local tests, merge commit
SHA, base-branch update, and cleanup status.
