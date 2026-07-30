from html import unescape
from html.parser import HTMLParser
import re

import bleach
from bleach.css_sanitizer import CSSSanitizer


ALLOWED_TAGS = {
    "a", "blockquote", "br", "code", "em", "h1", "h2", "h3", "h4",
    "h5", "h6", "hr", "img", "li", "ol", "p", "pre", "s", "span",
    "strong", "table", "tbody", "td", "th", "thead", "tr", "u", "ul", "col", "colgroup",
}
STYLE_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6", "p", "span", "table", "col"}


def _allow_attribute(tag: str, name: str, value: str) -> bool:
    normalized_value = str(value or "").strip().lower()
    if tag in {"th", "td"} and name in {"colspan", "rowspan"}:
        return normalized_value.isdigit() and int(normalized_value) > 0
    if tag == "table" and name == "data-table-width":
        return normalized_value == "auto" or (
            normalized_value.isdigit() and 25 <= int(normalized_value) <= 100
        )
    if tag in {"th", "td"} and name == "data-vertical-align":
        return normalized_value in {"top", "middle", "bottom"}
    if name == "style":
        return tag in STYLE_TAGS
    if tag == "a":
        if name == "href":
            return normalized_value.startswith(("http://", "https://", "mailto:"))
        if name == "target":
            return normalized_value == "_blank"
        if name == "rel":
            return set(normalized_value.split()).issubset({"noopener", "noreferrer"})
    if tag == "img":
        if name == "src":
            return normalized_value.startswith(("http://", "https://"))
        return name in {"alt", "title"}
    return False
CSS_SANITIZER = CSSSanitizer(
    allowed_css_properties=["background-color", "color", "font-size", "text-align", "width", "min-width"]
)
CLEANER = bleach.Cleaner(
    tags=ALLOWED_TAGS,
    attributes=_allow_attribute,
    protocols={"http", "https", "mailto"},
    css_sanitizer=CSS_SANITIZER,
    strip=True,
    strip_comments=True,
)


class _DangerousBlockRemover(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.output: list[str] = []
        self.blocked_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag.lower() in {"script", "style"}:
            self.blocked_depth += 1
        elif not self.blocked_depth:
            attributes = "".join(
                f' {name}="{value or ""}"' for name, value in attrs
            )
            self.output.append(f"<{tag}{attributes}>")

    def handle_startendtag(self, tag, attrs):
        if tag.lower() not in {"script", "style"} and not self.blocked_depth:
            attributes = "".join(
                f' {name}="{value or ""}"' for name, value in attrs
            )
            self.output.append(f"<{tag}{attributes}>")

    def handle_endtag(self, tag):
        if tag.lower() in {"script", "style"}:
            self.blocked_depth = max(0, self.blocked_depth - 1)
        elif not self.blocked_depth:
            self.output.append(f"</{tag}>")

    def handle_data(self, data):
        if not self.blocked_depth:
            self.output.append(data)

    def handle_entityref(self, name):
        if not self.blocked_depth:
            self.output.append(f"&{name};")

    def handle_charref(self, name):
        if not self.blocked_depth:
            self.output.append(f"&#{name};")


class _VisibleContentParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text: list[str] = []
        self.has_image = False

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "img" and dict(attrs).get("src"):
            self.has_image = True

    def handle_data(self, data):
        self.text.append(data)


def sanitize_faq_content(content: str) -> str:
    remover = _DangerousBlockRemover()
    remover.feed(str(content or ""))
    cleaned = CLEANER.clean("".join(remover.output)).strip()

    def filter_style(match):
        tag, before, style, after = match.groups()
        allowed = {"width", "min-width"} if tag in {"table", "col"} else {
            "background-color", "color", "font-size", "text-align"
        }
        declarations = []
        for declaration in style.split(";"):
            if ":" not in declaration:
                continue
            name, value = (part.strip() for part in declaration.split(":", 1))
            if name not in allowed:
                continue
            if name in {"width", "min-width"}:
                is_pixel_width = bool(re.fullmatch(r"[1-9]\d*px", value))
                is_table_percentage = (
                    tag == "table"
                    and name == "width"
                    and bool(re.fullmatch(r"\d+%", value))
                    and 25 <= int(value[:-1]) <= 100
                )
                if not is_pixel_width and not is_table_percentage:
                    continue
            declarations.append(f"{name}: {value};")
        style_attribute = f' style="{" ".join(declarations)}"' if declarations else ""
        return f"<{tag}{before}{style_attribute}{after}>"

    return re.sub(
        r'<([a-z0-9]+)([^>]*) style="([^"]*)"([^>]*)>',
        filter_style,
        cleaned,
        flags=re.IGNORECASE,
    )


def is_faq_content_empty(content: str) -> bool:
    parser = _VisibleContentParser()
    parser.feed(str(content or ""))
    visible_text = unescape("".join(parser.text)).replace("\xa0", "").strip()
    return not visible_text and not parser.has_image
