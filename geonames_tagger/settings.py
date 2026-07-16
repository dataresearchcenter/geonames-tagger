from anystore.settings import BaseSettings
from pydantic_settings import SettingsConfigDict

DEFAULT_SOURCE_URI = "https://download.geonames.org/export/dump/allCountries.zip"
DEFAULT_PLACES = "geonames.db/places.tsv"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="geonames_",
        env_file=".env",
        extra="ignore",
    )

    # Uri of the prebuilt places.tsv — any anystore uri works (local path,
    # `s3://`, `http(s)://`, ...). Env: GEONAMES_PLACES.
    places: str = DEFAULT_PLACES
    source_uri: str = DEFAULT_SOURCE_URI
    # Minimum normalized length for variants drawn from GeoNames
    # `alternatenames`. Short alternates account for most false positives
    # (Sind→Sindh, Mein→Maine, Kern→Kern County, VIII→…, Allen→Allen County).
    # Canonical names and asciinames are unaffected. Lower toward 4 if you
    # need to match transliterations like "Roma" (4); raise higher for
    # stricter canonical-leaning matching.
    min_alternate_length: int = 6
