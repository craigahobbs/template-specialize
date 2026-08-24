# AGENTS.md

Notes for coding agents working in this repository.

**template-specialize** is a small, stable CLI that renders [Jinja2](https://jinja.palletsprojects.com/) templates (one file or a directory tree). Prefer the smallest change that preserves behavior. Public contracts live in argparse, `README.md`, and the unittest suite — not in comments.

## python-build

This is a [python-build](https://github.com/craigahobbs/python-build#readme) package. Read the python-build skill before running tests, lint, coverage, or changing the Makefile: [`../python-build/SKILL.md`](../python-build/SKILL.md) if that file exists, otherwise [https://raw.githubusercontent.com/craigahobbs/python-build/main/SKILL.md](https://raw.githubusercontent.com/craigahobbs/python-build/main/SKILL.md).

Local Makefile overrides:

- `TESTS_REQUIRE` — `botocore >= 1.0.0` (tests only; the AWS extension imports it lazily)
- `PYLINT_ARGS` — missing docstring checks disabled
- no `SPHINX_DOC` — `make doc` is a no-op

## Layout

| Path | Role |
| --- | --- |
| `src/template_specialize/main.py` | CLI, environment merge, render, rename/delete |
| `src/template_specialize/aws_parameter_store.py` | `aws_parameter_store` Jinja2 extension |
| `src/template_specialize/__main__.py` | `python -m template_specialize` |
| `src/tests/` | `unittest` suite |
| `Makefile` | python-build stub |
| `pyproject.toml` | package metadata, version, dependencies, console script |
| `README.md` | user documentation; the Usage block must match argparse |
| `CHANGELOG.md` | release history; regenerate with `make changelog` |

The installable package is `template_specialize` only (`package-dir = {"" = "src"}`). Keep the empty `__init__.py` files; unittest discovery depends on `src/tests` being a package.

## Code style

Match the existing files. Do not restyle, add type annotations, or introduce a formatter config.

- MIT license header (comment + LICENSE URL) on every `.py` file.
- 4-space indent, single quotes, UTF-8.
- Docstrings are not required (pylint `missing-*-docstring` is disabled). Keep the existing module and `main()` docstrings.
- Errors go through `argparse.ArgumentParser.exit` (status `2`, or `0` for `--dump`). Tests assert exact stderr text — do not rephrase messages as a cleanup.
- Platform-only branches use `# pragma: no cover`. The botocore import fallback uses `# pragma: nocover`. Keep each file's existing spelling; do not delete `os.sep` / Windows path code as unused.
- `# pylint: disable=` only where pylint cannot see a Jinja or protected-access invariant.

## Behavioral contracts

Easy to break with a "simplification":

**Jinja2.** `StrictUndefined`, `keep_trailing_newline=True`, loader `FileSystemLoader([src_dir, *searchpaths])`. Names passed to Jinja are POSIX paths (`pathlib.Path.as_posix()` on Windows).

**Environment files (`-c`).** JSON object of name → `{parents?, values?}`. Lines matching `^\s*//` are stripped; no `#` or `/* */` comments. Duplicate names across files error. `parents` must be a list of strings. Inheritance is depth-first along `parents`; later parents and the environment's own `values` deep-merge over earlier ones. Circular parent chains error. Unknown `-e` errors even if no `-c` was given.

**Deep merge (`_merge_values`).** Dicts merge by key. Lists merge by index (extra source items append). Scalars replace. If types disagree, source wins (a dict or list replaces a dest of another type).

**CLI keys (`-k`).** `json.loads(value)` on success (`1`, `true`, `{"a": 1}` are typed); otherwise the raw string. Repeated keys deep-merge. CLI keys overlay environment values.

**`--dump`.** Writes sorted, 4-space JSON of the template variables (including `now` as ISO-8601) and exits without writing DST.

**Render shapes.** File→file and directory→directory. File→directory and directory→file fail with status 2.

**`template_specialize_rename`.** Registered only when SRC is a directory. Operations are recorded during render and applied after every file is written. First argument is a destination-relative POSIX path; omit the second argument to delete. The new name must be a basename (no directory component). Paths that escape the destination directory are rejected (`os.path.commonpath` + `os.path.samefile`). Renaming onto an existing directory deletes that directory first unless it is the same path.

**`aws_parameter_store`.** botocore is optional at runtime and required for tests. One SSM client per environment, `get_parameter(..., WithDecryption=True)`, values cached on the Jinja environment. Client errors become `ValueError` including the AWS error code.

**Python 3.14+.** Pass `color=False` to `ArgumentParser`. **`-i`** appends Jinja include search paths.

## Tests

Follow `src/tests/test_main.py`: `create_test_files` temp trees, patch `sys.stdout` / `sys.stderr`, assert exit codes and exact output. AWS tests mock `botocore.session` — do not call AWS.

`TestMain.test_console_script` expects the `template-specialize` console script next to `sys.executable` (editable install).

## Docs and releases

| Change | Also update |
| --- | --- |
| argparse flags or help | `README.md` Usage block and tests |
| error / `--dump` text | tests that assert the string |
| env merge or JSON comments | `TestParseEnvironments`, `TestMergeEnvironment` |
| rename/delete | `TestMain` rename tests |
| AWS extension | `test_aws_parameter_store.py` and `TestMain.test_aws_parameter_store*` |
| supported Python versions | `pyproject.toml` classifiers |
| user-visible behavior | tests, then `CHANGELOG.md` |

Commit subjects are short, lowercase, and imperative. Release commits look like `template-specialize 1.6.3`. Changelog commits look like `update changelog`.

## Do not

- Reintroduce PyYAML or non-JSON environment files.
- Treat `template_specialize` as a public library API; the product is the CLI.
- Expand scope beyond the requested change.
