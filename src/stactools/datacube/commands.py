import logging
from typing import Optional

import click
import pystac
from click import Command, Group

from stactools.datacube import stac

logger = logging.getLogger(__name__)


def create_datacube_command(cli: Group) -> Command:
    """Creates the stactools-datacube command line utility."""

    @cli.group(
        "datacube",
        short_help=("Commands for working with stactools-datacube"),
    )
    def datacube() -> None:
        pass

    rtol_option = click.option(
        "--rtol",
        type=float,
        default=1.0e-5,
        help="relative tolerance of floating point values to be considered equal",
    )
    use_driver_option = click.option(
        "--use-driver",
        type=str,
        default=None,
        help="specify the driver prefix (like NETCDF or ZARR)",
    )

    @datacube.command("extend-item")
    @click.argument("item_filename")
    @click.option("--asset", type=str, help="name of the asset to extend")
    @rtol_option
    @use_driver_option
    def extend_item_command(
        item_filename: str,
        asset: Optional[str] = None,
        rtol: float = 1.0e-5,
        use_driver: Optional[str] = None,
    ) -> None:
        item = pystac.Item.from_file(item_filename)
        stac.extend_item(
            item, asset_name=asset, rtol=rtol, use_driver=use_driver
        )
        item.save_object()

    @datacube.command("create-item")
    @click.argument("source")
    @click.argument("destination")
    @rtol_option
    @use_driver_option
    def create_item_command(
        source: str,
        destination: str,
        rtol: float = 1.0e-5,
        use_driver: Optional[str] = None,
    ) -> None:
        item = stac.create_item(source, rtol=rtol, use_driver=use_driver)
        item.save_object(dest_href=destination)

    return datacube
