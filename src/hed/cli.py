from __future__ import annotations

import os
import re
import sys
import traceback
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, NoReturn, cast

import cyclopts
import marko
from cyclopts import validators
from cyclopts.help import DefaultFormatter, PanelSpec
from cyclopts.types import StdioPath
from marko import Markdown
from marko.md_renderer import MarkdownRenderer
from rich import get_console
from rich.box import MINIMAL

from hed.config import TomlConfig
from hed.git import (
    TagNotFoundError,
    find_previous_tag,
    get_current_commit,
    get_tags_for_commit,
    repo_from_path,
)
from hed.operations import (
    PatternNotFoundError,
    change_title,
    extract_release,
    normalize_headings,
)

if TYPE_CHECKING:
    from marko.element import Element


_app = cyclopts.App(
    help_formatter=DefaultFormatter(
        panel_spec=PanelSpec(box=MINIMAL),
    ),
)
_app.meta.group_parameters = cyclopts.Group("Global options", sort_key=0)
app = _app.meta


def _path_converter(type_: type[Path], tokens: list[cyclopts.Token]) -> Path:
    assert len(tokens) == 1, "expected 1 token"
    return type_(tokens[0].value).expanduser()


def _get_config_file(directory: Path) -> Path:
    default = "pyproject.toml"

    for filename in ("hed.toml", default):
        config_path = directory / filename
        if config_path.exists():
            return config_path

    return directory / default


@_app.meta.default
def _meta(  # noqa: D417
    *tokens: Annotated[str, cyclopts.Parameter(show=False, allow_leading_hyphen=True)],
    directory: Annotated[
        Path,
        cyclopts.Parameter(
            converter=_path_converter,
            validator=validators.Path(exists=True, file_okay=False, dir_okay=True),
            show_default=lambda p: f"'{p}'",
        ),
    ] = Path(),
    config_file: Annotated[
        Path | None,
        cyclopts.Parameter(
            name="--config-file",
            converter=_path_converter,
            validator=validators.Path(exists=True, file_okay=True, dir_okay=False),
        ),
    ] = None,
) -> None:
    """CLI meta command.

    Args:
        directory: Change to the given directory prior to running the command.
        config_file: The path to a `toml` file to use for configuration.
    """
    os.chdir(directory)

    if config_file is None:
        config_file = _get_config_file(directory)

    _app.config = [
        # TODO(tga): environment variables
        TomlConfig(
            path=config_file,
            root_keys=("tool", "hed"),
            include=(
                "capture-end",
                "capture-start",
                "changelog",
                "diff-url",
                "title",
            ),
            search_parents=False,
        ),
    ]

    _app(tokens)


