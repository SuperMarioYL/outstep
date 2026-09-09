# Changelog

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
