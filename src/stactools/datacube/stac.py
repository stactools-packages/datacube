import os.path
import re
from datetime import datetime, timedelta
from typing import Any, Dict, Iterable, Iterator, List, Optional, Tuple, Union, cast
from urllib.parse import urlparse

import numpy as np
import rasterio.crs
import shapely.geometry
import stactools.core.projection
from dateutil.parser import parse as parse_datetime
from osgeo import gdal
from pystac import Asset, CommonMetadata, Item
from pystac.extensions.datacube import (
    AdditionalDimension,
    DatacubeExtension,
    Dimension,
    DimensionType,
    HorizontalSpatialDimension,
    HorizontalSpatialDimensionAxis,
    TemporalDimension,
    Variable,
    VariableType,
    VerticalSpatialDimension,
    VerticalSpatialDimensionAxis,
)
from stactools.core.io import ReadHrefModifier

gdal.UseExceptions()


def is_horizontal_x_dimension_name(type_name: str) -> bool:
    return type_name in ("lon", "long", "longitude")


def is_horizontal_y_dimension_name(type_name: str) -> bool:
    return type_name in ("lat", "latitude")


def is_vertical_dimension_name(type_name: str) -> bool:
    return type_name in ("z", "elevation")


def is_temporal_dimension_name(type_name: str) -> bool:
    return type_name == "time"


def get_dimension_type(dimension: Dict[str, Any]) -> str:
    typ: Optional[str] = dimension.get("type")
    if typ:
        return typ

    name = dimension["name"].lower()
    if is_horizontal_x_dimension_name(name):
        return "HORIZONTAL_X"
    elif is_horizontal_y_dimension_name(name):
        return "HORIZONTAL_Y"
    elif is_vertical_dimension_name(name):
        return "VERTICAL"
    elif is_temporal_dimension_name(name):
        return "TEMPORAL"
    else:
        return "OTHER"


UNIT_RE = re.compile(r"(\w+) since (.*)")


def get_time_offset_and_step(unit: str) -> Tuple[datetime, timedelta]:
    match = UNIT_RE.match(unit)
    if match:
        step_unit, offset = match.groups()
        offset = parse_datetime(offset)
        step = timedelta(**{step_unit: 1})
        return offset, step
    raise ValueError(f"Failed to parse time unit from '{unit}'")


