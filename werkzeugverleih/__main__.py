"""
name:
  Werkzeugverleih
copyright:
  (C) 2020
authors:
  Stadler, Jakob
  Sagmeister, Matthias
  @ Technische Hochschule Deggendorf
description:
  Locally-hosted webserver for a tool rental system.
dependencies:
  see requirements.txt
"""

# Proxy to allow starting the application with
# `python -m werkzeugverleih`
from werkzeugverleih.main import main
if __name__ == '__main__':
  main()
