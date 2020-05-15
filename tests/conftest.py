# -*- coding: utf-8 -*-


"""
Collection of pytest fixtures for plugin tests
"""


import pytest


# make fixtures defined by AiiDA available
pytest_plugins = ['aiida.manage.tests.pytest_fixtures']
