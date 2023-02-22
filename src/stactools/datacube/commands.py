import logging
from typing import Optional

import click
import pystac
from click import Command, Group

from stactools.datacube import stac

logger = logging.getLogger(__name__)


def create_datacube_command(cli: Group) -> Command:
    """Creates the stactools-ephemeral command line utility."""

    @cli.group(
        "datacube",
        short_help=("Commands for working with stactools-ephemeral"),
    )
    def datacube() -> None:
        pass

    @datacube.command("extend-item")
    @click.argument("source")
    @click.option("--asset", type=str)
    def extend_item_command(source: str, asset: Optional[str] = None) -> None:
        item = pystac.Item.from_file(source)
        stac.extend_item(item, asset_name=asset)
        item.save_object()

    @datacube.command("create-item")
    @click.argument("source")
    @click.argument("destination")
    def create_item_command(source: str, destination: str) -> None:
        item = stac.create_item(source)
        item.save_object(dest_href=destination)

    # @datacube.command("create-item")
    # @click.argument("source")
    # @click.argument("destination")
    # def create_item_command(source: str, destination: str) -> None:
    #     item = stac.create_item(source)
    #     item.save_object(dest_href=destination)

    # @datacube.command(
    #     "create-collection",
    #     short_help="Creates a STAC collection",
    # )
    # @click.argument("destination")
    # def create_collection_command(destination: str) -> None:
    #     """Creates a STAC Collection

    #     Args:
    #         destination (str): An HREF for the Collection JSON
    #     """
    #     collection = stac.create_collection()

    #     collection.set_self_href(destination)

    #     collection.save_object()

    #     return None

    # @datacube.command(
    #     "create-collection",
    #     short_help="Creates a STAC collection",
    # )
    # @click.argument("destination")
    # def create_collection_command(destination: str) -> None:
    #     """Creates a STAC Collection

    #     Args:
    #         destination (str): An HREF for the Collection JSON
    #     """
    #     collection = stac.create_collection()

    #     collection.set_self_href(destination)

    #     collection.save_object()

    #     return None

    # @datacube.command("create-item", short_help="Create a STAC item")
    # @click.argument("source")
    # @click.argument("destination")
    # def create_item_command(source: str, destination: str) -> None:
    #     """Creates a STAC Item

    #     Args:
    #         source (str): HREF of the Asset associated with the Item
    #         destination (str): An HREF for the STAC Item
    #     """
    #     item = stac.create_item(source)

    #     item.save_object(dest_href=destination)

    #     return None

    return datacube
