from __future__ import annotations

import sys
import traceback
from functools import cache, partial
from typing import TYPE_CHECKING, NoReturn

from rich.console import Console

if TYPE_CHECKING:
    from collections.abc import Iterable


@cache
def stdout_console() -> Console:
    """Return the global stdout `Console`.

    Do **not** modify the console properties.
    """
    return Console(stderr=False, highlight=False, soft_wrap=True)


@cache
def stderr_console() -> Console:
    """Return the global stderr `Console`.

    Do **not** modify the console properties.
    """
    return Console(stderr=True, highlight=False)


def abort(msg: str, *, exc: BaseException | None = None, code: int = 1) -> NoReturn:
    """Print error `msg` to stderr and exit with `code`."""
    assert code != 0, "expected non-zero exit code"
    print_err(msg, exc=exc, warning=False)
    sys.exit(code)


def print_err(
    msg: str,
    *,
    exc: BaseException | None = None,
    warning: bool = False,
    console: Console | None = None,
) -> None:
    """Print context `msg`, followed by `exc`, and its causes, to `console`."""
    console = console or stderr_console()
    print_ = partial(console.print, highlight=False, soft_wrap=True)

    def title(text: str) -> str:
        color = "yellow" if warning else "red"
        return f"[bold {color}]{text}:[/bold {color}]"

    print_(f"{title('warning' if warning else 'error')} {msg}")

    if not exc:
        return

    for exc_ in chain_errors(exc):
        errmsg = traceback.format_exception_only(type(exc_), exc_)[0].strip()
        print_(f"{title('caused by')} {errmsg}")


def chain_errors(exc: BaseException) -> Iterable[BaseException]:
    """Iter exception causes, including `exc`."""
    exc_: BaseException | None = exc
    while exc_ is not None:
        yield exc_
        exc_ = exc_.__cause__
