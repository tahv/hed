from __future__ import annotations

from typing import cast

from marko import MarkoExtension, block
from marko.ext.gfm import elements as gfm_elements
from marko.ext.gfm.renderer import GFMRendererMixin
from marko.helpers import render_dispatch
from marko.md_renderer import MarkdownRenderer


class _HedRenderMixin(GFMRendererMixin):
    @render_dispatch(MarkdownRenderer)  # type: ignore[arg-type]
    def render_list_item(self: MarkdownRenderer, element: block.ListItem) -> str:
        """Add support for indented elements.

        CommonMark [list items](https://spec.commonmark.org/0.31.2/#list-items)
        state that a "A list item may contain any kind of block".

        In practice this is achieved by indenting the element four spaces or one tab.
        See [Adding Elements in Lists](https://www.markdownguide.org/basic-syntax/#adding-elements-in-lists).

        ```markdown
        * This is the first list item.

            I need to add another paragraph below the second list item.
        * Here's the second list item.

            | foo | bar |
            | foo | bar |
        * And here's the third list item.
        ```
        """
        # TODO(tga): GitLab expect a newline after a table if followed by a list item
        with self.container(prefix="", second_prefix="  "):
            return cast("str", self.render_children(element))

    @render_dispatch(MarkdownRenderer)  # type: ignore[arg-type]
    def render_table(self: MarkdownRenderer, element: gfm_elements.Table) -> str:
        """Prefix table lines with `self._prefix`."""
        lines = []
        head, *body = element.children
        lines.append(self._prefix + self.render(head))
        lines.append(self._prefix + f"| {' | '.join(element.delimiters)} |\n")
        lines.extend(self._prefix + self.render(row) for row in body)
        return "".join(lines)

    @render_dispatch(MarkdownRenderer)  # type: ignore[arg-type]
    def render_blank_line(self: MarkdownRenderer, _: block.BlankLine) -> str:
        self._prefix = self._second_prefix
        return "\n"


GithubTableExtension = MarkoExtension(
    elements=[
        gfm_elements.Table,
        gfm_elements.TableRow,
        gfm_elements.TableCell,
    ],
    renderer_mixins=[_HedRenderMixin],
)
