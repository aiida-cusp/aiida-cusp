# -*- coding: utf-8 -*-


"""
Utility script comparing the current GitHub-Tag (defined via the
GITHUB_REF evironment variable) to the version defined in the
package's setup.json file

Usage: python version.py $GITHUB_REF
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


def parse_tag_version_from_git(github_ref):
    """
    Parse current version from GitHub tag

    :params github_ref: the GITHUB_REF environment variable contents
        provided by github
    :type github_ref: str
    """
    pattern = r"(?<=^refs/tags/v)([\s\S]+$)"
    match = re.search(pattern, github_ref)
    if match is None:
        raise IOError("unable to parse version from GITHUB_REF")
    return version.parse(match.group(0))


if __name__ == "__main__":
    try:
        github_ref = sys.argv[1]
    except IndexError:
        raise IOError("missing $GITHUB_REF as command line argument")
    github_tag = parse_tag_version_from_git(github_ref)
    json_version = parse_version_from_json(pathlib.Path('.'))
    assert github_tag == json_version, (
           f"version defined in setup.json does not match with github tag "
           f"version ({json_version} =/= {github_tag})")
