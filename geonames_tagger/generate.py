from collections import defaultdict
from functools import lru_cache
from typing import Iterator

from anystore.io import logged_items, smart_open
from anystore.logging import get_logger
from anystore.types import SDict, SDictGenerator, Uri
from wordfreq import zipf_frequency

from geonames_tagger.util import iter_source, text_norm

log = get_logger(__name__)

# Languages checked when deciding whether a candidate is a common dictionary
# word. Multi-lingual on purpose: input text language is not known at build
# time, and a token like "auch" (German "also") or "rolle" (German "role")
# must be filterable even when GeoNames stores it as a city in some country.
COMMON_WORD_LANGS = ("de", "en", "fr", "es", "it", "nl", "pt", "ru")
# zipf > 4.5 ≈ top ~30k most common words in the language.
COMMON_WORD_MAX_ZIPF = 4.5
# Places at or above this population are kept even if the name is a common
# word — protects China, Berlin, Iran, etc.
COMMON_WORD_POP_OVERRIDE = 100_000

# On-disk line format: <norm> \t <ids> \t <captions> \n
# ids is comma-separated ints; captions are joined by US (\x1F) which never
# appears in human-readable text. Tab/newline/US are stripped from caption
# strings on write so the parse is unambiguous.
FIELD_SEP = "\t"
ID_SEP = ","
CAPTION_SEP = "\x1f"


@lru_cache(maxsize=200_000)
def _max_zipf(norm: str) -> float:
    return max(
        (zipf_frequency(norm, lang) for lang in COMMON_WORD_LANGS),
        default=0.0,
    )


def _is_dictionary_word(norm: str) -> bool:
    return _max_zipf(norm) > COMMON_WORD_MAX_ZIPF


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


MIN_NORM_LENGTH = 4


def generate_places(uri: Uri, min_alternate_length: int = 6) -> SDictGenerator:
    """Yield one record per (norm, source row) variant. `min_alternate_length`
    is the length floor applied ONLY to variants drawn from GeoNames
    `alternatenames`; canonical name and asciiname are filtered at
    MIN_NORM_LENGTH (4)."""
    rows = logged_items(
        iter_source(uri), "Load", 10_000, item_name="Row", logger=log, uri=uri
    )
    for row in rows:
        caption = row["name"]
        canonical_norm = text_norm(caption) or ""
        population = int(row.get("population") or 0)
        # Track origin so the length floor differs between canonical and alt.
        variants: list[tuple[str, bool]] = []
        for v in (row.get("name"), row.get("asciiname")):
            if v:
                variants.append((v, False))
        if row.get("alternatenames"):
            for v in row["alternatenames"].split(","):
                if v:
                    variants.append((v, True))
        seen_norms: set[str] = set()
        for name, is_alternate in variants:
            norm = text_norm(name)
            if norm is None:
                continue
            min_len = min_alternate_length if is_alternate else MIN_NORM_LENGTH
            if len(norm) < min_len:
                continue
            if norm in seen_norms:
                continue
            seen_norms.add(norm)
            if norm.replace(" ", "").isdigit():
                continue
            # Drop single-token alt norms that are a strict substring of a
            # longer canonical norm — kills "sind"/"Sindh", "allen"/"Allen
            # County", "fort"/"Fort Bend County", "kern"/"Kern County", etc.
            # If the place is also separately registered under its short name
            # in another GeoNames row, that row's canonical equals its norm
            # and survives this filter.
            if (
                is_alternate
                and " " not in norm
                and len(norm) < len(canonical_norm)
                and norm in canonical_norm
            ):
                continue
            if population < COMMON_WORD_POP_OVERRIDE and _is_dictionary_word(norm):
                continue
            yield {"norm": norm, "caption": caption, "name": name, **transform_row(row)}


def aggregate_places(
    rows: SDictGenerator,
) -> Iterator[tuple[str, list[int], list[str]]]:
    """Collapse per-variant flat rows into one record per norm."""
    ids: dict[str, set[int]] = defaultdict(set)
    captions: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        norm = row["norm"]
        ids[norm].add(int(row["id"]))
        captions[norm].add(row["caption"])
    for norm in ids:
        yield norm, sorted(ids[norm]), sorted(captions[norm])


def _sanitize_caption(caption: str) -> str:
    return caption.replace("\t", " ").replace(CAPTION_SEP, " ").replace("\n", " ")


def encode_row(norm: str, ids: list[int], captions: list[str]) -> str:
    ids_s = ID_SEP.join(str(i) for i in ids)
    cap_s = CAPTION_SEP.join(_sanitize_caption(c) for c in captions)
    return f"{norm}{FIELD_SEP}{ids_s}{FIELD_SEP}{cap_s}\n"


def decode_row(line: str) -> tuple[str, list[int], list[str]]:
    norm, ids_s, cap_s = line.rstrip("\n").split(FIELD_SEP)
    ids = [int(i) for i in ids_s.split(ID_SEP)] if ids_s else []
    captions = cap_s.split(CAPTION_SEP) if cap_s else []
    return norm, ids, captions


def build_places_db(
    source_uri: Uri,
    out_uri: Uri,
    min_alternate_length: int = 6,
) -> None:
    """End-to-end build: GeoNames zip → final tagger-loadable file. `out_uri`
    can be any anystore uri (local path, `s3://`, ...); parent dirs are
    created for local paths."""
    flat = generate_places(source_uri, min_alternate_length=min_alternate_length)
    with smart_open(out_uri, "w") as fh:
        for norm, ids, captions in aggregate_places(flat):
            fh.write(encode_row(norm, ids, captions))
