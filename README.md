# stactools-datacube

[![PyPI](https://img.shields.io/pypi/v/stactools-datacube)](https://pypi.org/project/stactools-datacube/)

- Name: datacube
- Package: `stactools.datacube`
- [stactools-datacube on PyPI](https://pypi.org/project/stactools-datacube/)
- Owner: @constantinius
- [Dataset homepage](http://example.com)
- STAC extensions used:
  - [datacube](https://github.com/stac-extensions/datacube/)
- [Browse the example in human-readable form](https://radiantearth.github.io/stac-browser/#/external/raw.githubusercontent.com/stactools-packages/datacube/main/examples/collection.json)

A short description of the package and its usage.

## STAC Examples

- [Collection](examples/collection.json)
- [Item](examples/item/item.json)

## Installation

```shell
pip install stactools-datacube
```

## Command-line Usage

Description of the command line functions

```shell
stac datacube create-item source destination
```

Use `stac datacube --help` to see all subcommands and options.

## Contributing

We use [pre-commit](https://pre-commit.com/) to check any changes.
To set up your development environment:

```shell
pip install -e .
pip install -r requirements-dev.txt
pre-commit install
```

To check all files:

```shell
pre-commit run --all-files
```

To run the tests:

```shell
pytest -vv
```
