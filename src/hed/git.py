from __future__ import annotations

from typing import TYPE_CHECKING

import pygit2
from pygit2.enums import ReferenceFilter

if TYPE_CHECKING:
    from pathlib import Path


class TagNotFoundError(Exception):
    """Raised when a tag is requested but does not exist in the repo."""


def repo_from_path(path: Path) -> pygit2.Repository:
    """Returns git repo at `path`."""
    return pygit2.Repository(path.absolute())


def find_previous_tag(repo: pygit2.Repository, tag_name: str) -> str | None:
    """Find the closest reachable tag before `tag_name`."""
    commits_tag: dict[pygit2.Oid, str] = {
        t.peel(pygit2.Commit).id: t.shorthand
        for t in repo.references.iterator(ReferenceFilter.TAGS)
        if t.shorthand != tag_name
    }

    walker = repo.walk(get_commit_for_tag(repo, tag_name).id)
    walker.simplify_first_parent()

    for commit in walker:
        tag = commits_tag.get(commit.id, None)
        if tag:
            return tag

    return None


def get_commit_for_tag(repo: pygit2.Repository, tag: str) -> pygit2.Commit:
    """Returns the commit attached to `tag`."""
    try:
        ref = repo.lookup_reference(f"refs/tags/{tag}")
    except KeyError as exc:
        raise TagNotFoundError(tag) from exc
    return ref.peel(pygit2.Commit)


def get_current_commit(repo: pygit2.Repository) -> pygit2.Commit:
    """Returns 'HEAD' commit."""
    obj = repo.revparse_single("HEAD")
    assert isinstance(obj, pygit2.Commit)
    return obj


def get_tags_for_commit(repo: pygit2.Repository, commit: pygit2.Commit) -> list[str]:
    """List tags on `commit`."""
    tags: list[str] = []
    for tag_ref in repo.references.iterator(ReferenceFilter.TAGS):
        tag_commit = tag_ref.peel(pygit2.Commit)
        if tag_commit.id == commit.id:
            tags.append(tag_ref.shorthand)
    return tags
