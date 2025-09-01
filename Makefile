all: generate

geonames.db:
	mkdir -p geonames.db

geonames.db/allCountries.zip: geonames.db
	curl -s -o geonames.db/allCountries.zip https://download.geonames.org/export/dump/allCountries.zip

generate: geonames.db/allCountries.zip
	geonames-tagger build -i geonames.db/allCountries.zip

install:
	poetry install --with dev --all-extras

lint:
	poetry run flake8 geonames_tagger --count --select=E9,F63,F7,F82 --show-source --statistics
	poetry run flake8 geonames_tagger --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

pre-commit:
	poetry run pre-commit install
	poetry run pre-commit run -a

test:
	poetry run pytest -v --capture=sys --cov=geonames_tagger --cov-report lcov

build:
	poetry run build

clean:
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +
