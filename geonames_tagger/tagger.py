import re
from functools import cache
from threading import RLock
from typing import Generator

from ahocorasick_rs import AhoCorasick
from anystore.io import smart_open
from anystore.logging import get_logger
from anystore.util import Took
from pydantic import BaseModel
from rigour.names import NameTypeTag, analyze_names

from geonames_tagger.generate import _is_dictionary_word, decode_row
from geonames_tagger.settings import Settings
from geonames_tagger.util import text_norm

settings = Settings()
compiler_lock = RLock()
log = get_logger(__name__)

TOKEN_RE = r"(^|\s){name}(\s|$)"
AHO: AhoCorasick | None = None
DB: dict[str, dict[str, list]] | None = None

# Roman numerals up through XXX cover "Heinrich XIII", "John Paul II", etc.
# Used as a context signal for person-name detection.
_ROMAN_NUMERALS = frozenset(
    "ii iii iv v vi vii viii ix x xi xii xiii xiv xv xvi xvii xviii xix "
    "xx xxi xxii xxiii xxiv xxv xxvi xxvii xxviii xxix xxx".split()
)


def _is_initial_or_roman(token: str) -> bool:
    """Single-letter initials and Roman numerals are person-name context
    signals (e.g. "Lina E.", "Heinrich XIII")."""
    if len(token) == 1 and token.isalpha():
        return True
    return token.lower() in _ROMAN_NUMERALS


def _person_token_norms(text: str) -> set[str]:
    """Run rigour's name tagger over `text` and return the set of normalized
    tokens that appear inside a person-name reference. A token qualifies if
    rigour recognizes it as a name AND it isn't a common dictionary word
    (rigour will spuriously tag German function words like "des", "in", "ein"
    as names because some of those exist as rare surnames in its corpus) AND
    it has an adjacent name token or context signal (initial/Roman)."""
    if not text or not text.strip():
        return set()
    result: set[str] = set()
    for name in analyze_names(NameTypeTag.PER, [text]):
        parts = list(name.parts)
        if not parts:
            continue
        real_name = [False] * len(parts)
        context = [False] * len(parts)
        for i, p in enumerate(parts):
            in_span = any(p in sp.parts for sp in name.spans)
            form = p.form.lower()
            if in_span and not _is_dictionary_word(form):
                real_name[i] = True
            elif _is_initial_or_roman(form):
                context[i] = True
        for i, p in enumerate(parts):
            if not real_name[i]:
                continue
            left = i > 0 and (real_name[i - 1] or context[i - 1])
            right = i < len(parts) - 1 and (real_name[i + 1] or context[i + 1])
            if left or right:
                tnorm = text_norm(p.form)
                if tnorm:
                    result.add(tnorm)
    return result


@cache
def _load() -> None:
    """Stream the prebuilt places file once and build AhoCorasick + lookup."""
    global AHO, DB
    with compiler_lock:
        if AHO is not None and DB is not None:
            return
        uri = settings.places
        log.info("Loading places ...", uri=uri)
        with Took() as t:
            db: dict[str, dict[str, list]] = {}
            with smart_open(uri, "r") as fh:
                for line in fh:
                    if line.strip():
                        norm, ids, captions = decode_row(line)
                        db[norm] = {"id": ids, "caption": captions}
            DB = db
            AHO = AhoCorasick(list(DB.keys()))
        log.info("Loading places complete.", count=len(DB), took=t.took)


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
    if norm is None:
        return
    results = AHO.find_matches_as_strings(norm, overlapping=True)
    if not results:
        return
    person_norms = _person_token_norms(text)
    for result in sorted(results, key=len, reverse=True):
        # If every token of the match falls inside a person-name reference in
        # the source text, the match is almost certainly the person, not the
        # place. Multi-word place names (Sant Julia de Loria) survive because
        # not all of their tokens will be flagged.
        match_tokens = set(result.split())
        if match_tokens and match_tokens.issubset(person_norms):
            continue
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
