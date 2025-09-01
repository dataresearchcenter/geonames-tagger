from typing import Annotated, Optional

import typer
from anystore.cli import ErrorHandler
from anystore.io import (
    smart_stream,
    smart_write_csv,
    smart_write_json,
    smart_write_models,
)
from anystore.logging import configure_logging, get_logger
from anystore.util import Took
from rich import print
from rich.console import Console

from geonames_tagger import __version__
from geonames_tagger.generate import (
    build_automaton_data,
    generate_automaton_data,
    generate_places,
)
from geonames_tagger.settings import Settings
from geonames_tagger.tagger import tag_locations
from geonames_tagger.util import PLACES_FIELDNAMES

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
):
    """Tag input text (line by line) and return locations"""
    with ErrorHandler(logger=log):

        def _get_matches():
            for text in smart_stream(input_uri, mode="r"):
                yield from tag_locations(text)

        smart_write_models(output_uri, _get_matches())


@cli.command("build")
def cli_build(
    source_uri: Annotated[
        str, typer.Option("-i", help="allCountries.zip uri")
    ] = settings.source_uri,
):
    """Build the complete database in LOCATIONS data root"""
    with ErrorHandler(logger=log), Took() as t:
        log.info("Building locations database ...", uri=settings.data_root)
        log.info(
            "Building places csv ...",
            source_uri=source_uri,
            uri=settings.get_places_path(),
        )
        places = generate_places(source_uri)
        smart_write_csv(settings.get_places_path(), places)
        log.info("Building places csv complete.", took=t.took)
        log.info("Building automaton data ...", uri=settings.get_automaton_data_uri())
        build_automaton_data(settings.get_places_path())
        log.info("Building automaton data complete.", took=t.took)


@cli.command("build-places")
def cli_build_places(
    input_uri: Annotated[
        str, typer.Option("-i", help="allCountries.zip uri")
    ] = settings.source_uri,
    output_uri: Annotated[
        str, typer.Option("-o", help="Output uri, default stdout")
    ] = "-",
):
    """Generate places csv"""
    with ErrorHandler(logger=log):
        places = generate_places(input_uri)
        smart_write_csv(output_uri, places, fieldnames=PLACES_FIELDNAMES)


@cli.command("build-automaton")
def cli_build_automaton(
    input_uri: Annotated[
        str, typer.Option("-i", help="places csv, default stdin")
    ] = "-",
    output_uri: Annotated[
        str, typer.Option("-o", help="Output uri, default stdout")
    ] = "-",
):
    """Generate automaton json data"""
    with ErrorHandler(logger=log):
        log.info("Generating automaton json ...", uri=input_uri)
        with Took() as t:
            data = generate_automaton_data(input_uri)
            smart_write_json(output_uri, [data])
            log.info("Generate complete.", uri=output_uri, took=t.took)
