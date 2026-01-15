from __future__ import annotations

import io
import os
import textwrap
from os import PathLike
from pathlib import Path
from typing import cast

import pygit2
import pygit2.enums
import pytest

from hed.cli import app

CHANGELOG = """\
# Changelog

## 1.0.1 - 2026-01-10

### Bug fixes

- Fixed a thing! ([#2](https://github.com/owner/repo/pull/2))

## 1.0.0 - 2026-01-9

### Breaking changes

- Removed a deprecated feature. ([#1](https://github.com/owner/repo/pull/1))
"""


CHANGELOG_LINK_TITLE = """\
# Changelog

## [1.0.1](https://github.com/owner/repo/releases/tag/1.0.1) - 2026-01-10

### Bug fixes

- Fixed a thing! ([#2](https://github.com/owner/repo/pull/2))

## [1.0.0](https://github.com/owner/repo/releases/tag/1.0.0) - 2026-01-9

### Breaking changes

- Removed a deprecated feature. ([#1](https://github.com/owner/repo/pull/1))
"""

CHANGELOG_RELEASE_H3 = """\
# Changelog

## Releases

### 1.0.1 - 2026-01-10

#### Bug fixes

- Fixed a thing! ([#2](https://github.com/owner/repo/pull/2))

### 1.0.0 - 2026-01-9

#### Breaking changes

- Removed a deprecated feature. ([#1](https://github.com/owner/repo/pull/1))
"""


class FileFactory:
    """Create `file` and all its parents directories."""

    def __call__(  # noqa: D102
        self,
        file: str | PathLike[str],
        content: str | bytes | None = None,
    ) -> Path:
        file = Path(file)
        file.parent.mkdir(parents=True, exist_ok=True)

        if content is not None:
            mode = "wt" if isinstance(content, str) else "wb"
            with file.open(mode) as f:
                f.write(content)

        with file.open("a"):
            os.utime(file, times=None)

        return file


@pytest.fixture
def file_factory() -> FileFactory:
    """Fixture for creating files."""
    return FileFactory()


@pytest.fixture
def repo(tmp_path: Path) -> pygit2.Repository:
    """Create an empty git repository in `tmp_path`."""
    return pygit2.init_repository(tmp_path)


@pytest.fixture
def signature() -> pygit2.Signature:
    """Shared git author signature."""
    return pygit2.Signature("John Doe", "john@doe.com")


