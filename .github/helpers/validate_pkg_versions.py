# -*- coding: utf-8 -*-


"""
Utility script which reads and comparing all version tags defined
throughout the package source, i.e. read versions from

* aiida_cusp/__init__.py
* setup.json
* docs/source/conf.py

"""


import re
import sys
import json
import pathlib

from packaging import version


def parse_version_from_json(path_to_repo_root):
    """
    Parse version from setup.json file

    :param path_to_repo_root: path to the repository root folder
    :type path_to_repo_root: pathlib.Path
    """
    path_to_json = pathlib.Path(path_to_repo_root) / "setup.json"
    with open(path_to_json, 'r') as json_file:
        setup_kwargs = json.load(json_file)
    try:
        pkg_version = setup_kwargs.get('version')
        return version.parse(pkg_version)
    except KeyError:
        raise IOError("unable to parse version string from setup.json")


def parse_version_from_init(path_to_source_root):
    """
    Parse version from project's __init__.py file

    :param path_to_source_root: path to the source root folder of the
        package, i.e. `aiida_cusp` located in the repository root folder
    :type path_to_source_root: pathlib.Path
    """
    path_to_init = pathlib.Path(path_to_source_root) / "__init__.py"
    with open(path_to_init, 'r') as init_file:
        content = init_file.read()
    pattern = r"(?<=__version__\s=\s[\'\"])[\s\S]+?(?=[\"\']\n)"
    match = re.search(pattern, content)
    if match is None:
        raise IOError("unable to parse version string from __init__.py")
    return version.parse(match.group(0))


def parse_version_from_conf(path_to_source_root):
    """
    Parse current version from the sphinx conf.py file

    :params path_to_source_root: path to the source root folder of the
        documentation, i.e. ./docs/source
    :type github_ref: str
    """
    path_to_conf = pathlib.Path(path_to_source_root) / "conf.py"
    with open(path_to_conf, 'r') as conf_file:
        content = conf_file.read()
    pattern = r"(?<=release\s=\s[\'\"])[\s\S]+?(?=[\"\']\n)"
    match = re.search(pattern, content)
    if match is None:
        raise IOError("unable to parse version from Sphinx conf.py")
    return version.parse(match.group(0))


if __name__ == "__main__":
    json_version = parse_version_from_json(pathlib.Path('.'))
    init_version = parse_version_from_init(pathlib.Path('./aiida_cusp'))
    conf_version = parse_version_from_conf(pathlib.Path('./docs/source'))
    # now check if the parsed versions do match
    assert conf_version == json_version, (
           f"version defined in setup.json does not match with version "
           f"defined in Sphinx conf.py ({json_version} =/= {conf_version})")
    assert conf_version == init_version, (
           f"version defined in __init__.py does not match with version "
           f"defined in Sphinx conf.py ({init_version} =/= {conf_version})")
    assert json_version == init_version, (
           f"version defined in setup.json does not match with version "
           f"defined in __init__.py ({json_version} =/= {init_version})")
