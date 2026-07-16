from pathlib import Path

FIXTURES_PATH = (Path(__file__).parent / "fixtures").absolute()


def test_locationtagger(monkeypatch):
    monkeypatch.setenv("GEONAMES_PLACES", str(FIXTURES_PATH / "places.tsv"))

    from geonames_tagger import tagger

    tagger._load.cache_clear()
    tagger.AHO = None
    tagger.DB = None
    tagger.settings = tagger.Settings()

    result = list(tagger.tag_locations("Sant Julia de Loria"))[0]
    assert result.model_dump() == {
        "name": "sant julia de loria",
        "caption": ["Sant Julià de Lòria"],
        "id": [3039162, 3039163],
    }
