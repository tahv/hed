from __future__ import annotations

from itertools import dropwhile, takewhile
from typing import TYPE_CHECKING, TextIO, TypeGuard

from mistletoe.block_token import BlockToken, Heading
from mistletoe.span_token import LineBreak, RawText

if TYPE_CHECKING:
    import re
    from collections.abc import Iterable

    from mistletoe.token import Token


class PatternNotFoundError(Exception):
    """Raised when the entire file was parsed but the pattern was never matched."""

    def __init__(self, pattern: re.Pattern[str]) -> None:
        self.pattern = pattern
        super().__init__(f"'{self.pattern.pattern}'")


def extract_release(
    io: TextIO,
    start_pattern: re.Pattern[str],
    end_pattern: re.Pattern[str],
) -> Iterable[str]:
    """Iter `io` lines and extract text between `start_pattern` and `end_pattern` lines.

    The `start_pattern` line is included but `end_pattern` line is not.

    Raises:
        PatternNotFoundError: The `start_pattern` was not found.
            Occurs before the iteration begin.
    """
    capture = dropwhile(lambda x: not start_pattern.match(x), io)
    try:
        yield next(capture)
    except StopIteration:
        raise PatternNotFoundError(start_pattern) from None
    yield from takewhile(lambda x: not end_pattern.match(x), capture)


def normalize_headings(token: BlockToken) -> None:
    """Normalize headings in `token` tree to start at h1."""
    headings: list[Heading] = [
        t for t in iter_token_tree(token) if isinstance(t, Heading)
    ]
    offset = min((h.level for h in headings), default=1) - 1
    for h in headings:
        h.level -= offset


def update_title(token: BlockToken, title: str) -> None:
    """Find the h1 in `token` tree and change its text to `title`."""
    if not title:
        msg = "Empty title"
        raise ValueError(msg)

    if len(title.splitlines()) > 1:
        msg = "Title must fit on one line"
        raise ValueError(msg)

    def is_h1(token: Token) -> TypeGuard[Heading]:
        return isinstance(token, Heading) and token.level == 1

    headings = list[Heading](filter(is_h1, iter_token_tree(token)))

    if len(headings) != 1:
        msg = f"Expected exactly one h1 heading, found {len(headings)}"
        raise RuntimeError(msg)

    heading = headings[0]
    heading.children = (RawText(title),)


def iter_token_tree(token: Token) -> Iterable[Token]:
    """Iter `token` children recursively."""
    yield token
    for child in token.children or []:
        yield from iter_token_tree(child)


def remove_softbreaks(token: BlockToken) -> None:
    """Remove soft `LineBreak` from `token` hierarchy.

    See: https://github.com/orgs/community/discussions/10981
    """

    def is_softbreak(token: Token) -> TypeGuard[LineBreak]:
        return isinstance(token, LineBreak) and token.soft

    for token_ in iter_token_tree(token):
        if token_.children:
            token_.children = tuple(
                t if not is_softbreak(t) else RawText(" ") for t in token_.children
            )
