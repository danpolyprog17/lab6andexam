import bleach
import markdown as md

ALLOWED_TAGS = list(bleach.sanitizer.ALLOWED_TAGS) + [
    "p",
    "pre",
    "span",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "table",
    "thead",
    "tbody",
    "tr",
    "th",
    "td",
    "code",
    "blockquote",
    "ul",
    "ol",
    "li",
]
ALLOWED_ATTRS = {
    **bleach.sanitizer.ALLOWED_ATTRIBUTES,
    "*": ["class", "id", "style"],
    "a": ["href", "title", "name", "target", "rel"],
    "img": ["src", "alt", "title"],
}


def sanitize_markdown_text(text: str) -> str:
    if not text:
        return ""
    # Clean raw user input before storing
    return bleach.clean(text, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS, strip=True)


def render_markdown_to_html(markdown_text: str) -> str:
    if not markdown_text:
        return ""
    html = md.markdown(
        markdown_text,
        extensions=["extra", "sane_lists", "tables", "fenced_code"],
        output_format="html5",
    )
    # Double-sanitize in case the markdown produced unexpected HTML
    return bleach.clean(html, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS, strip=True)
