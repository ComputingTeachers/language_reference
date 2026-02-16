#!/usr/bin/env -S uv run --script
# /// script
# requires-python = "~=3.14"
# dependencies = [
#   "pyyaml",
# ]
# ///
"""
Generates Github Actions Workflows for languages.

To generate for every language:
    ./generate_github_workflows.py
"""

from collections.abc import Set
from pathlib import Path
from string import Template

import yaml

github_workflow_template = Template(
    """
name: language_reference_$LANGUAGE

on:
  push:
    branches:
      - main
    paths:
      - ".github/workflows/language_reference_$LANGUAGE.yml"
      - "language_reference/languages/$LANGUAGE/**"

jobs:
  language_check_$LANGUAGE:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@main

      - name: $LANGUAGE
        run: docker compose --project-directory language_reference up --build $LANGUAGE
""".lstrip()
)

LANGUAGES: Set[str] = frozenset(
    yaml.safe_load(Path("compose.yaml").read_bytes())["services"].keys()
)

PATH_WORKFLOWS = Path("../").joinpath(".github/workflows/")

for language in LANGUAGES:
    PATH_WORKFLOWS.joinpath(f"language_reference_{language}.yml").write_text(
        github_workflow_template.substitute(LANGUAGE=language)
    )
