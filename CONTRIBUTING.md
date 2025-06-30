# Setup

We use [Poetry](https://python-poetry.org/) to manage this project.
After [installing Poetry](https://python-poetry.org/docs/#installation),
create a virtual environment and install the project's dependencies with:

```bash
poetry install --with dev
```

## Running tests

We use [pytest](https://docs.pytest.org/en/stable/) to run tests.
To run the test suite, run:

```bash
poetry run pytest
```

> Append the `-s` option to display standard output

### Updating test snapshots

If you intentionally change behavior captured in a snapshot, you can update it by running:

```bash
poetry run pytest --snapshot-update
```

### Run the linter

```bash
poetry run ruff check
```

### Run mypy

To run from the current directory:
```bash
poetry run mypy .
```
