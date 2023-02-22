import stactools.datacube


def test_version() -> None:
    assert stactools.datacube.__version__ is not None
