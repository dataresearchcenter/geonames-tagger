import csv
import io
import zipfile

from anystore.io import smart_open
from anystore.types import SDictGenerator, Uri
from anystore.util import clean_dict
from normality import normalize, squash_spaces

SOURCE_FIELDNAMES = (
    "geonameid",
    "name",
    "asciiname",
    "alternatenames",
    "latitude",
    "longitude",
    "feature class",
    "feature code",
    "country code",
    "cc2",
    "admin1 code",
    "admin2 code",
    "admin3 code",
    "admin4 code",
    "population",
    "elevation",
    "dem",
    "timezone",
    "modification date",
)

TARGET_FIELDNAMES = (
    "geonameid",
    "name",
    "asciiname",
    "alternatenames",
    "feature class",
    "feature code",
    "country code",
    "admin1 code",
    "admin2 code",
    "admin3 code",
    "admin4 code",
    "population",
)

FEATURES = ("A", "P")  # admin areas and cities, villages
MIN_NAME_LENGTH = 8  # for P (cities): drop short ambiguous city names
MIN_NAME_LENGTH_A = 4  # for A (admin): looser, countries like "Iran" are 4 chars
MIN_POPULATION = 5_000

PLACES_FIELDNAMES = (
    "id",
    "norm",
    "caption",
    "name",
    "feature",
    "country",
    "admin1",
    "admin2",
    "admin3",
    "admin4",
)


def iter_source(uri: Uri) -> SDictGenerator:
    with smart_open(uri) as fh:
        with zipfile.ZipFile(fh) as zh:
            with zh.open("allCountries.txt") as h:
                th = io.TextIOWrapper(h)
                for row in csv.DictReader(
                    th, fieldnames=SOURCE_FIELDNAMES, delimiter="\t"
                ):
                    if row["feature class"] not in FEATURES:
                        continue
                    pop = int(row.get("population") or 0)
                    name_len = len(row["name"])
                    if row["feature class"] == "P":
                        if name_len < MIN_NAME_LENGTH or pop < MIN_POPULATION:
                            continue
                    else:  # "A" — admin areas: less strict on length, same on pop
                        if name_len < MIN_NAME_LENGTH_A or pop < MIN_POPULATION:
                            continue
                    yield clean_dict(
                        {
                            k.replace(" ", "_"): v
                            for k, v in row.items()
                            if k in TARGET_FIELDNAMES
                        }
                    )


def text_norm(text: str) -> str:
    text = normalize(text, ascii=True) or ""
    if not text:
        return text
    return squash_spaces(text)
