"""GENERATED from style/brand.json by style/generate_style.py -- do not edit by hand.

Pygments styles carrying the Kataglyphis code palette, so code blocks on
the docs website match the book and the slides. Registered as the
"kataglyphis-light" / "kataglyphis-dark" Pygments styles via entry points.
"""

from pygments.style import Style
from pygments.token import (
    Comment,
    Error,
    Generic,
    Keyword,
    Name,
    Number,
    Operator,
    String,
    Text,
)


class KataglyphisLightStyle(Style):
    """Kataglyphis kataglyphis-light code highlighting."""

    name = "kataglyphis-light"
    background_color = "#f6f8fa"
    highlight_color = "#ffebee"
    line_number_color = "#6a737d"
    line_number_background_color = "#ffffff"

    styles = {
        Text: "#111111",
        Comment: "italic #6a737d",
        Comment.Preproc: "#e36209",
        Comment.Special: "bold italic #6a737d",
        Keyword: "bold #d73a49",
        Keyword.Constant: "#005cc5",
        Keyword.Type: "#6f42c1",
        Operator: "#d73a49",
        Operator.Word: "bold #d73a49",
        Name.Builtin: "#005cc5",
        Name.Function: "#6f42c1",
        Name.Class: "#6f42c1",
        Name.Decorator: "#e36209",
        Name.Exception: "#b31d28",
        Name.Attribute: "#22863a",
        Name.Tag: "#d73a49",
        Name.Variable: "#111111",
        Name.Constant: "#005cc5",
        String: "#032f62",
        String.Escape: "#005cc5",
        Number: "#005cc5",
        Number.Float: "#005cc5",
        Generic.Deleted: "#b31d28",
        Generic.Inserted: "#22863a",
        Generic.Emph: "italic #111111",
        Generic.Strong: "bold #111111",
        Generic.Heading: "bold #6f42c1",
        Error: "bold #b31d28",
    }


class KataglyphisDarkStyle(Style):
    """Kataglyphis kataglyphis-dark code highlighting."""

    name = "kataglyphis-dark"
    background_color = "#0d1117"
    highlight_color = "#2d0b0f"
    line_number_color = "#8b949e"
    line_number_background_color = "#161b22"

    styles = {
        Text: "#c9d1d9",
        Comment: "italic #8b949e",
        Comment.Preproc: "#ffa657",
        Comment.Special: "bold italic #8b949e",
        Keyword: "bold #ff7b72",
        Keyword.Constant: "#79c0ff",
        Keyword.Type: "#ffa657",
        Operator: "#ff7b72",
        Operator.Word: "bold #ff7b72",
        Name.Builtin: "#79c0ff",
        Name.Function: "#d2a8ff",
        Name.Class: "#ffa657",
        Name.Decorator: "#ffa657",
        Name.Exception: "#ff7b72",
        Name.Attribute: "#7ee787",
        Name.Tag: "#ff7b72",
        Name.Variable: "#c9d1d9",
        Name.Constant: "#79c0ff",
        String: "#a5d6ff",
        String.Escape: "#79c0ff",
        Number: "#79c0ff",
        Number.Float: "#ae81ff",
        Generic.Deleted: "#ff7b72",
        Generic.Inserted: "#7ee787",
        Generic.Emph: "italic #c9d1d9",
        Generic.Strong: "bold #c9d1d9",
        Generic.Heading: "bold #d2a8ff",
        Error: "bold #ff7b72",
    }
