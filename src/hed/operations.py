from __future__ import annotations

from itertools import dropwhile, takewhile
from typing import TYPE_CHECKING, TextIO

from marko.block import Document, Heading
from marko.inline import RawText

if TYPE_CHECKING:
    import re


class PatternNotFoundError(Exception):
    """Raised when the entire file was parsed but the pattern was never matched."""

    def __init__(self, pattern: re.Pattern[str]) -> None:
        self.pattern = pattern
        super().__init__(f"'{self.pattern.pattern}'")


def extract_release(
    io: TextIO,
    start_pattern: re.Pattern[str],
    end_pattern: re.Pattern[str],
) -> str:
    """Iter `io` lines and extract text between `start_pattern` and `end_pattern` lines.

    The `start_pattern` line is included but `end_pattern` line is not.
    """
    lines: list[str] = []
    capture = dropwhile(lambda x: not start_pattern.match(x), io)
    try:
        lines.append(next(capture))
    except StopIteration:
        raise PatternNotFoundError(start_pattern) from None
    lines.extend(takewhile(lambda x: not end_pattern.match(x), capture))
    return "".join(lines).strip()


def change_title(document: Document, title: str) -> None:
    """Update `document` h1 text to `title`."""
    if not title:
        msg = "Empty title"
        raise ValueError(msg)

    if len(title.splitlines()) > 1:
        msg = "Title must fit on one line"
        raise ValueError(msg)

    headings: list[Heading] = [
        el for el in document.children if isinstance(el, Heading) and el.level == 1
    ]

    assert headings, "expected document to have at least one main heading"

    if len(headings) > 1:
        msg = f"Expected exactly 1 main heading, got {len(headings)}"
        raise RuntimeError(msg)

    headings[0].children = [RawText(title)]


def normalize_headings(document: Document) -> None:
    """Normalize `document` headings to start a h1."""
    lowest_level = min(
        (el.level for el in document.children if isinstance(el, Heading)),
        default=1,
    )
    offset = lowest_level - 1

    for el in document.children:
        if isinstance(el, Heading):
            el.level -= offset
