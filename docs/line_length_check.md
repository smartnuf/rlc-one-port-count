# Line-length checker

This is a staged salvage of the useful line-length machinery developed on the
abandoned PR #49–#51 branch stack.

The checker is derived from the corrected path-selection and directive logic at
PR #50 branch commit:

```text
36c0bff5dea042fee4cdec4c4addb3a0b27085db
```

It deliberately does **not** modify `scripts/lint.sh`, `scripts/lint.ps1`,
`scripts/validate_changes.py`, the GitHub Actions workflow, `Makefile`, or
`AGENTS.md`. Consequently, adding these files does not turn the repository's
existing long-line backlog into a mandatory CI failure.

## Initial use

Report all included tracked files without failing:

```bash
.venv/bin/python scripts/check_line_lengths.py --report
```

Report selected files:

```bash
.venv/bin/python scripts/check_line_lengths.py --report \
  README.md src/rice/core.py
```

Check only staged and unstaged tracked files, excluding deleted and untracked
paths:

```bash
.venv/bin/python scripts/check_line_lengths.py --changed
```

Check an explicit committed range:

```bash
.venv/bin/python scripts/check_line_lengths.py \
  --base origin/main \
  --head HEAD
```

Run the focused tests:

```bash
.venv/bin/python -m pytest -q tests/test_line_lengths.py
```

## Exit behaviour

Normal checking returns a nonzero status when diagnostics are present.
`--report` prints the same diagnostics and a summary but returns success. Use
report mode while reducing the inherited backlog.

Do not wire the normal full-tree invocation into `make lint`, `make check`, or
CI until the desired baseline has been reached. A later migration can enforce
the rule for changed files first, or enforce the full tree once it is clean.

## Included files

The default selection uses `git ls-files`, so untracked build and workflow
artefacts are ignored. It checks common hand-maintained source and
documentation
suffixes plus `Makefile`, `AGENTS.md`, `LICENSE`, `.gitignore`, and
`.gitattributes`.

The generated compact snapshot below is excluded explicitly:

```text
data/counts/small-r2-x3.json
```

## Suppression directives

For Python, shell, PowerShell, TOML, YAML, and other hash-comment formats:

```text
# line-length: ignore-next-line -- exact URL required by external system
# line-length: disable -- generated table cannot be wrapped
# line-length: enable
```

For Markdown:

```markdown
<!-- line-length: ignore-next-line -- exact URL -->
<!-- line-length: disable -- generated table cannot be wrapped -->
<!-- line-length: enable -->
```

Reasons are required for `ignore-next-line` and `disable`. Unmatched, nested,
unknown, and overlong directives are errors. Prefer wrapping or refactoring to
adding suppressions.