def read_dimensions_and_variables(
    href: str, rtol: float = 1.0e-5
) -> Tuple[Dict[str, Dimension], Dict[str, Variable], Dict[str, Any]]:
    url = urlparse(href)
    if not url.scheme:
        path = href
    elif url.scheme in ("ftp", "http", "https"):
        path = f"/vsicurl/{href}"
    elif url.scheme == "s3":
        path = f"/vsis3/{url.netloc}{url.path}"
    # TODO: gs, azure, ...
    else:
        raise ValueError(f"Unsupported HREF {href}")

    ds = gdal.OpenEx(path, gdal.OF_MULTIDIM_RASTER | gdal.GA_ReadOnly)
    info = gdal.MultiDimInfo(ds)

    dimensions = {}
    for dim in info["dimensions"]:
        extent: Union[List[str], List[float]]
        values: Union[List[str], List[float]]
        step: Union[str, float, None]

        typ = get_dimension_type(dim)
        indexing_variable = dim.get("indexing_variable")
        if indexing_variable:
            root = ds.GetRootGroup()
            md_arr = root.OpenMDArrayFromFullname(indexing_variable)
            data = md_arr.ReadAsArray()
        else:
            data = np.arange(int(dim["size"]))

        diff = np.diff(data)
        if len(diff) > 1:
            evenly_spaced = np.allclose(diff, np.mean(diff), rtol=rtol)
            step = float((data[-1] - data[0]) / len(data)) if evenly_spaced else None
            values = (
                [float(v) for v in data] if not evenly_spaced else cast(List[float], [])
            )
        else:
            evenly_spaced = False
            step = None
            values = [float(v) for v in data]

        extent = [float(data[0]), float(data[-1])]

        if indexing_variable:
            array_info = info["arrays"][indexing_variable[1:]]
            unit = array_info.get("unit")
        else:
            unit = None

        properties = {}
        dimension: Dimension
        if typ in ("HORIZONTAL_X", "HORIZONTAL_Y"):
            properties["axis"] = (
                HorizontalSpatialDimensionAxis.X
                if typ == "HORIZONTAL_X"
                else HorizontalSpatialDimensionAxis.Y
            )
            dimension = HorizontalSpatialDimension(
                {
                    "type": DimensionType.SPATIAL,
                    "axis": (
                        HorizontalSpatialDimensionAxis.X
                        if typ == "HORIZONTAL_X"
                        else HorizontalSpatialDimensionAxis.Y
                    ),
                    "extent": extent,
                    "step": step,
                    "unit": unit,
                    **({"values": values} if values else {}),
                }
            )
        elif typ == "VERTICAL":
            dimension = VerticalSpatialDimension(
                {
                    "type": DimensionType.SPATIAL,
                    "axis": VerticalSpatialDimensionAxis.Z,
                    "extent": extent,
                    "step": step,
                    "unit": unit,
                    **({"values": values} if values else {}),
                }
            )
        elif typ == "TEMPORAL":
            # translate extent, values, step according to units
            offset, step_unit = get_time_offset_and_step(unit)
            extent = [
                (offset + extent[0] * step_unit).isoformat(),
                (offset + extent[1] * step_unit + step_unit).isoformat(),
            ]
            values = [(offset + v * step_unit).isoformat() for v in values]
            if step is not None:
                # TODO: maybe refine, using days
                step = f"PT{(step_unit * step).total_seconds()}S"

            # set unit to null deliberately, as we already translated to ISO
            unit = None
            dimension = TemporalDimension(
                {
                    "type": DimensionType.TEMPORAL,
                    "extent": extent,
                    "step": step,
                    **({"values": values} if values else {}),
                }
            )
        else:
            dimension = AdditionalDimension(
                {
                    "type": "other",
                    "extent": extent,
                    "step": step,
                    "unit": unit,
                    **({"values": values} if values else {}),
                }
            )

        # TODO: reference_system

        dimensions[dim["name"]] = dimension

    variables = {}
    for array_name, array_info in info["arrays"].items():
        variables[array_name] = Variable(
            {
                "type": VariableType.DATA,
                "unit": array_info.get("unit"),
                "dimensions": [dim_name[1:] for dim_name in array_info["dimensions"]],
                # TODO: description
            }
        )
    return (dimensions, variables, info)


def _get_dimension(
    dimensions: Iterable[Dimension],
    dim_type: DimensionType,
    axis: Optional[HorizontalSpatialDimensionAxis] = None,
) -> Optional[Dimension]:
    horizontal_dimensions: Iterator[HorizontalSpatialDimension] = (
        cast(HorizontalSpatialDimension, dim)
        for dim in dimensions
        if dim.dim_type == dim_type
    )
    if axis:
        horizontal_dimensions = (
            dim for dim in horizontal_dimensions if dim.axis == axis
        )
    return next(horizontal_dimensions, None)


def _reference_system_to_crs(
    reference_system: Union[str, int, float, Dict[str, Any]]
) -> rasterio.crs.CRS:
    if isinstance(reference_system, int):
        return rasterio.crs.CRS.from_epsg(reference_system)
    return rasterio.crs.CRS(reference_system)


