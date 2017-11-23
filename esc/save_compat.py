#!/usr/bin/env python3

import argparse
from pathlib import Path
import pickle
import re
import sys
import git
from ck2parser import rootpath, cachedir, is_codename, SimpleParser
from print_time import print_time


parser = SimpleParser()

digestible_mods = ['SWMH']

digest_dir = cachedir / 'digests'
cp_filename = 'save_compat.txt'

repo_map = {}


def parse_arguments():
    argparser = argparse.ArgumentParser(
        description='Create and compare mod digests for save-compatibility.')
    argparser.add_argument('mod', nargs='+', type=Path, help='mod path')

    args = argparser.parse_args()

    for path in args.mod:
        if not path.is_dir():
            raise ValueError('{} is not an existing directory'.format(path))
        if not path.name in digestible_mods:
            raise ValueError("don't know how to digest {}".format(path.name))

    return args


def get_repo(mod_path):
    if mod_path.name in repo_map:
        return repo_map[mod_path]
    repo = git.Repo(str(mod_path), search_parent_directories=True)
    repo_map[mod_path] = repo
    return repo


def checkout(repo, ref):
    repo_dir = Path(repo.working_tree_dir)
    invalidate_repo_cache(repo_dir)

    prev_head = repo.head.commit if repo.head.is_detached else repo.head.ref
    repo.head.ref = ref
    repo.head.reset(working_tree=True)

    print('{}: checked out {}'.format(repo_dir.name,
        ref.hexsha[:8] if isinstance(ref, git.Commit) else ref.name),
        file=sys.stderr)
    return prev_head


def get_checkpoint_commit_from_file(mod_path):
    mod_path = mod_path.resolve()
    repo = get_repo(mod_path)
    repo_dir = Path(repo.working_tree_dir)

    cp_dir = mod_path
    while cp_dir != repo_dir.parent:
        if (cp_dir / cp_filename).exists():
            break
        cp_dir = cp_dir.parent
    else:
        raise RuntimeError('{} not found for {}'.format(cp_filename, mod_path))

    cp_contents = (cp_dir / cp_filename).read_text()
    commit_str = cp_contents.partition('#')[0].strip()

    commit = repo.commit(commit_str)

    return commit.hexsha[:8]


def compare_digests(old, new):
    report = {k: v for k, v in ((k, old_v - new.get(k, set()))
                                for k, old_v in old.items()) if v}
    return report


def create_digest_SWMH():
    digest = {'version': {1}}
    titles = set()
    for _, tree in parser.parse_files('common/landed_titles/*.txt'):
        dfs = list(tree)
        while dfs:
            n, v = dfs.pop()
            if is_codename(n.val):
                titles.add(n.val)
                dfs.extend(v)
    digest['landed_titles'] = titles
    return digest


def create_digest(mod_path):
    mod_path = mod_path.resolve()
    parser.moddirs = [mod_path]
    if mod_path.name == 'SWMH':
        digest = create_digest_SWMH()
    else:
        raise ValueError("don't know how to digest {}".format(mod_path.name))

    return digest


def record_digest(mod_path, commit=None, new=False):
    repo = get_repo(mod_path)
    if repo.is_dirty(untracked_files=True, path=str(mod_path)):
        raise RuntimeError('repo is dirty at {}'.format(mod_path))

    if commit:
        commit = repo.commit(commit)
    else:
        commit = repo.head.commit

    digest_path = digest_dir / mod_path.name / commit.hexsha[:8]
    if not new and digest_path.exists():
        with digest_path.open('rb') as f:
            digest = pickle.load(f)
        return digest

    must_checkout = repo.head.commit != commit
    try:
        if must_checkout:
            prev_head = checkout(repo, commit)

        digest = create_digest(mod_path)
    finally:
        if must_checkout:
            checkout(repo, prev_head)

    digest_path.parent.mkdir(parents=True, exist_ok=True)
    with digest_path.open('wb') as f:
        pickle.dump(digest, f)

    return digest


def check_compat(mod_path, checkpoint_commit=None):
    digest = record_digest(mod_path)
    if checkpoint_commit is None:
        checkpoint_commit = get_checkpoint_commit_from_file(mod_path)

    old_digest = record_digest(mod_path, checkpoint_commit)

    if old_digest['version'] != digest['version']:
        old_digest = record_digest(mod_path, checkpoint_commit, new=True)

    compat_report = compare_digests(old_digest, digest)
    return compat_report


def invalidate_repo_cache(bad_path=None):
    parser.invalidate_repo_cache(bad_path)


@print_time
def main():
    args = parse_arguments()
    for mod_path in args.mod:
        compat_report = check_compat(mod_path)
        if len(compat_report) == 0:
            print('compatible')
        else:
            print('incompatible:')
            print(sorted(compat_report.items()))


if __name__ == '__main__':
    main()