"""AD-18: `static/tokens.css` must mirror DESIGN.md's frontmatter tokens exactly.

Parses both files independently (no shared code with the generator) so a
drift in either one fails this test.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from harness_lab import config

# The DESIGN.md that declares the tokens; a lot's delta (lot 6 of 2026-10-04, its own
# DESIGN.md) inherits them and declares no `colors:` of its own.
_DESIGN_MD_MATCHES = [
    path
    for path in (config.repo_root() / "_bmad-output" / "planning-artifacts" / "ux-designs").glob(
        "*/DESIGN.md"
    )
    if re.search(r"^colors:", path.read_text(encoding="utf-8"), re.M)
]
assert len(_DESIGN_MD_MATCHES) == 1, f"expected exactly one DESIGN.md, found {_DESIGN_MD_MATCHES}"
DESIGN_MD = _DESIGN_MD_MATCHES[0]
STATIC_DIR = Path(__file__).resolve().parents[1] / "src" / "harness_lab" / "web" / "static"
TOKENS_CSS = STATIC_DIR / "tokens.css"

_ATTR_TO_CSS = {
    "fontFamily": "font-family",
    "fontSize": "font-size",
    "fontWeight": "font-weight",
    "lineHeight": "line-height",
    "letterSpacing": "letter-spacing",
}


def _design_frontmatter() -> dict:
    text = DESIGN_MD.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    assert match, "DESIGN.md must start with a YAML frontmatter block."
    return yaml.safe_load(match.group(1))


def _expected_tokens(frontmatter: dict) -> dict[str, str]:
    """The `:root` block: every dark colour (charte v2.1, dark first: the `-dark` twins, under
    the light names), then the type ramp, the radii and the spacing."""
    expected: dict[str, str] = {}
    for key, value in frontmatter["colors"].items():
        if key.endswith(_DARK):
            expected[f"--color-{key.removesuffix(_DARK)}"] = str(value)
    for key, attrs in frontmatter["typography"].items():
        for attr, value in attrs.items():
            expected[f"--typography-{key}-{_ATTR_TO_CSS[attr]}"] = str(value)
    for key, value in frontmatter["rounded"].items():
        expected[f"--rounded-{key}"] = str(value)
    for key, value in frontmatter["spacing"].items():
        expected[f"--spacing-{key}"] = str(value)
    return expected


# ---------- tokens.css in three blocks (charte v2.1): the dark theme, the light one twice ---

_DARK = "-dark"
_BLOCKS = {
    "root": re.compile(r"^:root\s*\{(.*?)^\}", re.S | re.M),
    "light": re.compile(r'^:root\[data-theme="light"\]\s*\{(.*?)^\}', re.S | re.M),
    "media": re.compile(
        r"^@media \(prefers-color-scheme: light\)\s*\{\s*"
        r":root:not\(\[data-theme\]\)\s*\{(.*?)\}\s*^\}",
        re.S | re.M,
    ),
}


def _tokens_blocks() -> dict[str, str]:
    """The body of each block of tokens.css; nothing else is declared there (a fourth block, or
    a declaration outside them, would redefine a token behind the test's back)."""
    text = re.sub(r"/\*.*?\*/", "", TOKENS_CSS.read_text(encoding="utf-8"), flags=re.S)
    blocks = {}
    rest = text
    for name, pattern in _BLOCKS.items():
        found = pattern.findall(text)
        assert len(found) == 1, f"tokens.css: {len(found)} bloc(s) {name}, un seul attendu"
        blocks[name] = found[0]
        rest = pattern.sub("", rest)
    assert not rest.strip(), f"tokens.css declares outside its three blocks: {rest.strip()[:80]}"
    return blocks


def _declarations(block: str) -> dict[str, str]:
    return {name: value.strip() for name, value in re.findall(r"(--[\w-]+)\s*:\s*([^;]+);", block)}


def _color_scheme(block: str) -> str | None:
    match = re.search(r"(?<![\w-])color-scheme\s*:\s*([^;]+);", block)
    return match.group(1).strip() if match else None


def _css_custom_properties() -> dict[str, str]:
    """The `:root` block's custom properties (the dark theme, the ramp, radii, spacing)."""
    return _declarations(_tokens_blocks()["root"])


def test_tokens_css_matches_design_frontmatter():
    frontmatter = _design_frontmatter()
    expected = _expected_tokens(frontmatter)
    actual = _css_custom_properties()

    missing = expected.keys() - actual.keys()
    assert not missing, f"tokens.css is missing: {sorted(missing)}"

    mismatched = {
        name: (expected[name], actual[name])
        for name in expected
        if expected[name].strip("'\"") != actual[name].strip("'\"")
    }
    assert not mismatched, f"tokens.css values differ from DESIGN.md: {mismatched}"


def test_tokens_css_declares_no_orphan_token():
    orphans = _css_custom_properties().keys() - _expected_tokens(_design_frontmatter()).keys()
    assert not orphans, f"tokens.css declares tokens absent from DESIGN.md: {sorted(orphans)}"


def _twin_gaps(colors: dict) -> list[str]:
    """Story 31: what breaks « every colour X has its X-dark, and every X-dark its X »."""
    light = {k for k in colors if not k.endswith(_DARK)}
    dark = {k.removesuffix(_DARK) for k in colors if k.endswith(_DARK)}
    return [f"{k}-dark manque" for k in sorted(light - dark)] + [
        f"{k}-dark sans {k}" for k in sorted(dark - light)
    ]


def test_every_color_has_its_dark_twin_and_back():
    gaps = _twin_gaps(_design_frontmatter()["colors"])
    assert not gaps, gaps


def test_removing_one_dark_twin_is_caught():
    """The coverage check itself: any single `X-dark` taken out is reported."""
    colors = _design_frontmatter()["colors"]
    for twin in [k for k in colors if k.endswith(_DARK)]:
        mutated = {k: v for k, v in colors.items() if k != twin}
        assert _twin_gaps(mutated) == [f"{twin.removesuffix(_DARK)}-dark manque"], twin


def _light_expected(colors: dict) -> dict[str, str]:
    return {f"--color-{k}": str(colors[k]).upper() for k in colors if not k.endswith(_DARK)}


def test_light_block_redefines_every_color_with_its_light_value():
    """`:root[data-theme="light"]` = exactly `{--color-X: X}`, for every colour; nothing else
    (no `--color-X-dark` of its own, no other token)."""
    colors = _design_frontmatter()["colors"]
    light = {n: v.upper() for n, v in _declarations(_tokens_blocks()["light"]).items()}
    assert light == _light_expected(colors)
    dark = [k for k in colors if k.endswith(_DARK)]
    assert len(light) == len(dark), "one declaration per colour"


def test_media_block_is_the_light_block():
    """« Système » on a light workstation: the very same declarations, without the attribute."""
    blocks = _tokens_blocks()
    assert _declarations(blocks["media"]) == _declarations(blocks["light"])


def test_color_scheme_follows_the_theme():
    blocks = _tokens_blocks()
    assert _color_scheme(blocks["root"]) == "dark"
    assert _color_scheme(blocks["light"]) == "light"
    assert _color_scheme(blocks["media"]) == "light"


def test_no_static_file_loads_google_fonts():
    offenders = [
        path.name
        for path in STATIC_DIR.rglob("*")
        if path.suffix in {".html", ".css", ".js"}
        and "fonts.googleapis.com" in path.read_text(encoding="utf-8")
    ]
    assert not offenders, f"static files reference fonts.googleapis.com: {offenders}"


def test_every_font_url_exists():
    text = (STATIC_DIR / "fonts.css").read_text(encoding="utf-8")
    urls = re.findall(r"url\(\s*['\"]?([^'\")]+)['\"]?\s*\)", text)
    assert len(urls) == 4, urls
    missing = [url for url in urls if not (STATIC_DIR / url).is_file()]
    assert not missing, f"fonts.css points to missing files: {missing}"


# ---------- story 33: contrasts of the discipline tokens, colours only through tokens ----------


def _luminance(hex_color: str) -> float:
    """WCAG 2.x relative luminance of `#RRGGBB`."""
    value = hex_color.lstrip("#")
    channels = [int(value[i : i + 2], 16) / 255 for i in (0, 2, 4)]
    linear = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def _contrast(a: str, b: str) -> float:
    light, dark = sorted((_luminance(a), _luminance(b)), reverse=True)
    return (light + 0.05) / (dark + 0.05)


def _palette(colors: dict, dark: bool) -> dict[str, str]:
    """The light colours, or their `-dark` twins under the light names."""
    return {
        k: str(colors[f"{k}{_DARK}"] if dark else v)
        for k, v in colors.items()
        if not k.endswith(_DARK)
    }


def _palettes() -> dict[str, dict[str, str]]:
    """Both themes' palettes, from the DESIGN.md frontmatter: light (the keys), dark (`-dark`)."""
    colors = _design_frontmatter()["colors"]
    return {"clair": _palette(colors, False), "sombre": _palette(colors, True)}


_SOFT_BACKGROUNDS = [
    "primary-soft",
    "accent-soft",
    "warning-soft",
    "danger-soft",
    *(f"discipline-{n}-soft" for n in ("prompt", "context", "harness", "network", "neutral")),
    "produced-soft",
    "reasoning-soft",
]
_TEXT_BACKGROUNDS = ["surface", "surface-raised", *_SOFT_BACKGROUNDS]
_JSON = ["json-key", "json-string", "json-literal"]
# Charte v2.1: the status fills are dark in the light theme, light in the dark one; their text
# is `on-status`. The discipline fills carry `on-discipline` (prompt, context, harness, neutral)
# or `on-vivid` (network).
_STATUS = ["state-active", "accent", "danger", "state-error"]

# (foreground, background, WCAG AA threshold), checked in both themes: 4.5 for text, 3 for a
# mark that carries meaning (a stroke, a dot, an icon).
_THEME_PAIRS = [
    *((fg, bg, 4.5) for fg in ("ink", "ink-soft") for bg in _TEXT_BACKGROUNDS),
    *((fg, bg, 4.5) for fg in _JSON for bg in _TEXT_BACKGROUNDS),
    ("on-ink", "ink-fill", 4.5),
    ("on-ink-soft", "ink-fill", 4.5),
    ("on-ink-soft", "ink-fill", 3.0),
    ("primary", "surface-raised", 4.5),
    ("primary", "surface", 4.5),
    ("primary-deep", "primary-soft", 4.5),
    ("on-primary", "primary", 4.5),
    ("on-button", "button", 4.5),
    ("on-button", "button-hover", 4.5),
    ("button", "surface", 3.0),
    *(
        ("on-discipline", f"discipline-{n}", 4.5)
        for n in ("prompt", "context", "harness", "neutral")
    ),
    ("on-vivid", "discipline-network", 4.5),
    ("on-vivid", "hosting-network", 4.5),
    ("on-vivid", "warning", 4.5),
    *(("on-status", bg, 4.5) for bg in _STATUS),
    ("danger", "surface-raised", 4.5),
    ("danger", "danger-soft", 4.5),
    ("warning-line", "surface-raised", 4.5),
    ("warning-line", "warning-soft", 3.0),
    # Non-text, 3:1: control borders, the focus ring, the marks of a state, a discipline's
    # fill (the yellow network one is never alone: a label or a 🌐 sits beside it).
    ("line-strong", "surface-raised", 3.0),
    ("line-strong", "surface", 3.0),
    # The track of a brick switch, off (`ink-soft`), on its card: raised, or the soft fill of an
    # active one (story 3.1 review: `line` was at 1.5:1).
    *(("ink-soft", bg, 3.0) for bg in ("surface-raised", *_SOFT_BACKGROUNDS)),
    ("focus", "surface", 3.0),
    ("focus", "surface-raised", 3.0),
    ("ink-fill-edge", "surface", 3.0),
    ("ink-fill-edge", "surface-raised", 3.0),
    *(("state-active", bg, 3.0) for bg in ("surface", "surface-raised")),
    *(("state-error", bg, 3.0) for bg in ("surface", "surface-raised")),
    *(("state-unavailable", bg, 3.0) for bg in ("surface", "surface-raised")),
    ("muted", "surface-raised", 3.0),
    *(
        (f"discipline-{n}", bg, 3.0)
        for n in ("prompt", "context", "harness", "neutral")
        for bg in ("surface", "surface-raised")
    ),
    *(
        (f"segment-{s}", "segment-free", 3.0)
        for s in (
            "system-prompt",
            "global-memory",
            "tool-descriptions",
            "history",
            "rag",
            "tool-results",
            "message",
        )
    ),
    ("picto-tile", "surface", 3.0),
]


def test_both_themes_meet_wcag_aa():
    failures = []
    for theme, palette in _palettes().items():
        for fg, bg, threshold in _THEME_PAIRS:
            ratio = _contrast(palette[fg], palette[bg])
            if ratio < threshold:
                failures.append(f"{theme} : {fg} sur {bg} : {ratio:.2f} (seuil {threshold})")
    assert not failures, failures


def test_the_contrast_check_catches_a_weak_pair():
    """The check itself: ink-soft is not readable on its own background, which it flags."""
    palette = _palettes()["clair"]
    assert _contrast(palette["ink-soft"], palette["surface"]) >= 4.5
    assert _contrast(palette["ink-soft"], palette["ink-soft"]) < 4.5
    assert round(_contrast(palette["surface"], palette["surface"]), 1) == 1.0


def test_every_color_comes_from_a_charte_v21_value():
    """Charte v2.1: no colour of the interface is invented; each value of the light and dark
    palettes is one the charte publishes (its `charte.css`), so a drift or a stray colour fails."""
    charte = {
        "clair": {
            "#F6F8FB",
            "#FFFFFF",
            "#ECF0F5",
            "#CED5DF",
            "#808A97",
            "#121821",
            "#4F5A68",
            "#6E7886",
            "#1D5BC2",
            "#164A9E",
            "#E1EAFA",
            "#2A3442",
            "#8F6300",
            "#8A5F00",
            "#FBF1D6",
            "#E0B54A",
            "#1B7043",
            "#E2F1E8",
            "#E8892A",
            "#9A4A00",
            "#FDEBDA",
            "#B3261E",
            "#FCE4E1",
            "#1F5FD1",
            "#141A1F",
            "#C3CEDD",
        },
        "sombre": {
            "#0F1318",
            "#161B22",
            "#1E242C",
            "#333B46",
            "#67717E",
            "#E8ECF2",
            "#A3ADBA",
            "#8792A0",
            "#8DB0F7",
            "#B3CBFA",
            "#1A2742",
            "#0A1733",
            "#FFFFFF",
            "#E3C26B",
            "#3A3112",
            "#8CC7A0",
            "#15291D",
            "#F0A35E",
            "#3A2614",
            "#EE8C84",
            "#3B1C1A",
            "#9EC0FF",
            "#141A1F",
            "#C3CEDD",
            "#3B6FD0",
            "#F0D27A",
        },
    }
    strays = []
    for theme, palette in _palettes().items():
        allowed = charte[theme] | _CAT_SEQ[theme]
        strays += [f"{theme}: {k} = {v}" for k, v in palette.items() if v.upper() not in allowed]
    assert not strays, strays


# The categorical series of the charte (`cat-1` to `cat-8`), light then dark.
_CAT_SEQ = {
    "clair": {
        "#1D5BC2",
        "#A87A00",
        "#1F8155",
        "#B83A75",
        "#C24D1B",
        "#0E7C8C",
        "#6F7378",
        "#8A5A2B",
    },
    "sombre": {
        "#8DB0F7",
        "#E3C26B",
        "#8CC7A0",
        "#E58FB8",
        "#F2A07B",
        "#6CCAD8",
        "#A9B4C6",
        "#9FAE4F",
    },
}


def test_the_theme_roles_keep_their_contract():
    """The role tokens split from one value keep a coherent pair in both themes: the control
    border is the strong stroke, the status text sits on its own fill."""
    for palette in _palettes().values():
        assert palette["ink-fill-edge"] == palette["line-strong"]
        assert palette["on-discipline"] == palette["on-primary"]
        assert palette["on-vivid"] == "#141A1F"
        assert palette["logo-tile"] == "#FFFFFF"


# ---------- colours only through tokens.css, in every page of static/ (stories 33, 25, 31) ---

_COMMENTS = {
    ".css": re.compile(r"/\*.*?\*/", re.S),
    # Block comments, then line comments not preceded by `:` (a URL keeps its `//`).
    ".js": re.compile(r"/\*.*?\*/|(?<![:\\])//[^\n]*", re.S),
    # A page with its style and script inline (story 25); its entities (`&#9680;`) too.
    ".html": re.compile(r"<!--.*?-->|/\*.*?\*/|(?<![:\\])//[^\n]*|&#\w+;", re.S),
}
_HARD_COLOR = re.compile(
    r"#[0-9a-fA-F]{3,8}\b(?![-\w])|\b(?:rgba?|hsla?|hwb|lab|lch|oklab|oklch)\("
)

# The CSS named colours (CSS Color 4), matched only as a value: in a declaration of a
# stylesheet, a `<style>` or a `style=""`, or assigned to a colour property in a script.
_NAMED_COLORS = (
    "aliceblue antiquewhite aqua aquamarine azure beige bisque black blanchedalmond blue "
    "blueviolet brown burlywood cadetblue chartreuse chocolate coral cornflowerblue cornsilk "
    "crimson cyan darkblue darkcyan darkgoldenrod darkgray darkgreen darkgrey darkkhaki "
    "darkmagenta darkolivegreen darkorange darkorchid darkred darksalmon darkseagreen "
    "darkslateblue darkslategray darkslategrey darkturquoise darkviolet deeppink deepskyblue "
    "dimgray dimgrey dodgerblue firebrick floralwhite forestgreen fuchsia gainsboro ghostwhite "
    "gold goldenrod gray green greenyellow grey honeydew hotpink indianred indigo ivory khaki "
    "lavender lavenderblush lawngreen lemonchiffon lightblue lightcoral lightcyan "
    "lightgoldenrodyellow lightgray lightgreen lightgrey lightpink lightsalmon lightseagreen "
    "lightskyblue lightslategray lightslategrey lightsteelblue lightyellow lime limegreen linen "
    "magenta maroon mediumaquamarine mediumblue mediumorchid mediumpurple mediumseagreen "
    "mediumslateblue mediumspringgreen mediumturquoise mediumvioletred midnightblue mintcream "
    "mistyrose moccasin navajowhite navy oldlace olive olivedrab orange orangered orchid "
    "palegoldenrod palegreen paleturquoise palevioletred papayawhip peachpuff peru pink plum "
    "powderblue purple rebeccapurple red rosybrown royalblue saddlebrown salmon sandybrown "
    "seagreen seashell sienna silver skyblue slateblue slategray slategrey snow springgreen "
    "steelblue tan teal thistle tomato turquoise violet wheat white whitesmoke yellow "
    "yellowgreen"
).split()
_NAMED = "|".join(_NAMED_COLORS)
_CSS_DECLARATION = re.compile(r"(?<![\w-])[\w-]+\s*:\s*([^;{}]*)")
_CSS_STRING = re.compile(r"\"[^\"]*\"|'[^']*'")
_CSS_NAMED = re.compile(rf"(?<![\w-])(?:{_NAMED})(?![\w-])", re.I)
_JS_NAMED = re.compile(
    rf"\b(?:color|background(?:Color)?|fill|stroke|border(?:Color)?|outline(?:Color)?)\b"
    rf"[\"']?\s*[:=,]\s*[\"'`]\s*(?:{_NAMED})\b",
    re.I,
)
_HTML_CSS = re.compile(r"<style\b[^>]*>(.*?)</style>|\bstyle=\"([^\"]*)\"", re.S)
# `color-mix(` only between tokens: once its `var(--…)`, its `in <space>` and its
# percentages taken out, nothing but punctuation remains.
_COLOR_MIX = re.compile(r"color-mix\(((?:[^()]|\([^()]*\))*)\)", re.I)
_MIX_ALLOWED = re.compile(r"var\(--[\w-]+\)|\bin\s+[\w-]+|\d+(?:\.\d+)?%|[\s,]|transparent")


def _css_of(path: Path, text: str) -> str:
    if path.suffix == ".css":
        return text
    if path.suffix == ".html":
        return "\n".join(a or b for a, b in _HTML_CSS.findall(text))
    return ""


def _named_color_offenders(path: Path, text: str) -> list[str]:
    offenders = []
    for value in _CSS_DECLARATION.findall(_css_of(path, text)):
        value = _CSS_STRING.sub("", value)
        offenders += [
            f"{path.name}: {m.group(0)!r} in {value.strip()[:60]}"
            for m in _CSS_NAMED.finditer(value)
        ]
        for mix in _COLOR_MIX.findall(value):
            if _MIX_ALLOWED.sub("", mix):
                offenders.append(f"{path.name}: color-mix with a literal colour: {mix[:60]}")
    if path.suffix in {".js", ".html"}:
        offenders += [f"{path.name}: {m.group(0)!r}" for m in _JS_NAMED.finditer(text)]
    return offenders


def _static_sources() -> list[Path]:
    """Every page, stylesheet and script of static/ but tokens.css, the only home of colours;
    a page added later (stories 29, 30) is covered without touching this test."""
    return sorted(
        path
        for path in STATIC_DIR.rglob("*")
        if path.suffix in _COMMENTS and path.name != "tokens.css"
    )


def test_static_files_write_no_color_outside_the_tokens():
    """Every colour goes through `tokens.css`, so the dark theme (story 31) only redefines the
    tokens. CSS id selectors (`#gauge-bar`) are not colours: a hex colour is 3 to 8 hex digits
    not followed by a name character."""
    sources = _static_sources()
    names = {path.name for path in sources}
    assert {"app.css", "app.js", "theme.js", "diagnostic.html", "pages.css"} <= names
    assert {"llm.html", "llm.css", "llm.js"} <= names  # story 29: the « LLM nu » screen
    assert {"rag.html", "rag.css", "rag.js"} <= names  # story 30: the RAG workshop
    assert {"mcp.html", "mcp.css", "mcp.js"} <= names  # story 6 (2026-09-30): MCP workshop
    offenders = []
    for path in sources:
        text = _COMMENTS[path.suffix].sub("", path.read_text(encoding="utf-8"))
        for line in text.splitlines():
            for match in _HARD_COLOR.finditer(line):
                offenders.append(f"{path.name}: {match.group(0)!r} in {line.strip()[:80]}")
            if "invert(" in line:
                offenders.append(f"{path.name}: a filter inverts the colours: {line.strip()[:80]}")
        offenders += _named_color_offenders(path, text)
    assert not offenders, offenders


def test_the_color_guard_catches_named_colours_and_colour_functions():
    """The guard itself: named colours as values, the colour functions and a `color-mix(` with
    a literal colour are caught; `white-space`, a class name, a token mix are not."""
    css = Path("x.css")
    caught = [
        ".a { color: white; }",
        ".a { border: 1px solid Red; }",
        ".a { background: color-mix(in srgb, var(--color-ink) 50%, black); }",
        ".a { outline-color: color-mix(in oklab, var(--color-ink), currentColor); }",
    ]
    for text in caught:
        assert _named_color_offenders(css, text), text
    for fn in ("hwb(", "lab(", "lch(", "oklab(", "oklch(", "rgb(", "hsla("):
        assert _HARD_COLOR.search(f"color: {fn}0 0 0)"), fn
    assert _named_color_offenders(Path("x.js"), 'el.style.color = "white";')
    assert _named_color_offenders(Path("x.html"), '<p style="background: navy">x</p>')
    fine = [
        ".a { white-space: nowrap; color: var(--color-ink); }",
        '.white-card { content: "black"; grid-template-areas: "tile icon"; }',
        ".a { background: color-mix(in srgb, var(--color-ink) 40%, transparent); }",
    ]
    for text in fine:
        assert not _named_color_offenders(css, text), text
    assert not _HARD_COLOR.search("const label = labelFor(x);")


_THEME_SCRIPT = '<script src="/static/theme.js"></script>'


def test_every_page_loads_the_tokens_and_the_theme_script_first():
    """Story 31: each page reads its colours from tokens.css, and sets `data-theme` before its
    first render: a classic script (neither a module nor deferred) in `<head>`, before the
    first stylesheet."""
    pages = sorted(STATIC_DIR.glob("*.html"))
    assert {p.name for p in pages} >= {
        "index.html",
        "diagnostic.html",
        "llm.html",
        "rag.html",
        "mcp.html",
    }
    for page in pages:
        text = page.read_text(encoding="utf-8")
        head = text[: text.index("</head>")]
        assert '<link rel="stylesheet" href="/static/tokens.css"' in head, page.name
        assert head.count(_THEME_SCRIPT) == 1, page.name
        scripts = re.findall(r"<script\b[^>]*\bsrc=\"/static/theme\.js\"[^>]*>", text)
        assert scripts == ['<script src="/static/theme.js">'], (page.name, scripts)
        first_sheet = head.index('<link rel="stylesheet"')
        assert head.index(_THEME_SCRIPT) < first_sheet, page.name
        assert re.search(r"<select\b[^>]*\bdata-theme-picker\b", text), page.name


# ---------- story 34: the projection mode's ramp, 9/7 of tokens.css ----------
# Lot 4 (AD-28): in pages.css, shared by every page that offers the mode (panes.js).

PAGES_CSS = STATIC_DIR / "pages.css"


def _projection_block() -> dict[str, str]:
    text = PAGES_CSS.read_text(encoding="utf-8")
    match = re.search(r":root\.projection\s*\{(.*?)\}", text, re.S)
    assert match, "pages.css must redefine the ramp under :root.projection"
    return {n: v.strip() for n, v in re.findall(r"(--[\w-]+)\s*:\s*([^;]+);", match.group(1))}


def _shared_pane_classes() -> re.Pattern[str]:
    """The `pane-*` classes pages.css styles (AD-28): no other sheet sets a rule on them."""
    text = re.sub(r"/\*.*?\*/", "", PAGES_CSS.read_text(encoding="utf-8"), flags=re.S)
    names = sorted(set(re.findall(r"\.(pane-[\w-]+)", text)), key=len, reverse=True)
    return re.compile(r"\.(" + "|".join(names) + r")(?![\w-])")


def _subject(selector: str) -> str:
    """The compound a selector styles: its last one, the functional pseudo-classes left out
    (`.top-bar:not(:has(.pane-chip)) > select` styles a `select`, not a chip)."""
    bare = selector
    while (simpler := re.sub(r":(?:not|has|is|where)\([^()]*\)", "", bare)) != bare:
        bare = simpler
    return re.split(r"\s*[>+~]\s*|\s+", bare.strip())[-1]


def test_only_pages_css_writes_the_shared_rules():
    """Lot 4 (AD-28): `diagram-*` rules, the `pane-*` rules of the panes (pages.css's own
    classes) and the projection ramp live in pages.css only: a page adds its own classes beside
    them, never redefines nor overrides one in its own sheet. A style inlined in an HTML page
    counts too."""
    panes = _shared_pane_classes()
    offenders = []
    for path in sorted(STATIC_DIR.rglob("*")):
        if path.name == "pages.css" or path.suffix not in (".css", ".html"):
            continue
        text = path.read_text(encoding="utf-8")
        if path.suffix == ".html":
            text = "\n".join(re.findall(r"<style\b[^>]*>(.*?)</style>", text, re.S))
        text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
        for selector in re.findall(r"([^{}]+)\{", text):
            shared = re.search(r"\.diagram-[\w-]", selector)
            pane = any(panes.search(_subject(one)) for one in selector.split(",") if one.strip())
            if shared or pane or re.search(r":root\.projection\s*$", selector.strip()):
                offenders.append(f"{path.name}: {' '.join(selector.split())[:80]}")
    assert not offenders, offenders


def test_the_shared_rules_guard_catches_a_diagram_rule(tmp_path):
    """The guard's pattern itself: a `.diagram-` selector, alone or compound, is one."""
    for css in (".diagram-block { color: red; }", ".mcp .diagram-block.is-active, .x { }"):
        selectors = re.findall(r"([^{}]+)\{", css)
        assert any(re.search(r"\.diagram-[\w-]", s) for s in selectors), css
    assert not re.search(r"\.diagram-[\w-]", ".mcp-diagram-x { }")
    panes = _shared_pane_classes()
    for selector in (
        ".pane-chips > .pane-chip",
        ".mcp .pane-title",
        ".x .pane-text-action:disabled",
    ):
        assert panes.search(_subject(selector)), selector
    for selector in (".pane-title-row", ".top-bar:not(:has(.pane-chip.is-linked)) > select"):
        assert not panes.search(_subject(selector)), selector


def test_projection_sizes_are_the_ramp_times_nine_sevenths():
    base = _css_custom_properties()
    projection = _projection_block()
    sizes = {
        n: v for n, v in base.items() if n.startswith("--typography-") and n.endswith("-font-size")
    }
    assert sizes.keys() <= projection.keys(), "every font size of the ramp is redefined"
    for name, value in sizes.items():
        expected = round(int(value.removesuffix("px")) * 9 / 7)
        assert projection[name] == f"{expected}px", name


def test_projection_sizes_match_the_design_table():
    projection = _projection_block()
    text = DESIGN_MD.read_text(encoding="utf-8")
    rows = re.findall(r"^\| (`[^|]+`) \| (\d+) px \| (\d+) px", text, re.M)
    assert rows, "DESIGN.md > Typography holds the projection table"
    seen = set()
    for roles, base, big in rows:
        for role in re.findall(r"`([\w.-]+)`", roles):
            name = (
                f"--{role.replace('.', '-')}"
                if role.startswith("spacing.")
                else f"--typography-{role}-font-size"
            )
            assert projection.get(name) == f"{big}px", (role, projection.get(name), big)
            if not role.startswith("spacing."):
                assert _css_custom_properties()[name] == f"{base}px", role
            seen.add(name)
    font_sizes = {n for n in projection if n.endswith("-font-size")}
    assert font_sizes <= seen, f"missing from the DESIGN.md table: {sorted(font_sizes - seen)}"


# ---------- story 3 of 2026-09-30: /diagnostic sized by the tokens (lot 3: /models merged) --

_FONT_DECLARATION = re.compile(r"\b(font(?:-size)?)\s*:\s*([^;}]+)")


def test_diagnostic_and_models_pages_size_their_text_by_the_tokens():
    """No `rem` nor `em` left (the old diagnostic's 1.4rem, 0.9rem…), every font and font
    size from the type ramp; their shared styles (table, badges, buttons, fields) in
    pages.css, scoped to the annex pages."""
    offenders = []
    for name in ("diagnostic.html",):
        page = (STATIC_DIR / name).read_text(encoding="utf-8")
        assert '<body class="annex-page">' in page, name
        css = _COMMENTS[".css"].sub("", "\n".join(re.findall(r"<style>(.*?)</style>", page, re.S)))
        offenders += [f"{name}: {m.group(0)}" for m in re.finditer(r"\d(?:\.\d+)?r?em\b", css)]
        for prop, value in _FONT_DECLARATION.findall(css):
            if "var(--typography-" not in value and value.strip() not in {"inherit"}:
                offenders.append(f"{name}: {prop}: {value.strip()}")
    assert not offenders, offenders
    shared = (STATIC_DIR / "pages.css").read_text(encoding="utf-8")
    for rule in (
        ".annex-page .hosting-tag-network {",
        ".annex-page .button-primary {",
        ".annex-page .button-secondary {",
        ".annex-page .field-input {",
        # Lot 3 of 2026-10-04: the cards of « Diagnostic et modèles ».
        ".annex-page .model-grid {",
        ".annex-page .model-card {",
        ".annex-page .model-logo {",
        ".annex-page .state-pill {",
        ".annex-page .checks-panel {",
        ".annex-page .models-filters {",
    ):
        assert rule in shared, rule


# ---------- charte v2.1 (story 3.1): neutral buttons, no relief, fonts, icon, gold rule ----------

_RULE = re.compile(r"([^{}]+)\{([^{}]*)\}")
_BUTTONISH = re.compile(
    r"button|toggle|switch|segmented|-apply|-modes|-chip|-option|\.ae-button|\.scenario-info\b",
    re.I,
)
# A `primary` fill, even as a fallback or a variant (`primary-deep`…); `primary-soft` is the
# charte's selection background (`primaire-doux`) and stays allowed.
_PRIMARY_FILL = re.compile(
    r"background(?:-color)?\s*:[^;]*var\(--color-primary(?!-soft\b)[\w-]*\)?"
)


def _style_rules() -> list[tuple[str, str, str]]:
    """(file, selector, body) of every rule of every stylesheet and inline `<style>`."""
    rules = []
    for path in sorted(STATIC_DIR.glob("*.css")) + sorted(STATIC_DIR.glob("*.html")):
        text = path.read_text(encoding="utf-8")
        if path.suffix == ".html":
            text = "\n".join(re.findall(r"<style\b[^>]*>(.*?)</style>", text, re.S))
        text = _COMMENTS[".css"].sub("", text)
        rules += [(path.name, " ".join(s.split()), b) for s, b in _RULE.findall(text)]
    return rules


def test_le_bleu_n_est_jamais_un_aplat_de_bouton():
    """A button's fill is the neutral `button` token; a pressed toggle is `primary-soft` with a
    `primary` rim, never a `primary` fill."""
    offenders = [
        f"{name}: {selector[:70]}"
        for name, selector, body in _style_rules()
        if _BUTTONISH.search(selector) and _PRIMARY_FILL.search(body)
    ]
    assert not offenders, offenders


def test_the_guard_on_button_fills_sees_a_primary_fill():
    rule = ".x-button { background: var(--color-primary); }"
    assert [m for m in _RULE.findall(rule) if "var(--color-primary)" in m[1]]
    assert _BUTTONISH.search(".mcp-switch button[aria-checked]")
    assert _BUTTONISH.search(".scenario-info:hover")
    for body in (
        "background: var(--color-primary);",
        "background: var(--discipline, var(--color-primary));",
        "background-color: var(--color-primary-deep);",
    ):
        assert _PRIMARY_FILL.search(body), body
    assert not _PRIMARY_FILL.search("background: var(--color-primary-soft);")
    assert not _PRIMARY_FILL.search("background: var(--color-surface); color: var(--color-primary)")


def test_primary_buttons_are_neutral_and_secondary_ones_outlined():
    rules = {sel: body for _, sel, body in _style_rules()}
    primary = rules[".llm-button-primary"]
    assert "background: var(--color-button)" in primary
    assert "color: var(--color-on-button)" in primary
    secondary = rules[".llm-button-secondary"]
    assert "var(--color-line-strong)" in secondary
    assert "background: var(--color-primary)" not in secondary
    assert ".llm-button-primary:hover:not(:disabled)" in rules
    assert "var(--color-button-hover)" in rules[".llm-button-primary:hover:not(:disabled)"]


def test_no_relief_shadow_nor_dotted_page_is_left():
    offenders = []
    for path in STATIC_DIR.rglob("*"):
        if path.suffix in {".css", ".html", ".js"}:
            text = path.read_text(encoding="utf-8")
            offenders += [
                f"{path.name}: {word}"
                for word in ("--color-relief", "--color-dot", "relief-offset", "dot-grid")
                if word in text
            ]
    assert not offenders, offenders


def test_the_fonts_are_the_charte_ones_with_their_licences():
    fonts = STATIC_DIR / "fonts"
    names = sorted(p.name for p in fonts.iterdir())
    assert "sora-latin-600-normal.woff2" in names and "sora-OFL.txt" in names
    assert not [n for n in names if "fredoka" in n.lower()], names
    css = (STATIC_DIR / "fonts.css").read_text(encoding="utf-8")
    assert "font-family: Sora;" in css and "Fredoka" not in css
    assert "Sora" in (STATIC_DIR / "tokens.css").read_text(encoding="utf-8")


def test_the_icon_and_the_pictogram_are_the_charte_ones():
    text = (STATIC_DIR / "favicon.svg").read_text(encoding="utf-8").lstrip()
    assert text.startswith("<svg") and 'viewBox="0 0 32 32"' in text
    assert text.rstrip().endswith("</svg>")
    # The pictogram is inline in the pages (pages.css, `--color-picto-*`), not a loose file.
    assert not (STATIC_DIR / "pictogramme.svg").exists()
    logo = _COMMENTS[".css"].sub("", PAGES_CSS.read_text(encoding="utf-8"))
    assert "fill: var(--color-picto-tile)" in logo and "stroke: var(--color-picto-bars)" in logo


def test_the_gold_rule_sits_under_the_page_titles():
    css = PAGES_CSS.read_text(encoding="utf-8")
    assert "#llm-title::after" in css and "background: var(--color-title-rule)" in css
    palettes = _palettes()
    # The rule is a fine mark: the v2.1 `accent` of each theme, never the `accent-aplat` fill.
    for theme, expected in (("clair", "#8F6300"), ("sombre", "#E3C26B")):
        palette = palettes[theme]
        assert palette["title-rule"] == expected == palette["accent"]
        for ground in ("surface", "surface-raised"):
            assert _contrast(palette["title-rule"], palette[ground]) >= 3.0, (theme, ground)
    # The same values in the CSS: dark `:root`, light attribute block, light media query.
    tokens = (STATIC_DIR / "tokens.css").read_text(encoding="utf-8")
    light_attr, light_media = ':root[data-theme="light"]', "@media (prefers-color-scheme: light)"
    blocks = {
        "dark :root": (tokens[: tokens.index(light_attr)], "#E3C26B"),
        "light attribute": (
            tokens[tokens.index(light_attr) : tokens.index(light_media)],
            "#8F6300",
        ),
        "light media": (tokens[tokens.index(light_media) :], "#8F6300"),
    }
    for name, (block, value) in blocks.items():
        assert re.findall(r"--color-title-rule: (#\w+);", block) == [value], name