@pytest.fixture(autouse=True)
def chdir_to_tmp_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Automatically change current directory to `tmp_path`."""
    monkeypatch.chdir(tmp_path)


def initial_commit(
    repo: pygit2.Repository,
    signature: pygit2.Signature,
    file: Path,
) -> pygit2.Oid:
    """Write the initial commit in the form of a README.md file."""
    assert repo.is_empty
    index = cast("pygit2.Index", repo.index)
    root = Path(repo.path).parent

    index.add(file.absolute().relative_to(root))
    index.write()
    tree = index.write_tree()

    return repo.create_commit(
        "HEAD",
        signature,
        signature,
        "Initial Commit",
        tree,
        [],
    )


def commit_file(
    repo: pygit2.Repository,
    file: Path,
    signature: pygit2.Signature,
    message: str,
) -> pygit2.Oid:
    """Commit file at 'HEAD'."""
    index = cast("pygit2.Index", repo.index)
    root = Path(repo.path).parent

    index.add(file.absolute().relative_to(root))
    index.write()
    tree = index.write_tree()

    ref = repo.head.name
    parents = [repo.head.target]

    return repo.create_commit(ref, signature, signature, message, tree, parents)


def test_extract(file_factory: FileFactory, capsys: pytest.CaptureFixture[str]) -> None:
    file_factory("CHANGELOG.md", CHANGELOG)

    app(["--tag", "1.0.1"], result_action="return_value")

    assert capsys.readouterr().out == textwrap.dedent("""\
    # 1.0.1 - 2026-01-10

    ## Bug fixes

    - Fixed a thing! ([#2](https://github.com/owner/repo/pull/2))

    """)


def test_change_title(
    file_factory: FileFactory,
    capsys: pytest.CaptureFixture[str],
) -> None:
    file_factory("CHANGELOG.md", CHANGELOG)

    app(
        ["--tag", "1.0.1", "--title", "{tag}"],
        result_action="return_value",
    )

    assert capsys.readouterr().out == textwrap.dedent("""\
    # 1.0.1

    ## Bug fixes

    - Fixed a thing! ([#2](https://github.com/owner/repo/pull/2))

    """)


def test_error_empty_title(
    file_factory: FileFactory,
    capsys: pytest.CaptureFixture[str],
) -> None:
    file_factory("CHANGELOG.md", CHANGELOG)

    with pytest.raises(SystemExit) as exc_info:
        app(
            ["--tag", "1.0.1", "--title", ""],
            result_action="return_value",
        )

    assert exc_info.value.code == 1
    assert capsys.readouterr().err == textwrap.dedent("""\
    error: Failed to change title
    caused by: ValueError: Empty title
    """)


@pytest.mark.parametrize(
    "args",
    [
        pytest.param(("-",), id="positional-stdin"),
        pytest.param(("TEST.md",), id="positional-file"),
        pytest.param(("--changelog", "-"), id="keyword-stdin"),
        pytest.param(("--changelog", "TEST.md"), id="keyword-file"),
    ],
)
def test_changelog_param(
    args: tuple[str, ...],
    monkeypatch: pytest.MonkeyPatch,
    file_factory: FileFactory,
    capsys: pytest.CaptureFixture[str],
) -> None:
    if "-" in args:
        wrapper = io.TextIOWrapper(io.BytesIO(), encoding="utf-8")
        wrapper.write(CHANGELOG)
        wrapper.seek(0, 0)
        monkeypatch.setattr("sys.stdin", wrapper)
    else:
        file_factory("TEST.md", CHANGELOG)

    app(["--tag", "1.0.1", *args], result_action="return_value")

    assert capsys.readouterr().out == textwrap.dedent("""\
    # 1.0.1 - 2026-01-10

    ## Bug fixes

    - Fixed a thing! ([#2](https://github.com/owner/repo/pull/2))

    """)


def test_diff_url_and_previous_tag(
    file_factory: FileFactory,
    capsys: pytest.CaptureFixture[str],
) -> None:
    file_factory("CHANGELOG.md", CHANGELOG)

    app(
        [
            "--tag",
            "1.0.1",
            "--previous-tag",
            "1.0.0",
            "--diff-url",
            "https://github.com/owner/repo/compare/{prev}...{tag}",
        ],
        result_action="return_value",
    )

    assert capsys.readouterr().out == textwrap.dedent("""\
    # 1.0.1 - 2026-01-10

    ## Bug fixes

    - Fixed a thing! ([#2](https://github.com/owner/repo/pull/2))

    **Full Changelog:** [1.0.0...1.0.1](https://github.com/owner/repo/compare/1.0.0...1.0.1)

    """)


def test_error_failed_to_format_diff_url(
    file_factory: FileFactory,
    capsys: pytest.CaptureFixture[str],
) -> None:
    file_factory("CHANGELOG.md", CHANGELOG)

    with pytest.raises(SystemExit) as exc_info:
        app(
            ["--tag", "1.0.1", "--previous-tag", "1.0.0", "--diff-url", "https://{}"],
            result_action="return_value",
        )

    assert exc_info.value.code == 1
    assert capsys.readouterr().err == textwrap.dedent("""\
    error: Failed to format string: 'https://{}'
    caused by: IndexError: Replacement index 0 out of range for positional args tuple
    """)


def test_change_working_directory(
    file_factory: FileFactory,
    capsys: pytest.CaptureFixture[str],
) -> None:
    file_factory("subdir/CHANGELOG.md", CHANGELOG)

    app(
        ["--tag", "1.0.1", "--directory", "subdir"],
        result_action="return_value",
    )

    assert capsys.readouterr().out == textwrap.dedent("""\
    # 1.0.1 - 2026-01-10

    ## Bug fixes

    - Fixed a thing! ([#2](https://github.com/owner/repo/pull/2))

    """)


@pytest.mark.parametrize(
    "changelog",
    [
        pytest.param(CHANGELOG, id="plain-title"),
        pytest.param(CHANGELOG_LINK_TITLE, id="link-title"),
    ],
)
def test_default_capture_start(
    changelog: str,
    file_factory: FileFactory,
    capsys: pytest.CaptureFixture[str],
) -> None:
    file_factory("CHANGELOG.md", changelog)

    app(["--tag", "1.0.1", "--title", "{tag}"], result_action="return_value")

    assert capsys.readouterr().out == textwrap.dedent("""\
    # 1.0.1

    ## Bug fixes

    - Fixed a thing! ([#2](https://github.com/owner/repo/pull/2))

    """)


def test_extract_capture_start_end(
    file_factory: FileFactory,
    capsys: pytest.CaptureFixture[str],
) -> None:
    file_factory("CHANGELOG.md", CHANGELOG_RELEASE_H3)

    app(
        ["--tag", "1.0.1", "--capture-start", r"### {tag}", "--capture-end", "### "],
        result_action="return_value",
    )

    assert capsys.readouterr().out == textwrap.dedent("""\
    # 1.0.1 - 2026-01-10

    ## Bug fixes

    - Fixed a thing! ([#2](https://github.com/owner/repo/pull/2))

    """)


def test_extract_capture_eof(
    file_factory: FileFactory,
    capsys: pytest.CaptureFixture[str],
) -> None:
    file_factory("CHANGELOG.md", CHANGELOG)

    app(
        ["--tag", "1.0.0"],
        result_action="return_value",
    )

    assert capsys.readouterr().out == textwrap.dedent("""\
    # 1.0.0 - 2026-01-9

    ## Breaking changes

    - Removed a deprecated feature. ([#1](https://github.com/owner/repo/pull/1))

    """)


def test_error_no_match_for_tag(
    file_factory: FileFactory,
    capsys: pytest.CaptureFixture[str],
) -> None:
    file_factory("CHANGELOG.md", CHANGELOG)

    with pytest.raises(SystemExit) as exc_info:
        app(["--tag", "2.0.0"], result_action="return_value")

    assert exc_info.value.code == 1
    assert capsys.readouterr().err == textwrap.dedent("""\
    error: No match for tag '2.0.0'
    caused by: hed.operations.PatternNotFoundError: '^## ([2\\.0\\.0\\]|2\\.0\\.0)'
    """)


@pytest.mark.parametrize("filename", ["pyproject.toml", "hed.toml"])
def test_read_default_config_file(
    filename: str,
    file_factory: FileFactory,
    capsys: pytest.CaptureFixture[str],
) -> None:
    file_factory("FOO.md", CHANGELOG_RELEASE_H3)
    file_factory(
        filename,
        textwrap.dedent("""\
        [tool.hed]
        capture-start = '^### {tag}'
        capture-end = '^### '
        changelog = "FOO.md"
        diff-url = "https://github.com/owner/repo/compare/{prev}...{tag}"
        title = "Test"
        """),
    )

    app(["--tag", "1.0.1", "--previous-tag", "1.0.0"], result_action="return_value")

    assert capsys.readouterr().out == textwrap.dedent("""\
    # Test

    ## Bug fixes

    - Fixed a thing! ([#2](https://github.com/owner/repo/pull/2))

    **Full Changelog:** [1.0.0...1.0.1](https://github.com/owner/repo/compare/1.0.0...1.0.1)

    """)


def test_read_config_file_option(
    file_factory: FileFactory,
    capsys: pytest.CaptureFixture[str],
) -> None:
    file_factory("CHANGELOG.md", CHANGELOG)
    file_factory(
        "test.toml",
        textwrap.dedent("""\
        [tool.hed]
        title = "Test"
        """),
    )

    app(["--config-file", "test.toml", "--tag", "1.0.1"], result_action="return_value")

    assert capsys.readouterr().out == textwrap.dedent("""\
    # Test

    ## Bug fixes

    - Fixed a thing! ([#2](https://github.com/owner/repo/pull/2))

    """)


def test_prefer_hed_toml(
    file_factory: FileFactory,
    capsys: pytest.CaptureFixture[str],
) -> None:
    file_factory("CHANGELOG.md", CHANGELOG)
    file_factory(
        "hed.toml",
        textwrap.dedent("""\
        [tool.hed]
        title = "Test"
        """),
    )
    file_factory(
        "pyproject.toml",
        textwrap.dedent("""\
        [tool.hed]
        title = "Invalid"
        """),
    )

    app(["--tag", "1.0.1"], result_action="return_value")

    assert capsys.readouterr().out == textwrap.dedent("""\
    # Test

    ## Bug fixes

    - Fixed a thing! ([#2](https://github.com/owner/repo/pull/2))

    """)


def test_tag_from_head(
    repo: pygit2.Repository,
    signature: pygit2.Signature,
    file_factory: FileFactory,
    capsys: pytest.CaptureFixture[str],
) -> None:
    commit = initial_commit(
        repo,
        signature,
        file_factory("CHANGELOG.md", CHANGELOG),
    )
    repo.create_tag("1.0.1", commit, pygit2.enums.ObjectType.COMMIT, signature, "")

    app([], result_action="return_value")

    assert capsys.readouterr().out == textwrap.dedent("""\
    # 1.0.1 - 2026-01-10

    ## Bug fixes

    - Fixed a thing! ([#2](https://github.com/owner/repo/pull/2))

    """)


def test_find_previous_tag(
    repo: pygit2.Repository,
    signature: pygit2.Signature,
    file_factory: FileFactory,
    capsys: pytest.CaptureFixture[str],
) -> None:
    commit = initial_commit(
        repo,
        signature,
        file_factory("README.md", "# Test Project"),
    )
    repo.create_tag("1.0.0", commit, pygit2.enums.ObjectType.COMMIT, signature, "")

    changelog = file_factory("CHANGELOG.md", CHANGELOG)
    commit = commit_file(repo, changelog, signature, "Add CHANGELOG.md")
    repo.create_tag("1.0.1", commit, pygit2.enums.ObjectType.COMMIT, signature, "")

    app(
        ["--diff-url", "https://github.com/owner/repo/compare/{prev}...{tag}"],
        result_action="return_value",
    )

    assert capsys.readouterr().out == textwrap.dedent("""\
    # 1.0.1 - 2026-01-10

    ## Bug fixes

    - Fixed a thing! ([#2](https://github.com/owner/repo/pull/2))

    **Full Changelog:** [1.0.0...1.0.1](https://github.com/owner/repo/compare/1.0.0...1.0.1)

    """)


def test_warning_failed_to_find_previous_tag(
    repo: pygit2.Repository,
    signature: pygit2.Signature,
    file_factory: FileFactory,
    capsys: pytest.CaptureFixture[str],
) -> None:
    initial_commit(repo, signature, file_factory("CHANGELOG.md", CHANGELOG))

    app(
        [
            "--tag",
            "1.0.1",
            "--diff-url",
            "https://github.com/owner/repo/compare/{prev}...{tag}",
        ],
        result_action="return_value",
    )

    assert capsys.readouterr().err == textwrap.dedent("""\
    warning: Failed to find previous tag of '1.0.1'
    caused by: hed.git.TagNotFoundError: 1.0.1
    caused by: KeyError: 'refs/tags/1.0.1'
    """)


def test_warning_no_previous_tag(
    repo: pygit2.Repository,
    signature: pygit2.Signature,
    file_factory: FileFactory,
    capsys: pytest.CaptureFixture[str],
) -> None:
    commit = initial_commit(repo, signature, file_factory("CHANGELOG.md", CHANGELOG))
    repo.create_tag("1.0.0", commit, pygit2.enums.ObjectType.COMMIT, signature, "")

    app(
        [
            "--tag",
            "1.0.0",
            "--diff-url",
            "https://github.com/owner/repo/compare/{prev}...{tag}",
        ],
        result_action="return_value",
    )

    assert capsys.readouterr().err == textwrap.dedent("""\
    warning: No previous tag for '1.0.0'
    """)


def test_error_head_tag_not_found(
    repo: pygit2.Repository,
    signature: pygit2.Signature,
    file_factory: FileFactory,
    capsys: pytest.CaptureFixture[str],
) -> None:
    initial_commit(repo, signature, file_factory("CHANGELOG.md", CHANGELOG))

    with pytest.raises(SystemExit) as exc_info:
        app([], result_action="return_value")

    assert exc_info.value.code == 1
    assert capsys.readouterr().err == textwrap.dedent("""\
    error: No tag was provided and not tag is attached to 'HEAD'
    """)


def test_error_head_have_more_than_one_tag(
    repo: pygit2.Repository,
    signature: pygit2.Signature,
    file_factory: FileFactory,
    capsys: pytest.CaptureFixture[str],
) -> None:
    commit = initial_commit(repo, signature, file_factory("CHANGELOG.md", CHANGELOG))
    repo.create_tag("1.0.0", commit, pygit2.enums.ObjectType.COMMIT, signature, "")
    repo.create_tag("1.0.1", commit, pygit2.enums.ObjectType.COMMIT, signature, "")

    with pytest.raises(SystemExit) as exc_info:
        app([], result_action="return_value")

    assert exc_info.value.code == 1
    assert capsys.readouterr().err == textwrap.dedent("""\
    error: No tag was provided and 'HEAD' have more than one tag: 1.0.0, 1.0.1
    """)
