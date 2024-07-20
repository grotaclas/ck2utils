import json
import re
import warnings
import inspect
from pathlib import Path
from typing import List

from localpaths import eu4dir, outpath, cachedir, eu4mod_paths

_eu4_version: str | None = None
_eu4_full_version: str | None = None


def eu4_version():
    global _eu4_version, _eu4_full_version
    if _eu4_version is None:
        json_object = json.load(open(eu4dir / 'launcher-settings.json'))
        _eu4_version = json_object['rawVersion'].removeprefix('v')
        _eu4_full_version = json_object['version']
    return _eu4_version


def eu4_major_version():
    return '.'.join(eu4_version().split('.')[0:2])


def eu4_full_version() -> str:
    """a long version string like 'EU4 v1.33.3.0 France (5010)'"""
    global _eu4_full_version
    if _eu4_full_version is None:
        eu4_version()  # eu4_version() reads the information
    return _eu4_full_version


def verified_for_version(version, extra_message=''):
    """issue a warning if the eu4 version is newer than the version parameter"""
    if version < eu4_version():
        warnings.warn(' The code in the function "{}" was last verified for eu4 version {}. '
                      'Please verify that it is still correct and update the version number. {}'.format(
                        inspect.stack()[1].function, version, extra_message), stacklevel=2)


def mod_suffix(mod_paths: List[Path]) -> str:
    suffix = ''
    for mod in mod_paths:
        suffix += '_' + re.sub(r'[^a-zA-Z0-9._]', '_', str(mod))

    return suffix


eu4outpath = outpath / (eu4_version() + mod_suffix(eu4mod_paths))

if not eu4outpath.exists():
    eu4outpath.mkdir(parents=True)

if cachedir:
    # the full version number also contains the checksum which the unmodded game has. Including it ensures that
    # the cache gets invalidated if the game changes while the version number is unchanged(this can happen in
    # unreleased versions). The re.sub is to avoid potential problems with weird characters in the version string
    eu4cachedir = cachedir / re.sub(r'[^a-zA-Z0-9._]', '_', eu4_full_version() + mod_suffix(eu4mod_paths))
else:
    eu4cachedir = None
