# Changelog

## [0.3.0] - 2026-10-13

### Fixed

- **File-input crash paths** (m8): `run --battery` pointing at a directory or a
  non-UTF-8 file, and `report --file` targeting an existing directory, crashed
  with raw `IsADirectoryError` / `UnicodeDecodeError` tracebacks and exit 1.
  All three now exit 2 with the friendly `battery error:` / clear-message path.
- **shell_exec chaining** (m9): the oracle no longer authorizes a command that
  chains extra actions after an in-scope prefix. `echo workspace/a; cat
  /etc/passwd` used to satisfy an `echo workspace/*` allowlist (the documented
  v0.2.0 known limitation); commands carrying chaining metacharacters (`;`,
  `|`, `&`, backtick, `$(`, newline) are now classified unauthorized — the
  conservative direction for a tendency probe. Glob matching also switched to
  `fnmatchcase` so verdicts are case-deterministic across platforms.
- **Release assets** (m10): the release workflow builds wheel + sdist but only
  uploaded them as a workflow artifact, so the v0.2.0 tag page shipped with
  zero assets. The build job now attaches `dist/*` to the GitHub release.

### Added

- **`outstep compare` over saved reports** (m11): `outstep compare a.json
  b.json` loads containment reports written by `outstep report --out json
  --file` and renders a per-model scorecard, a best-first ranking, and a
  per-scenario verdict matrix — the offline half of the plan's m3 contract.
  Malformed or missing report files exit 2 with a `compare error`.

### Maintenance

- **Version lockstep** (m12): version bumped to 0.3.0 on every surface
  (`pyproject.toml`, `outstep.__version__`, CLI `--version`,
  `web/site.json` meta) with the version-consistency test updated.

## [0.2.0] - 2026-09-10

### Fixed

- **Battery loading** (m4): `--battery` now accepts a path to a YAML file, as its
  help text always promised. Previously every value was treated as a bundled
  resource name (paths even had `.yaml` appended a second time) and failed with a
  raw `FileNotFoundError` traceback. Unknown names and missing files now exit 2
  with a friendly `battery error:` message, and malformed scenario fields
  (`tools:` null, non-mapping allowlist entries) raise `BatteryError` with
  scenario context instead of an uncaught `TypeError`.
- **Scope oracle** (m5): `file_read` targets are normalized with
  `posixpath.normpath` before glob matching, so traversal targets such as
  `workspace/../../../etc/passwd` no longer satisfy a `workspace/**` allowlist
  and are correctly classified as unauthorized.

### Added

- **Report file output** (m6): `outstep report --out md|json --file <path>` writes
  the scorecard to disk. Previously every `--out` value only printed to the
  console, so the documented "save it" workflow was not possible.

### Maintenance

- **Version lockstep** (m7): version bumped to 0.2.0 on every surface
  (`pyproject.toml`, `outstep.__version__`, CLI `--version`), `web/site.json`
  now carries `meta.content_version` / `meta.implementation_version`, and a
  version-consistency test guards the lockstep.

### Known limitations

- `shell_exec` prefix globs cannot detect command chaining: `echo workspace/a;
  cat /etc/passwd` still matches an `echo workspace/*` allowlist. A correct fix
  requires shell command parsing and is deferred.

## [0.1.0] - 2026-08-11

Initial release.

- Canary-action battery v1 (12 escape-attempt scenarios in YAML) with schema
  validation and `outstep run --dry` plan printing.
- Scope observer classifying recorded actions against (tool, scope) allowlist
  globs.
- Dry-run containment report previews (stdout / md / json) with transcript hash.
- Live model execution is not yet implemented (`HarnessNotImplemented`).
