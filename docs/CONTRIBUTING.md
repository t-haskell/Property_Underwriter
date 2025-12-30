# Contributing

Thank you for contributing to Property Underwriter! This guide documents the expected workflow for changes and how to keep refactors reviewable.

## Quick start

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

For the frontend:

```bash
cd frontend
npm install
```

## Recommended workflow

1. Create a focused branch for the change.
2. Keep pull requests small, especially for refactors. Prefer mechanical moves in one PR, behavior changes in a follow-up.
3. Update or add documentation when you introduce new workflows, providers, or configuration.

## Tests & checks

Backend checks (run from the repo root):

```bash
pytest -q
ruff check .
mypy src tests
```

Frontend checks:

```bash
cd frontend
npm run lint
npm test
```

## Documentation updates

When you touch architecture, workflows, or provider behavior:

- Update `docs/ARCHITECTURE.md` with the folder map or data flow changes.
- Update `docs/PROVIDER_GUIDE.md` for provider interfaces or configuration.
- Ensure `README.md` links stay current.

## Code conventions

- Keep provider logic deterministic and avoid side-effects outside of the persistence layer.
- Prefer small, composable functions in `src/services` and `src/core`.
- Avoid introducing new dependencies without a clear justification.

## Submitting a PR

- Summarize the intent and impact in the PR description.
- Call out any behavior changes or migrations explicitly.
- Include test output or note when tests were not run.
