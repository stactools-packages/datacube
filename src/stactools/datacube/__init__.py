import stactools.core
from stactools.cli.registry import Registry

from stactools.datacube.stac import create_item, extend_asset, extend_item

__all__ = ["extend_item", "extend_asset", "create_item"]

stactools.core.use_fsspec()


def register_plugin(registry: Registry) -> None:
    from stactools.datacube import commands

    registry.register_subcommand(commands.create_datacube_command)


__version__ = "0.1.0"
