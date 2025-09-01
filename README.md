[![geonames-tagger on pypi](https://img.shields.io/pypi/v/geonames-tagger)](https://pypi.org/project/geonames-tagger/)
[![PyPI Downloads](https://static.pepy.tech/badge/geonames-tagger/month)](https://pepy.tech/projects/geonames-tagger)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/geonames-tagger)](https://pypi.org/project/geonames-tagger/)
[![Python test and package](https://github.com/dataresearchcenter/geonames-tagger/actions/workflows/python.yml/badge.svg)](https://github.com/dataresearchcenter/geonames-tagger/actions/workflows/python.yml)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)
[![Coverage Status](https://coveralls.io/repos/github/dataresearchcenter/geonames-tagger/badge.svg?branch=main)](https://coveralls.io/github/dataresearchcenter/geonames-tagger?branch=main)
[![AGPLv3+ License](https://img.shields.io/pypi/l/geonames-tagger)](./LICENSE)
[![Pydantic v2](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/pydantic/pydantic/main/docs/badge/v2.json)](https://pydantic.dev)

# geonames-tagger

[Inspired by countrytagger](https://github.com/alephdata/countrytagger/)

This library finds the names of places in a string of text and tries to associate them with known locations from [geonames.org](https://www.geonames.org/). The goal is to tag a piece (or set) of text with mentioned locations, optionally to refine location names to a more canonized value. As well, the corresponding geoname IDs are returned in a tagging result.

As opposed to the original `countrytagger`, this library doesn't ship with the data included, so one needs to build it locally and then use it with the `GEONAMES_DB` env var set.

## Data

Usage of the GeoNames data is licensed under a [Creative Commons Attribution 4.0 License](https://creativecommons.org/licenses/by/4.0/). Please verify that usage complies with your project.

## Install

    pip install geonames-tagger

## Usage

### cli

    echo "I am from Berlin, Germany" | geonames-tagger tag

this results in the following json response:


## python

```python
from geonames_tagger import tag_location:

text = 'I am in Berlin'
for result in tag_locations(text):
    print(result.name)  # the normalized but original name found in text
    print(result.caption)  # the canonical names as list from GeoNames db
    print(result.ids)  # the GeoName IDs
```

## Building the data

You can re-generate the place database like this:

    geonames-tagger build

This will download GeoNames and parse it into the format used by this library.


## License and Copyright

`geonames-tagger`, (C) 2025 [Data and Research Center – DARC](https://dataresearchcenter.org)

`geonames-tagger` is licensed under the AGPLv3 or later license.

The original `countrytagger` is released under the MIT license.

see [NOTICE](./NOTICE) and [LICENSE](./LICENSE)
