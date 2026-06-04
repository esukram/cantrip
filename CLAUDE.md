# cantrip — project conventions

A personal Claude Code plugin marketplace. Each plugin lives under `plugins/<name>/`
with a `.claude-plugin/plugin.json` manifest; the marketplace is declared in
`.claude-plugin/marketplace.json`.

## Semantic versioning (non-negotiable)

Every change to a skill/plugin MUST bump its version following
[Semantic Versioning 2.0.0](https://semver.org) (`MAJOR.MINOR.PATCH`):

- **MAJOR** — backward-incompatible changes (renamed/removed args, changed
  invocation, behavior that breaks existing usage).
- **MINOR** — backward-compatible new functionality.
- **PATCH** — backward-compatible bug fixes, doc/wording tweaks that don't
  change behavior.

When bumping a plugin, update the version in BOTH its `plugin.json` and the
matching entry in `marketplace.json` so they stay in sync. No skill change ships
without a version bump.

## READMEs

Do not add a "Repository layout" / file-tree section to README files — it's
duplicate information. Keep READMEs focused on what the thing is, install/usage,
and the component list.
