---
name: pr-handle
description: Handle a GitHub PR end-to-end in an isolated worktree — verify CI is green and review threads are resolved, run the test suite, merge, update the base branch, and clean up. Use when the user asks to handle, validate-and-merge, or fully process a pull request by number.
disable-model-invocation: true
argument-hint: "<PR-number>"
allowed-tools: Bash(gh:*), Bash(git:*), Bash(pnpm:*), Bash(npm:*), Bash(yarn:*), Bash(cat:*), Bash(ls:*), Read
---

# Handle PR end-to-end

Process pull request **#$ARGUMENTS** from inspection through merge and cleanup.
Run the stages in order. **Abort and report** at any stage that fails — never
merge unless every gate passes.

## 1. Inspect the PR

```
gh pr view $ARGUMENTS --json number,title,state,isDraft,mergeable,mergeStateStatus,statusCheckRollup,headRefName,baseRefName,url
```

Gates:
- `state` is `OPEN` and `isDraft` is `false`
- `mergeable` is `MERGEABLE` and `mergeStateStatus` is `CLEAN`
- every `statusCheckRollup` entry has `conclusion: SUCCESS` (no `PENDING`/`FAILURE`)

Note `headRefName` and `baseRefName` — later steps need them.

## 2. Verify review threads are resolved

```
gh api graphql -f query='
{ repository(owner: "<OWNER>", name: "<REPO>") {
    pullRequest(number: $ARGUMENTS) {
      reviewThreads(first: 50) { nodes {
        isResolved
        comments(first: 20) { nodes { author { login } body path } } } }
      reviews(first: 50) { nodes { author { login } state body } } } } }'
```

Derive `<OWNER>/<REPO>` from `git remote get-url origin`. Every review thread
must have `isResolved: true`. If any is unresolved, list them and abort —
ask the user to resolve them first.

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

Report a per-stage result table: CI checks, review threads, local tests,
merge commit SHA, base-branch update, and cleanup status.
