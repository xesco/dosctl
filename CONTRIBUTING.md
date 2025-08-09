# Commit Message Format

This project uses [Conventional Commits](https://www.conventionalcommits.org/) for automated semantic releases.

## Format

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

## Types

- **feat**: A new feature (triggers minor version bump)
- **fix**: A bug fix (triggers patch version bump)
- **docs**: Documentation changes (triggers patch version bump)
- **style**: Code style changes (formatting, etc.) (triggers patch version bump)
- **refactor**: Code refactoring (triggers patch version bump)
- **test**: Adding or updating tests (triggers patch version bump)
- **build**: Build system changes (triggers patch version bump)
- **ci**: CI/CD changes (triggers patch version bump)
- **perf**: Performance improvements (triggers patch version bump)
- **revert**: Reverting changes (triggers patch version bump)
- **chore**: Maintenance tasks (no version bump)

## Breaking Changes

Add `BREAKING CHANGE:` in the footer or use `!` after the type to trigger a major version bump:

```
feat!: remove deprecated API
```

or

```
feat: add new API

BREAKING CHANGE: removes the old API endpoint
```

## Examples

- `feat: add version flag to CLI` → 0.1.0 → 0.2.0
- `fix: resolve integration test failures` → 0.2.0 → 0.2.1
- `feat!: redesign command structure` → 0.2.1 → 1.0.0
- `docs: update README with new examples` → 0.2.1 → 0.2.2
- `chore: update dependencies` → no version change

## Automatic Process

When you push to `main`:
1. Semantic-release analyzes commit messages since last release
2. Determines version bump based on commit types
3. Updates version in `pyproject.toml` and `__init__.py`
4. Generates changelog
5. Creates GitHub release with release notes
6. Publishes to PyPI automatically
7. Commits version updates back to repo