def _get_geometry(
    datacube: DatacubeExtension[Asset], info: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    dimensions = datacube.dimensions.values()
    x_dim = cast(
        Optional[HorizontalSpatialDimension],
        _get_dimension(
            dimensions,
            DimensionType.SPATIAL,
            HorizontalSpatialDimensionAxis.X,
        ),
    )
    y_dim = cast(
        Optional[HorizontalSpatialDimension],
        _get_dimension(
            dimensions,
            DimensionType.SPATIAL,
            HorizontalSpatialDimensionAxis.Y,
        ),
    )
    attributes = info.get("attributes", {})
    if x_dim and y_dim and None not in x_dim.extent and None not in y_dim.extent:
        x_low, x_high = x_dim.extent
        y_low, y_high = y_dim.extent

        crs = _reference_system_to_crs(x_dim.reference_system or 4326)
        proj_geometry = shapely.geometry.mapping(
            shapely.geometry.box(x_low, y_low, x_high, y_high)
        )
        return stactools.core.projection.reproject_geom(
            crs, "EPSG:4326", proj_geometry, precision=6
        )

    elif (
        "geospatial_lat_min" in attributes
        and "geospatial_lat_max" in attributes
        and "geospatial_lon_min" in attributes
        and "geospatial_lon_max" in attributes
    ):
        return cast(
            Dict[str, Any],
            shapely.geometry.mapping(
                shapely.geometry.box(
                    attributes["geospatial_lon_min"],
                    attributes["geospatial_lat_min"],
                    attributes["geospatial_lon_max"],
                    attributes["geospatial_lat_max"],
                )
            ),
        )
    return None


def extend_asset(
    item: Item, asset: Asset, rtol: float = 1.0e-5
) -> DatacubeExtension[Asset]:
    dimensions, variables, info = read_dimensions_and_variables(asset.href, rtol)
    datacube = DatacubeExtension.ext(asset, add_if_missing=True)
    datacube.apply(dimensions, variables)

    if not item.geometry:
        geometry = _get_geometry(datacube, info)
        if geometry:
            item.geometry = geometry
            item.bbox = list(shapely.geometry.shape(geometry).bounds)

    common = CommonMetadata(item)
    time_dimension = cast(
        Optional[TemporalDimension],
        _get_dimension(dimensions.values(), DimensionType.TEMPORAL),
    )
    if time_dimension and time_dimension.extent:
        start, end = time_dimension.extent
        common.start_datetime = parse_datetime(start) if start else None
        common.end_datetime = parse_datetime(end) if end else None
        item.datetime = None
    elif time_dimension and time_dimension.values:
        common.start_datetime = parse_datetime(time_dimension.values[0])
        common.end_datetime = parse_datetime(time_dimension.values[-1])
        item.datetime = None
    elif "time_coverage_start" in info and "time_coverage_end" in info:
        common.start_datetime = parse_datetime(info["time_coverage_start"])
        common.end_datetime = parse_datetime(info["time_coverage_end"])
        item.datetime = None

    return datacube


def extend_item(
    item: Item, asset_name: Optional[str] = None, rtol: float = 1.0e-5
) -> Item:
    if not asset_name:
        for name, asset in item.assets.items():
            if "data" in (asset.roles or ()):
                asset_name = name
                break

    if asset_name is None:
        raise ValueError("Unable to find data asset to extend")

    asset = item.assets[asset_name]
    datacube = extend_asset(item, asset, rtol)

    dimensions = datacube.dimensions.values()
    # add geometry, we assume lon/lat here
    common = CommonMetadata(item)
    if not common.start_datetime and not common.end_datetime and not item.datetime:
        time_dimension = cast(
            Optional[TemporalDimension],
            _get_dimension(dimensions, DimensionType.TEMPORAL),
        )
        if time_dimension and time_dimension.extent:
            start, end = time_dimension.extent
            common.start_datetime = parse_datetime(start) if start else None
            common.end_datetime = parse_datetime(end) if end else None
        elif time_dimension and time_dimension.values:
            common.start_datetime = parse_datetime(time_dimension.values[0])
            common.end_datetime = parse_datetime(time_dimension.values[-1])

    return item


def create_item(
    href: str,
    read_href_modifier: Optional[ReadHrefModifier] = None,
    rtol: float = 1.0e-5,
) -> Item:
    id = os.path.splitext(os.path.basename(href))[0]
    if read_href_modifier:
        href = read_href_modifier(href)

    item = Item(
        id=id,
        geometry=None,
        bbox=None,
        datetime=datetime.now(),
        properties={},
    )

    item.add_asset("data", Asset(href=href, roles=["data"]))
    item.datetime = None
    extend_item(item, "data", rtol)
    return item
