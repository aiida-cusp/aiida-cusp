# -*- coding: utf-8 -*-
# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
# sys.path.insert(0, os.path.abspath('.'))


# -- Project information -----------------------------------------------------

project = 'aiida-cusp'
copyright = '2020, Andreas Stamminger'
author = 'Andreas Stamminger'

# The full version, including alpha/beta/rc tags
release = '0.0.0'

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.intersphinx',
    'sphinx.ext.autodoc',
]

# Disable warnings treated as error during the import stage of the
# autodoc extension (otherwise pymatgen will fail the build when running
# sphinx with -W option due to a UserWarning indicating a missing
# .pmgrc.yaml file...sigh)
autodoc_warningiserror = False

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
on_rtd = os.environ.get('READTHEDOCS', '') == 'True'
if on_rtd:
    from aiida.manage import configuration
    configuration.IN_RT_DOC_MODE = True
    configuration.BACKEND = 'django'
    html_theme = 'default'
else:
    html_theme = 'sphinx_rtd_theme'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = []

# RTD uses a relatively old Sphinx version which uses the `contents` as
# default output document name. Here we set this name manually to `index`
# (which is also the default name used by more recent sphinx versions)
# See also: https://github.com/readthedocs/readthedocs.org/issues/2569
master_doc = 'index'

# targets for intersphinx extension
intersphinx_mapping = {
    'pymatgen':
        ('https://pymatgen.org/', None),
    'aiida':
        ('https://aiida.readthedocs.io/projects/aiida-core/en/latest/', None),
    'ase':
        ('https://wiki.fysik.dtu.dk/ase/', None),
    'py':
        ('https://docs.python.org/3/', None),
}


# -- Things to be run before the documentation is build ----------------------


def run_apidoc_autobuild(_):
    import pathlib
    from sphinx.ext import apidoc
    docs_dir = pathlib.Path(__file__).parent.parent.absolute()
    module_path = str(docs_dir.parent / 'aiida_cusp')
    apidoc_path = str(docs_dir / 'source' / 'module_reference')
    apidoc_options = [
        '--separate',
        #  '--private',
        '--force',
        '--module-first',
        '--no-toc',
        '-d', '3',
        '-o', apidoc_path,
        module_path,
    ]
    sys.path.insert(0, str(docs_dir.parent))
    apidoc.main(apidoc_options)


def setup(app):
    app.connect('builder-inited', run_apidoc_autobuild)
