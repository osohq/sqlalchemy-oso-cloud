# Contributing Guide

## Reporting Issues

If you would like to report a bug, please first ensure that the bug has not
already been reported by searching [the project's open issues on
GitHub][issues].

If you can't find an existing issue, please [open a new one][new-issue]. Be
sure to include as much detail as possible, including a reproducible code
sample.

[issues]: https://github.com/osohq/sqlalchemy-oso-cloud/issues
[new-issue]: https://github.com/osohq/sqlalchemy-oso-cloud/issues/new

### Responsible Disclosure

If you believe you have discovered a security vulnerability in Oso, please send
details of the issue to security@osohq.com. Please do not open a GitHub issue
or otherwise comment about the issue in a public forum.

## Contributing Code

If you would like to contribute to this project, please open a pull request with your changes.
If you haven't already read and signed our
[Contributor License Agreement](https://github.com/osohq/cla/blob/main/individual.md),
you will be asked to do so upon opening your first PR. Thank you for contributing!

We use [Poetry](https://python-poetry.org/) to manage this project.
After [installing Poetry](https://python-poetry.org/docs/#installation),
run `poetry install` to create a virtual environment and install the project's
dependencies.

We use [pytest](https://docs.pytest.org/en/stable/) to run tests.
Use `poetry run pytest` to run the test suite.
If you intentionally change behavior captured in a snapshot, you can update it with
`poetry run pytest --snapshot-update`.

We use [ruff](https://docs.astral.sh/ruff/) for linting and [mypy](https://mypy-lang.org/)
for type checking. You can run them with `poetry run ruff check` and `poetry run mypy .`
respectively.

We use [pdoc](https://pdoc.dev/) to generate the
[API reference documentation](https://osohq.github.io/sqlalchemy-oso-cloud/).
Use `poetry run pdoc sqlalchemy_oso_cloud` to preview it locally.