@_app.default
def _main(  # noqa: C901, PLR0912
    changelog: Annotated[
        StdioPath,
        cyclopts.Parameter(
            name=("--changelog", "-c"),
            validator=validators.Path(exists=True, file_okay=True, dir_okay=False),
        ),
    ] = StdioPath("CHANGELOG.md"),  # noqa: B008
    *,
    tag: Annotated[
        str | None,
        cyclopts.Parameter(name=("--tag", "-t")),
    ] = None,
    capture_start: Annotated[
        str,
        cyclopts.Parameter(show_default=lambda s: f"'{s}'"),
    ] = r"^## (\[{tag}\]|{tag})",
    capture_end: Annotated[
        str,
        cyclopts.Parameter(show_default=lambda s: f"'{s}'"),
    ] = r"^## ",
    title: str | None = None,
    diff_url: str | None = None,
    previous_tag: str | None = None,
) -> None:
    """Extract release notes from markdown changelog.

    This tool is designed for changelog that follow
    "[keep a changelog](https://keepachangelog.com)"
    or "[common changelog](https://common-changelog.org)" format.

    Args:
        changelog: Path to the changelog file, or `-` for stdin.
        tag: Version to extract from the changelog file.
            If not provided, `hed` will try to find the tag
            associated to the current commit.
        capture_start: Start capture when this regex match a line in changelog.
            Accepts the `{tag}` placeholder,
            which will be replaced with the value of `--tag`.
        capture_end: End capture when this regex match a line in changelog,
            or when end-of-file is reached.
        diff_url: URL template for comparing tags.
            Must contain `{prev}` and `{tag}` placeholders,
            which will be replaced with the values of `--previous-tag` and `--tag`.
            If provided, a line will be added at the end of the markdown
            with a link for comparing revisions.
        previous_tag: Closest reachable tag from `--tag`.
            If not provided,
            `hed` will try to find the closest reachable tag from `--tag`.
        title: Override h1 title.
            Accepts the `{tag}` placeholder,
            which will be replaced with the value of `--tag`.
    """
    if tag is None:
        repo = repo_from_path(Path.cwd())
        tags = get_tags_for_commit(repo, get_current_commit(repo))
        if not tags:
            abort("No tag was provided and not tag is attached to 'HEAD'")
        elif len(tags) > 1:
            abort(
                "No tag was provided and 'HEAD' have more than one tag: "
                f"{', '.join(tags)}",
            )
        tag = tags[0]

    start_pattern = re.compile(capture_start.format(tag=re.escape(tag)))
    end_pattern = re.compile(capture_end)

    with changelog.open("rt") as f:
        try:
            text = extract_release(f, start_pattern, end_pattern)
        except PatternNotFoundError as exc:
            abort(f"No match for tag '{tag}'", exc=exc, code=1)

    markdown = Markdown(renderer=MarkdownRenderer)
    document = markdown.parse(text)

    normalize_headings(document)

    if title is not None:
        try:
            change_title(document, title.format(tag=tag))
        except AssertionError:  # pragma: no cover
            raise
        except Exception as exc:  # noqa: BLE001
            abort("Failed to change title", exc=exc, code=1)
        except:  # pragma: no cover
            raise

    if diff_url is not None and previous_tag is None:
        repo = repo_from_path(Path())
        try:
            previous_tag = find_previous_tag(repo, tag)
        except TagNotFoundError as exc:
            print_error(
                f"Failed to find previous tag of '{tag}'",
                exc=exc,
                warning=True,
            )
        else:
            if previous_tag is None:
                print_error(f"No previous tag for '{tag}'", warning=True)

    if diff_url is not None and previous_tag is not None:
        try:
            url = diff_url.format(tag=tag, prev=previous_tag)
        except LookupError as exc:
            abort(f"Failed to format string: {diff_url!r}", exc=exc)
        text = f"\n**Full Changelog:** [{previous_tag}...{tag}]({url})"
        cast("list[Element]", document.children).extend(marko.parse(text).children)

    print_stdout(markdown.render(document))


def abort(msg: str, *, exc: BaseException | None = None, code: int = 1) -> NoReturn:
    """Print error `msg` to stderr and exit with `code`."""
    assert code != 0, "expected non-zero exit code"
    print_error(msg, exc=exc, warning=False)
    sys.exit(code)


def print_error(
    msg: str,
    *,
    exc: BaseException | None = None,
    warning: bool = False,
) -> None:
    """Print `msg` and `exc` to stderr and exit with `code`."""
    title = "[bold {color}]{}:[/bold {color}]"
    color = "yellow" if warning else "red"

    print_stderr(
        f"{title.format('warning' if warning else 'error', color=color)} {msg}",
    )

    while exc is not None:
        errmsg = traceback.format_exception_only(type(exc), exc)[0].strip()
        print_stderr(f"{title.format('caused by', color=color)} {errmsg}")
        exc = exc.__cause__


def print_stdout(msg: str) -> None:
    """Print `msg` as is to stdout."""
    console = get_console()
    console.stderr = False
    console.print(msg, highlight=False, soft_wrap=True, markup=False)


def print_stderr(msg: str) -> None:
    """Print `msg` as is to stderr."""
    console = get_console()
    console.stderr = True
    console.print(msg, highlight=False, soft_wrap=True)
