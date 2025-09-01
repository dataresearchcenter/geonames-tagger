import re
from functools import cache
from threading import RLock
from typing import Generator

from anystore.io import smart_stream_json
from anystore.logging import get_logger
from pydantic import BaseModel

from geonames_tagger.generate import load_automaton
from geonames_tagger.settings import Settings
from geonames_tagger.util import text_norm

settings = Settings()
compiler_lock = RLock()
log = get_logger(__name__)

TOKEN_RE = r"(^|\s){name}(\s|$)"
AHO = None
DB = None


def _load_db():
    global DB
    with compiler_lock:
        for data in smart_stream_json(settings.get_automaton_data_uri()):
            DB = data
            break


def _load_automation():
    global AHO
    with compiler_lock:
        AHO = load_automaton(settings.get_automaton_data_uri())


@cache
def _load():
    if AHO is None:
        _load_automation()
    if DB is None:
        _load_db()


class Location(BaseModel):
    name: str
    caption: list[str]
    id: list[int]


def get_match(norm: str) -> Location | None:
    _load()
    res = DB.get(norm)
    if res is not None:
        return Location(name=norm, **res)


def tag_locations(text: str) -> Generator[Location, None, None]:
    """
    Extract known geonames from arbitrary text.
    """
    _load()
    norm = text_norm(text)
    if norm is not None:
        results = AHO.find_matches_as_strings(norm, overlapping=True)
        for result in sorted(results, key=len, reverse=True):
            if norm == result:
                match = get_match(norm)
                if match is not None:
                    yield match
                    return
            pat = TOKEN_RE.format(name=result)
            if re.search(pat, norm):
                match = get_match(result)
                if match is not None:
                    yield match
