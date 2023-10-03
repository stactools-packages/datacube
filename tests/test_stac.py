from datetime import timedelta
from typing import Dict

from pystac import Asset
from pystac.extensions.datacube import (
    AdditionalDimension,
    DatacubeExtension,
    Dimension,
    DimensionType,
    HorizontalSpatialDimension,
    HorizontalSpatialDimensionAxis,
    TemporalDimension,
    Variable,
    VerticalSpatialDimension,
)
from click.testing import CliRunner

from stactools.datacube import stac
from stactools.cli.cli import cli


def test_create_item() -> None:
    item = stac.create_item("tests/data/sresa1b_ncar_ccsm3-example.nc")
    assert item.id == "sresa1b_ncar_ccsm3-example"
    assert len(item.get_assets()) == 1
    assert DatacubeExtension.has_extension(item)
    asset = item.get_assets()["data"]

    assert asset.roles == ["data"]

    datacube = DatacubeExtension.ext(asset)
    lat = datacube.dimensions["lat"]
    lon = datacube.dimensions["lon"]
    bnds = datacube.dimensions["bnds"]
    plev = datacube.dimensions["plev"]
    time = datacube.dimensions["time"]

    assert isinstance(lat, HorizontalSpatialDimension)
    assert lat.dim_type == "spatial"
    assert lat.axis == "y"
    assert lat.extent == [-88.927734375, 88.927734375]
    assert lat.step is None
    assert lat.values is not None

    assert isinstance(lon, HorizontalSpatialDimension)
    assert lon.dim_type == "spatial"
    assert lon.axis == "x"
    assert lon.extent == [0.0, 358.59375]
    assert lon.step == 1.40625
    assert lon.values is None

    assert isinstance(bnds, AdditionalDimension)
    assert bnds.dim_type == "other"
    assert bnds.extent == [0.0, 1.0]
    assert bnds.step is None
    assert bnds.values == [0.0, 1.0]

    assert isinstance(plev, VerticalSpatialDimension)
    assert plev.dim_type == "spatial"
    assert plev.extent == [100000.0, 1000.0]
    assert plev.step is None
    assert plev.values is not None

    assert isinstance(time, TemporalDimension)
    assert time.dim_type == "temporal"
    assert time.extent == ["1999-01-17T12:00:00", "1999-01-18T12:00:00"]
    assert time.step is None
    assert time.values is not None

    assert datacube.variables is not None
    area = datacube.variables["area"]
    msk_rgn = datacube.variables["msk_rgn"]
    pr = datacube.variables["pr"]
    tas = datacube.variables["tas"]
    ua = datacube.variables["ua"]

    assert area.var_type == "data"
    assert area.dimensions == ["lat", "lon"]
    assert area.unit == "meter2"

    assert msk_rgn.var_type == "data"
    assert msk_rgn.dimensions == ["lat", "lon"]
    assert msk_rgn.unit == "bool"

    assert pr.var_type == "data"
    assert pr.dimensions == ["time", "lat", "lon"]
    assert pr.unit == "kg m-2 s-1"

    assert tas.var_type == "data"
    assert tas.dimensions == ["time", "lat", "lon"]
    assert tas.unit == "K"

    assert ua.var_type == "data"
    assert ua.dimensions == ["time", "plev", "lat", "lon"]
    assert ua.unit == "m s-1"


def test_get_dimension_type() -> None:
    assert stac.get_dimension_type({"name": "LON"}) == "HORIZONTAL_X"
    assert stac.get_dimension_type({"name": "long"}) == "HORIZONTAL_X"
    assert stac.get_dimension_type({"name": "Longitude"}) == "HORIZONTAL_X"
    assert stac.get_dimension_type({"name": "lat"}) == "HORIZONTAL_Y"
    assert stac.get_dimension_type({"name": "latitude"}) == "HORIZONTAL_Y"
    assert stac.get_dimension_type({"name": "Z"}) == "VERTICAL"
    assert stac.get_dimension_type({"name": "Elevation"}) == "VERTICAL"
    assert stac.get_dimension_type({"name": "TIME"}) == "TEMPORAL"
    assert stac.get_dimension_type({"name": "unknown"}) == "OTHER"

    assert (
        stac.get_dimension_type({"name": "unknown", "type": "HORIZONTAL_X"})
        == "HORIZONTAL_X"
    )


def test_is_horizontal_x_dimension_name() -> None:
    assert stac.is_horizontal_x_dimension_name("lon")
    assert stac.is_horizontal_x_dimension_name("long")
    assert stac.is_horizontal_x_dimension_name("longitude")


