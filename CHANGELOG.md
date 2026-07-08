# Changelog

All notable changes to this fork (mitiay7/caveman) are documented in this
file, one entry per integration commit.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
versions follow upstream releases with a `-fable.N` fork suffix.

## [Unreleased]

### Changed
- Skill frontmatter descriptions trimmed ~36% (348 → 223 words across all
  7 skills), saving ~160 tokens of fixed per-session cost — descriptions load
  into the system prompt whether or not a skill fires. All slash-command
  triggers and load-bearing semantics retained (upstream PR #662 by
  @jjmendezrodriguez, merged with authorship preserved). The merge also
  re-syncs the `plugins/caveman/skills/caveman-stats/SKILL.md` mirror, which
  the PR left with the old description, and rebuilds `dist/caveman.skill`
  from the merged tree so the trimmed frontmatter and this fork's body edits
  both land in the zip payload.
- Per-turn reinforcement shrunk from ~35 to ~15 tokens in
  `src/hooks/caveman-mode-tracker.js` and the opencode plugin: the
  UserPromptSubmit reminder now only re-points attention at the SessionStart
  ruleset instead of restating rules every turn (upstream PR #660 by
  @jjmendezrodriguez, merged with authorship preserved).

### Fixed
- Repo-local config (`.caveman/config.json` / `.caveman.json`) now resolves
  against the session's per-event `cwd` (sent on the hook's stdin) instead of
  the hook process's spawn cwd, so directory-scoped defaults — including
  `defaultMode: "off"` — track mid-session directory changes. Covers both the
  natural-language activation site and bare `/caveman` (a call site the
  original PR missed). Adapted subset of upstream PR #634 by @AmanKRoy; the
  PR's per-turn reinforcement gate was dropped because it silently suppressed
  the anchor after an explicit `/caveman <level>` in a `defaultMode: "off"`
  repo.
