# stactools-datacube

[![PyPI](https://img.shields.io/pypi/v/stactools-datacube)](https://pypi.org/project/stactools-datacube/)

- Name: datacube
- Package: `stactools.datacube`
- [stactools-datacube on PyPI](https://pypi.org/project/stactools-datacube/)
- Owner: @constantinius
- STAC extensions used:
  - [datacube](https://github.com/stac-extensions/datacube/)
- [Browse the example in human-readable form](https://radiantearth.github.io/stac-browser/#/external/raw.githubusercontent.com/stactools-packages/datacube/main/examples/item/item.json)

This stactools extension package allows to create or extend STAC Items
dealing with multi-dimensional data formats and to extract `datacube` related
metadata from these assets.

This extension relies on the GDAL multi-dimensional raster capabilities via
the official Python API.

## STAC Examples

- [Item](examples/item/item.json)

## Installation

```shell
pip install "pygdal==$(gdal-config --version).*"
pip install stactools-datacube
```

## Command-line Usage

This command creates a new STAC Item from a multi-dimensional file like a
netCDF:

```shell
stac datacube create-item source destination
```

The following command extends an existing STAC Item, optionally by
specifying an explicit asset:

```shell
stac datacube extend-item source --asset asset-name
```

Use `stac datacube --help` to see all subcommands and options.

### Fixing GDAL driver

Sometimes it is necessary to fix the GDAL driver to be used. For example: ZARRs
on HTTP storages. For this, the `--use-driver` option can be used:

```shell
stac datacube create-item --use-driver ZARR http://example.com/some.zarr/ out.json
```

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
