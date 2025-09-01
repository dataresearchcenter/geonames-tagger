from pathlib import Path

FIXTURES_PATH = (Path(__file__).parent / "fixtures").absolute()


def test_locationtagger(monkeypatch, tmp_path):
    monkeypatch.setenv("GEONAMES_DB", str(tmp_path))

    from geonames_tagger import generate, tagger

    generate.build_automaton_data(FIXTURES_PATH / "places.csv")

    result = list(tagger.tag_locations("Sant Julia de Loria"))[0]
    assert result.model_dump() == {
        "name": "sant julia de loria",
        "caption": ["Sant Julià de Lòria"],
        "id": [3039162, 3039163],
    }
