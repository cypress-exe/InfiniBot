# Contributing to InfiniBot

Thanks for your interest in improving InfiniBot! This document covers how to
get set up, the expected workflow, and what makes a good pull request.

## Before you start

- **Bug fixes and small improvements** - feel free to open a PR directly.
- **New features or larger changes** - please open an issue first to
  discuss the approach. This avoids wasted effort on something that might
  not fit the project's direction.
- Check existing [issues](https://github.com/cypress-exe/InfiniBot/issues)
  and [pull requests](https://github.com/cypress-exe/InfiniBot/pulls) to
  avoid duplicating work.
- Review the [license](LICENSE) usage terms before contributing derivative
  work. In particular, InfiniBot may not be used to run a competing public
  bot service.

## Development setup

InfiniBot runs inside Docker. See the [README](README.md#-quick-start) for
full setup instructions. In short:

```bash
git clone https://github.com/cypress-exe/InfiniBot.git
cd InfiniBot
sudo bash build.bash
sudo bash run.bash        # will error until you set DISCORD_AUTH_TOKEN in .env
sudo bash rebuild_and_run.bash
```

Dependencies are managed with [uv](https://docs.astral.sh/uv/) and pinned in
`pyproject.toml` / `uv.lock`. The project targets Python 3.13+.

Developer documentation for internal systems (database, config, event
harness, etc.) lives in the `./documentation` folder.

## Making changes

1. Fork the repository and create a feature branch off `main`:
   ```bash
   git checkout -b feature/short-description
   ```
2. Make your changes, keeping commits focused and scoped to a single
   purpose.
3. Follow the existing code style in the file you're editing rather than
   introducing a new convention.
4. Add or update tests where behavior changes (see below).
5. Update relevant docs in `./documentation` if you change internal
   architecture, config, or developer-facing behavior.

## Running tests

Tests run inside the Docker container:

```bash
./run_tests.bash
```

Useful flags:
- `--skip-build` - reuse the existing container image instead of rebuilding.
- `--run-all` - run the full test suite (used in CI).

CI (`.github/workflows/ci.yml`) builds the Docker image and runs the test
suite on every push and pull request to `main`. Please make sure tests pass
locally before opening a PR.

## Submitting a pull request

1. Push your branch and open a PR against `main`.
2. Fill out the pull request template, including a clear description of
   **what** changed and **why**.
3. Link any related issues (e.g. `Fixes #123`).
4. Ensure CI is passing. PRs with failing checks generally won't be
   reviewed until fixed.
5. Be responsive to review feedback. Small, iterative PRs are easier to
   merge than large ones that sit open.

## Reporting bugs and requesting features

Use [GitHub Issues](https://github.com/cypress-exe/InfiniBot/issues) with
the appropriate template. For security vulnerabilities, do **not** open a
public issue (see [SECURITY.md](SECURITY.md) instead).

## Questions

Join the [InfiniBot Discord server](https://discord.gg/mWgJJ8ZqwR) if you
want to discuss an idea before writing code, or need help getting your dev
environment running.

## Source Disclosure
This document was generated with Claude Sonnet 5 and reviewed/edited by cypress.exe.