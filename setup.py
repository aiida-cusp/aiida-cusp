# -*- coding: utf-8 -*-
"""
Install the aiida-cusp plugin package
"""


import pathlib
import json

from setuptools import setup


setup_json_file = pathlib.Path(__file__).parent.absolute() / 'setup.json'
with setup_json_file.open('r') as setup_json:
    setup_kwargs = json.load(setup_json)

readme_file = pathlib.Path(__file__).parent.absolute() / 'README.md'
with readme_file.open('r') as readme:
    long_description = readme.read()

setup(long_description=long_description, **setup_kwargs)
