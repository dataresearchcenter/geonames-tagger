from pathlib import Path

from anystore.settings import BaseSettings
from anystore.types import Uri
from pydantic import Field
from pydantic_settings import SettingsConfigDict

DEFAULT_SOURCE_URI = "https://download.geonames.org/export/dump/allCountries.zip"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="geonames_",
        env_file=".env",
        extra="ignore",
    )

    data_root: Path = Field(default=Path("geonames.db"), alias="geonames_db")
    source_uri: str = DEFAULT_SOURCE_URI
    places_csv: Path | None = None
    automaton_data: Uri | None = None

    def get_places_path(self) -> Path:
        return self.places_csv or self.data_root / "places.csv"

    def get_automaton_data_uri(self) -> Uri:
        return self.automaton_data or self.data_root / "automaton.json"
