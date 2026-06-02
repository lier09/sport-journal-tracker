#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/.."
python -m src.main run-daily --days-back 7 --sources rss crossref pubmed --report
