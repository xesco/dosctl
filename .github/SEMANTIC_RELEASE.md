# Semantic Release Documentation

This project uses automated semantic versioning based on conventional commit messages.

## When Releases ARE Triggered

The following commit types will trigger a new release:

- **`feat:`** - New features → **MINOR** version bump (1.1.1 → 1.2.0)
- **`fix:`** - Bug fixes → **PATCH** version bump (1.1.1 → 1.1.2)  
- **`docs:`** - Documentation changes → **PATCH** version bump
- **`perf:`** - Performance improvements → **PATCH** version bump
- **`BREAKING CHANGE:`** in commit body → **MAJOR** version bump (1.1.1 → 2.0.0)

## When Releases are NOT Triggered

The following commit types will NOT trigger a release:

- **`refactor:`** - Code refactoring (no functionality change)
- **`style:`** - Formatting, missing semicolons, etc
- **`test:`** - Adding or modifying tests
- **`chore:`** - Maintenance tasks
- **`ci:`** - Changes to CI configuration  
- **`build:`** - Changes to build system

## Workflow Steps

When a release is triggered, the workflow:

1. Analyzes commit messages to determine if release is needed
2. Calculates next version number based on commit types
3. Updates version in `pyproject.toml` and `src/dosctl/__init__.py`
4. Builds Python package with new version
5. Runs tests to ensure everything works
6. Commits version changes back to repository
7. Creates Git tag and GitHub release with auto-generated changelog
8. Publishes to PyPI if build artifacts exist

## Examples

```bash
# These will trigger releases:
git commit -m "feat: add new game search feature"      # → 1.1.1 → 1.2.0
git commit -m "fix: resolve Windows path issue"        # → 1.1.1 → 1.1.2
git commit -m "docs: update installation instructions" # → 1.1.1 → 1.1.2

# These will NOT trigger releases:
git commit -m "refactor: clean up code structure"      # No release
git commit -m "test: add unit tests for search"        # No release
git commit -m "chore: update dependencies"             # No release
```
