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

    @datacube.command("extend-item")
    @click.argument("source")
    @click.option("--asset", type=str)
    @click.option("--rtol", type=float, default=1.e-5)
    def extend_item_command(source: str, asset: Optional[str] = None, rtol: float = 1.e-5) -> None:
        item = pystac.Item.from_file(source)
        stac.extend_item(item, asset_name=asset, rtol=rtol)
        item.save_object()

    @datacube.command("create-item")
    @click.argument("source")
    @click.argument("destination")
    @click.option("--rtol", type=float, default=1.e-5)
    def create_item_command(source: str, destination: str, rtol: float = 1.e-5) -> None:
        item = stac.create_item(source, rtol=rtol)
        item.save_object(dest_href=destination)

    return datacube