def test_is_horizontal_y_dimension_name() -> None:
    assert stac.is_horizontal_y_dimension_name("lat")
    assert stac.is_horizontal_y_dimension_name("latitude")


def test_is_vertical_dimension_name() -> None:
    assert stac.is_vertical_dimension_name("z")
    assert stac.is_vertical_dimension_name("elevation")


def test_is_temporal_dimension_name() -> None:
    assert stac.is_temporal_dimension_name("time")


def test_iso_duration() -> None:
    assert stac.iso_duration(timedelta(weeks=1)) == "P1W"
    assert stac.iso_duration(timedelta(days=1)) == "P1D"
    assert stac.iso_duration(timedelta(hours=1)) == "PT1H"
    assert stac.iso_duration(timedelta(minutes=1)) == "PT1M"
    assert stac.iso_duration(timedelta(seconds=1)) == "PT1S"
    assert stac.iso_duration(timedelta(seconds=0)) == "PT0S"
    assert stac.iso_duration(timedelta(microseconds=1)) == "PT0.000001S"
    assert (
        stac.iso_duration(
            timedelta(
                weeks=1,
                days=1,
                hours=1,
                minutes=1,
                seconds=1,
                microseconds=1,
            )
        )
        == "P1W1DT1H1M1.000001S"
    )


def test_get_geometry() -> None:
    asset = Asset("http://example.com/data.nc")
    datacube = DatacubeExtension.ext(asset, add_if_missing=False)
    dimensions: Dict[str, Dimension] = {
        "lon": HorizontalSpatialDimension(
            {
                "type": DimensionType.SPATIAL,
                "axis": HorizontalSpatialDimensionAxis.X,
                "extent": [-180, 180],
                "values": [-180, 0, 180],
            }
        ),
        "lat": HorizontalSpatialDimension(
            {
                "type": DimensionType.SPATIAL,
                "axis": HorizontalSpatialDimensionAxis.Y,
                "extent": [-90, 90],
                "values": [-90, 0, 90],
            }
        ),
    }
    variables: Dict[str, Variable] = {}
    datacube.apply(dimensions, variables)
    assert stac.get_geometry(datacube, {}) == {
        "type": "Polygon",
        "coordinates": [
            [
                [180.0, -90.0],
                [180.0, 90.0],
                [-180.0, 90.0],
                [-180.0, -90.0],
                [180.0, -90.0],
            ]
        ],
    }


def test_get_geometry_with_step_adjustment() -> None:
    asset = Asset("http://example.com/data.nc")
    datacube = DatacubeExtension.ext(asset, add_if_missing=False)
    dimensions: Dict[str, Dimension] = {
        "lon": HorizontalSpatialDimension(
            {
                "type": DimensionType.SPATIAL,
                "axis": HorizontalSpatialDimensionAxis.X,
                "extent": [-179.5, 179.5],
                "step": 1,
            }
        ),
        "lat": HorizontalSpatialDimension(
            {
                "type": DimensionType.SPATIAL,
                "axis": HorizontalSpatialDimensionAxis.Y,
                "extent": [-89.5, 89.5],
                "step": 1,
            }
        ),
    }
    variables: Dict[str, Variable] = {}
    datacube.apply(dimensions, variables)
    assert stac.get_geometry(datacube, {}) == {
        "type": "Polygon",
        "coordinates": [
            [
                [180.0, -90.0],
                [180.0, 90.0],
                [-180.0, 90.0],
                [-180.0, -90.0],
                [180.0, -90.0],
            ]
        ],
    }


def test_get_geometry_from_metadata() -> None:
    asset = Asset("http://example.com/data.nc")
    datacube = DatacubeExtension.ext(asset, add_if_missing=False)
    dimensions: Dict[str, Dimension] = {}
    variables: Dict[str, Variable] = {}
    datacube.apply(dimensions, variables)
    metadata = {
        "attributes": {
            "geospatial_lon_min": -180,
            "geospatial_lat_min": -90,
            "geospatial_lon_max": 180,
            "geospatial_lat_max": 90,
        }
    }
    assert stac.get_geometry(datacube, metadata) == {
        "type": "Polygon",
        "coordinates": (
            (
                (180.0, -90.0),
                (180.0, 90.0),
                (-180.0, 90.0),
                (-180.0, -90.0),
                (180.0, -90.0),
            ),
        ),
    }


def test_use_driver(tmp_path):
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "datacube",
            "create-item",
            "--use-driver",
            "ZARR",
            "tests/data-files/test.zarr",
            tmp_path / "out.json",
        ],
    )
    print(result.stdout)
    assert result.exit_code == 0
