# ecsjobs

Python CLI and Docker image: a scheduled-job wrapper for AWS ECS that runs
jobs (ECS tasks, docker exec, local commands) and sends an email report.
Docs: https://jantman.github.io/ecsjobs/

## Commands

- Install: `uv sync --locked --all-groups`
- Lint: `uv run ruff check`
- Tests: `uv run pytest` (100% coverage is enforced)
- Single test: `uv run pytest ecsjobs/tests/test_x.py::TestY::test_z`
- Docs: `uv run sphinx-build -a -n -W -b html docs/source docs/build/html`
  (warnings are errors; the package must be installed)
- Image: `docker build -t ecsjobs:dev .` then
  `dev/docker_smoke_test.sh ecsjobs:dev` (end-to-end run against mocked AWS)

## Where things live

- `ecsjobs/`: the package. `runner.py` is the CLI entry point, `config.py`
  and `schema.py` load and validate the YAML config, `reporter.py` builds
  the email, `jobs/` has one module per job class.
- `ecsjobs/tests/`: pytest tests, mirroring the package layout.
- `docs/source/`: Sphinx docs (configuration, running, development, API).
- `.github/workflows/`: CI (tests), docs deploy, and release.

## Python and dependency support

- Supported: Python 3.8 through 3.14 (`requires-python = ">=3.8"`; the
  floor is set by `importlib.metadata`). The Docker image uses 3.14.
- The `test` matrix in `.github/workflows/tests.yml` must list exactly the
  versions in the pyproject `Programming Language :: Python :: 3.X`
  classifiers; change requires-python, classifiers, ruff `target-version`
  and the matrix together.
- Dependency lower bounds are tested floors: the `lowest` CI leg installs
  them on the oldest Python with `--resolution lowest-direct`. Only raise
  or lower a floor with a run that proves it.
- `uv.lock` forks by Python version; keep `uv sync --locked --all-groups`
  working on every supported version.

## Conventions

- 80-column lines; ruff rules E/F/W.
- Type annotations on new code.
- Leave existing file headers and copyright strings alone.
- Every change needs tests; coverage must stay at 100%.
- Update `docs/source` when behavior or configuration changes.
- Config YAML is loaded with `yaml.safe_load`; job `command` arrays must
  contain only strings.

## Releasing

- Bump `version` in `pyproject.toml` (the only place it lives) and run
  `uv lock`; merge to `master`.
- `.github/workflows/release.yml` sees a version greater than the latest
  GitHub release, then tests, publishes to PyPI (trusted publishing), pushes
  `ghcr.io/jantman/ecsjobs` (`:<version>` and `:latest`), and creates the
  tag (bare, e.g. `2.0.0`) and GitHub release.
- Never tag manually. There is no changelog file; release notes are the
  GitHub release notes.
