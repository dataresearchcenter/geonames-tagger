from collections import defaultdict
from threading import RLock

from ahocorasick_rs import AhoCorasick
from anystore.io import (
    SDict,
    SDictGenerator,
    Uri,
    logged_items,
    smart_stream_csv,
    smart_stream_json,
    smart_write_json,
)
from anystore.logging import get_logger
from anystore.util import Took

from geonames_tagger.settings import Settings
from geonames_tagger.util import iter_source, text_norm

compiler_lock = RLock()
settings = Settings()
log = get_logger(__name__)


def transform_row(row: SDict) -> SDict:
    return {
        "id": row["geonameid"],
        "feature": row.get("feature_code"),
        "country": row.get("country_code"),
        "admin1": row.get("admin1_code"),
        "admin2": row.get("admin2_code"),
        "admin3": row.get("admin3_code"),
        "admin4": row.get("admin4_code"),
    }


def generate_places(uri: Uri) -> SDictGenerator:
    # places = defaultdict(list)
    rows = logged_items(
        iter_source(uri), "Load", 100_000, item_name="Row", logger=log, uri=uri
    )
    for row in rows:
        caption = row["name"]
        names = set([row["name"]])
        if row.get("asciiname"):
            names.update([row["asciiname"]])
        if row.get("alternatenames"):
            names.update(row["alternatenames"].split(","))
        for name in names:
            norm = text_norm(name)
            if norm is None or len(norm) < 4:
                continue
            yield {"norm": norm, "caption": caption, "name": name, **transform_row(row)}


def generate_automaton_data(in_uri: Uri) -> dict[str, dict[str, list[int | str]]]:
    data: dict[str, dict[str, set[int | str]]] = defaultdict(lambda: defaultdict(set))
    for row in smart_stream_csv(in_uri):
        data[row["norm"]]["id"].add(int(row["id"]))
        data[row["norm"]]["caption"].add(row["caption"])
    return {k: {k2: list(v2) for k2, v2 in v.items()} for k, v in data.items()}


PLACES_CSV = settings.get_places_path()
AUTOMATON_JSON = settings.get_automaton_data_uri()


def build_automaton_data(
    places_csv_uri: Uri = PLACES_CSV, out_uri: Uri = AUTOMATON_JSON
) -> Uri:
    automaton = generate_automaton_data(places_csv_uri)
    smart_write_json(out_uri, [automaton])
    return out_uri


def load_automaton(data_uri: Uri) -> AhoCorasick:
    log.info("Loading automaton ...", uri=data_uri)
    with compiler_lock, Took() as t:
        tokens = []
        for data in smart_stream_json(data_uri):
            tokens = data.keys()
            break  # we only have 1 line here
        aho = AhoCorasick(tokens)
        log.info("Loading automaton complete.", took=t.took)
        return aho
