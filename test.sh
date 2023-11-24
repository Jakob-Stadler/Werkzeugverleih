#!/bin/sh
find ./tests/scratch/ ! -name '.gitignore' -type f  -exec rm -f "{}" +
./venv/bin/pytest --cov=werkzeugverleih --cov-report xml:cov.xml --cov-report html:htmlcov --cov-report term-missing
