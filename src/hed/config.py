from __future__ import annotations

from typing import TYPE_CHECKING, cast

import attrs
import cyclopts
from cyclopts import default_name_transform
from cyclopts.utils import to_tuple_converter
from typing_extensions import override

if TYPE_CHECKING:
    from collections.abc import Iterable


@attrs.define
class TomlConfig(cyclopts.config.Toml):
    """Exclude arguments from cyclopts `Toml` config."""

    include: Iterable[str] = attrs.field(default=(), converter=to_tuple_converter)

    @override
    def __call__(
        self,
        app: cyclopts.App,
        commands: tuple[str, ...],
        arguments: cyclopts.ArgumentCollection,
    ) -> None:
        default = object()
        args = cyclopts.ArgumentCollection()

        for arg_name in self.include:
            arg = arguments.get(
                arg_name,
                default=default,
                transform=default_name_transform,
            )
            if arg is not default:
                args.append(cast("cyclopts.Argument", arg))

        super().__call__(app, commands, args)
