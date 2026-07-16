from typing import Annotated, Optional

import typer
from anystore.cli import ErrorHandler
from anystore.io import smart_stream, smart_write_models
from anystore.logging import configure_logging, get_logger
from anystore.util import Took
from rich import print
from rich.console import Console

from geonames_tagger import __version__
from geonames_tagger.generate import build_places_db
from geonames_tagger.settings import Settings
from geonames_tagger.tagger import tag_locations

settings = Settings()
cli = typer.Typer(no_args_is_help=True, pretty_exceptions_enable=settings.debug)
console = Console(stderr=True)
log = get_logger(__name__)


@cli.callback(invoke_without_command=True)
def cli_geonames_tagger(
    version: Annotated[Optional[bool], typer.Option(..., help="Show version")] = False,
):
    if version:
        print(__version__)
        raise typer.Exit()
    configure_logging()


@cli.command("tag")
def cli_tag(
    input_uri: Annotated[
        str, typer.Option("-i", help="Input uri, default stdin")
    ] = "-",
    output_uri: Annotated[
        str, typer.Option("-o", help="Output uri, default stdout")
    ] = "-",
    aggregate: Annotated[
        bool, typer.Option(..., help="Aggregate duplicate matches into one")
    ] = True,
):
    """Tag input text (line by line) and return locations"""
    with ErrorHandler(logger=log):

        buffer = {}

        def _get_matches():
            for text in smart_stream(input_uri, mode="r"):
                if aggregate:
                    buffer.update({n.name: n for n in tag_locations(text)})
                else:
                    yield from tag_locations(text)
            if buffer:
                yield from buffer.values()

        smart_write_models(output_uri, _get_matches())


@cli.command("build")
def cli_build(
    source_uri: Annotated[
        str, typer.Option("-i", help="allCountries.zip uri")
    ] = settings.source_uri,
    output_uri: Annotated[
        str,
        typer.Option(
            "-o",
            help="Output places.tsv uri (default: $GEONAMES_PLACES)",
        ),
    ] = "",
):
    """Build the places database from a GeoNames allCountries.zip dump."""
    out = output_uri or settings.places
    with ErrorHandler(logger=log), Took() as t:
        log.info(
            "Building places db ...",
            source_uri=source_uri,
            uri=out,
            min_alternate_length=settings.min_alternate_length,
        )
        build_places_db(
            source_uri,
            out,
            min_alternate_length=settings.min_alternate_length,
        )
        log.info("Build complete.", took=t.took)
