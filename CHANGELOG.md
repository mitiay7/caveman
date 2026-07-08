# Changelog

All notable changes to this fork (mitiay7/caveman) are documented in this
file, one entry per integration commit.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
versions follow upstream releases with a `-fable.N` fork suffix.

## [v1.10.0-fable.1] — 2026-07-09

Curated fork release: five community PRs pending on upstream, reviewed and
integrated with authorship preserved, plus the E6 trigger narrowing deferred
from v1.9.2-fable.1. Net token accounting: SessionStart injection grows
~+200 tokens (Lists rule +170–190, language fold +~25, smart row/examples
filtered out for non-smart sessions); every turn saves ~20 tokens
(reinforcement −35→−15) and every session saves ~160 tokens of always-loaded
frontmatter descriptions plus ~135 from the E6/description rework — long
sessions come out ahead, and the additions buy correctness (list layout,
language stability, no accidental mode flips).

### Added
- New `smart` intensity level — selectivity compression for
  readability-enforcing harnesses (adapted from upstream PR #630 by
  @tristanmuzzu, who also specced it in issue #629, with example-line and
  placement grafts from PR #642 by @Shevanio). Cut content, not grammar:
  full sentences, zero fluff — drops recaps of unchanged plans, restated
  tool output, options not chosen, pleasantries, hedging, repeated
  paths/ids; complex replies end with one plain-language TLDR line. Differs
  from `lite` at reply scale (what gets included), not sentence scale. On
  harnesses that instruct full-sentence readability (Claude Code on
  Fable-class models), `full`/`ultra` fight the harness every turn — prefer
  `lite` or `smart` there (rationale in README only; zero SKILL.md body
  bytes for the note, and the smart table row + `- smart:` example lines
  are filtered per level by the activate hook, so non-smart sessions pay
  nothing). Plumbing: `smart` added to `VALID_MODES` in
  `src/hooks/caveman-config.js` (transitively enables `/caveman smart`
  parsing, `readFlag`, `CAVEMAN_DEFAULT_MODE`, config `defaultMode`, and
  the opencode plugin), both statusline whitelists (`.sh`/`.ps1`), every
  switch-hint surface (SKILL.md, activate fallback, `caveman-activate.md`,
  `caveman-init.js`, openclaw bootstrap + inline fallback,
  `commands/caveman.md` — body also rewritten level-agnostic), the
  caveman-help card, README level/slash tables, and secondary docs. The
  per-turn reinforcement needed no change: PR #660's slim generic anchor is
  already correct for smart. New tests: `/caveman smart` writes the flag
  and the anchor carries no grammar-compression text
  (`tests/test_mode_tracker.py`); activation at `CAVEMAN_DEFAULT_MODE=smart`
  injects only the smart row and smart example lines
  (`tests/test_hooks.py`). Same commit syncs the plugins mirror and
  rebuilds `dist/caveman.skill`.
- New `## Lists` rule in the caveman skill: keep list layout under
  compression — one item per line, sub-items on their own indented lines,
  never a child list inlined into its parent numbered step. Fixes caveman
  smashing lists (worst case: nested child lists) into run-on lines, a gap
  Auto-Clarity previously covered only by dropping caveman entirely
  (upstream PR #669 by @pierrz, cherry-picked with authorship preserved).
  Costs ~170–190 tokens per SessionStart injection; no added line matches
  the activate-hook filter regexes, so the section emits intact for all
  levels including wenyan. Same commit syncs the
  `plugins/caveman/skills/caveman/SKILL.md` mirror and rebuilds
  `dist/caveman.skill` from the updated tree.

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
- Language preservation hardened against English drift (adapted from
  upstream PR #658 by @chengzhen49959): the skill's language rule now states
  that the rules are written in English but the output language always
  matches the user, and that drop-rules apply to per-language filler
  equivalents (e.g. Chinese 的/其实/一些); the per-turn reinforcement anchor
  in `src/hooks/caveman-mode-tracker.js` gains a ~10-token "Reply in user's
  language" clause — previously the one injection point with no language
  rule, whose English-only text repeated every turn dragged non-English
  sessions toward English replies. Deliberately not taken from the PR: the
  duplicate `## Language` section (the rule already exists), the redundant
  activate-fallback hunk, and the 了 example (dropping the aspect marker can
  flip completed → imperative meaning, colliding with the NEVER-drop rule).
  Same commit re-syncs the plugins mirror and rebuilds `dist/caveman.skill`.

### Removed
- Bare brevity phrases ("be brief", "less tokens", "be terse", "shorter
  answers") no longer auto-activate caveman as a persistent session mode
  (E6 trigger narrowing). A one-off brevity request asks for one short
  answer; silently flipping a sticky mode on it distorted every subsequent
  reply. Both trigger surfaces narrowed in lockstep: the
  `caveman-mode-tracker.js` UserPromptSubmit regex now requires an explicit
  durability marker — "always" / "from now on" / "going forward" /
  "by default" directly before the phrase, or a same-sentence session-scope
  marker ("from now on", "going forward", "by default", "for this session")
  within 30 characters after it — and the skill frontmatter description
  drops "less tokens" / "be brief" / the "any token-efficiency request"
  catch-all as activators, gaining an explicit do-NOT-activate-on-one-off
  sentence (the model-side guard the hook cannot provide) plus the restored
  literal "use caveman" trigger that the #662 trim dropped. Explicit
  activation is unchanged: "caveman mode", "talk like caveman",
  "use caveman", "activate caveman", bare "caveman", and all `/caveman`
  slash paths. Durable phrasings ("always be brief", "use fewer tokens from
  now on", "shorter answers for this session") still activate. Asymmetry is
  deliberate: a false negative costs one `/caveman`; a false positive
  silently compresses the rest of the session. Description tax +~25 tokens
  (the negative sentence is load-bearing — do not trim it as fluff). Tests:
  bare/one-off phrases and incidental "always" stay off; durable
  prefix/suffix markers and "use caveman" each pinned
  (`tests/test_mode_tracker.py`). Same commit adds a README historical
  note, syncs the plugins mirror, and rebuilds `dist/caveman.skill`.

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
