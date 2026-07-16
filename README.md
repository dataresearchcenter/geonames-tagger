[![geonames-tagger on pypi](https://img.shields.io/pypi/v/geonames-tagger)](https://pypi.org/project/geonames-tagger/)
[![PyPI Downloads](https://static.pepy.tech/badge/geonames-tagger/month)](https://pepy.tech/projects/geonames-tagger)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/geonames-tagger)](https://pypi.org/project/geonames-tagger/)
[![Python test and package](https://github.com/dataresearchcenter/geonames-tagger/actions/workflows/build.yml/badge.svg)](https://github.com/dataresearchcenter/geonames-tagger/actions/workflows/build.yml)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)
[![Coverage Status](https://coveralls.io/repos/github/dataresearchcenter/geonames-tagger/badge.svg?branch=main)](https://coveralls.io/github/dataresearchcenter/geonames-tagger?branch=main)
[![AGPLv3+ License](https://img.shields.io/pypi/l/geonames-tagger)](./LICENSE)
[![Pydantic v2](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/pydantic/pydantic/main/docs/badge/v2.json)](https://pydantic.dev)

# geonames-tagger

[Inspired by countrytagger](https://github.com/alephdata/countrytagger/)

This library finds the names of places in a string of text and tries to associate them with known locations from [geonames.org](https://www.geonames.org/). The goal is to tag a piece (or set) of text with mentioned locations, optionally to refine location names to a more canonized value. As well, the corresponding geoname IDs are returned in a tagging result.

As opposed to the original `countrytagger`, this library doesn't ship with the data included, so one needs to build it first and then point the `GEONAMES_PLACES` env var at the built `places.tsv`. Thanks to [anystore](https://github.com/investigativedata/anystore), this can be a local path (the default: `./geonames.db/places.tsv`) or any remote uri, e.g. `s3://mybucket/places.tsv` or `https://example.org/places.tsv`.

## Data

Usage of the GeoNames data is licensed under a [Creative Commons Attribution 4.0 License](https://creativecommons.org/licenses/by/4.0/). Please verify that usage complies with your project.

## Install

    pip install geonames-tagger

## Usage

### cli

    echo "I just visited Sant Julia de loria last week" | geonames-tagger tag

this results in the following json response:

```json
{
  "name": "sant julia de loria",
  "caption": [
    "Sant Julià de Lòria"
  ],
  "id": [
    3039162,
    3039163
  ]
}
```

Input and output are uris handled by `anystore`, so `-i` / `-o` accept local paths, `s3://`, `http(s)://` or `-` for stdin/stdout (the default).

By default, duplicate matches are aggregated: each location is emitted once per input, no matter how many lines mention it. Use `--no-aggregate` to stream one result per match instead:

    geonames-tagger tag -i report.txt --no-aggregate


### python

```python
from geonames_tagger import tag_locations

text = "I am in Berlin"
for result in tag_locations(text):
    print(result.name)  # the normalized name found in the text
    print(result.caption)  # the canonical names as list from GeoNames db
    print(result.id)  # the GeoNames IDs as list
```

## Building the data

You can (re-)generate the places database like this:

    geonames-tagger build

This will download the full [GeoNames dump](https://download.geonames.org/export/dump/) (`allCountries.zip`, ~400 MB) and parse it into the format used by this library, written to `$GEONAMES_PLACES` (default: `./geonames.db/places.tsv`).

Use `-i` to build from an already downloaded dump and `-o` to override the output uri:

    geonames-tagger build -i ./allCountries.zip -o s3://mybucket/places.tsv

During the build, name variants that would produce noisy matches are dropped: very short alternate spellings (tune via `GEONAMES_MIN_ALTERNATE_LENGTH`, default 6), numeric codes, and names that are common dictionary words in major languages (unless the place is big enough to be meant anyway, like Berlin or China). At tagging time, matches that are part of a person's name (e.g. "Heinrich XIII") are suppressed as well.


## License and Copyright

`geonames-tagger`, (C) 2025 [Data and Research Center – DARC](https://dataresearchcenter.org)

`geonames-tagger` is licensed under the AGPLv3 or later license.

The original `countrytagger` is released under the MIT license.

see [NOTICE](./NOTICE) and [LICENSE](./LICENSE)
