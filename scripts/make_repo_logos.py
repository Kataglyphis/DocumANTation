"""Draw every Kataglyphis repository's logo into images/logos/ (stdlib only).

Run from anywhere: `python scripts/make_repo_logos.py`. Each repository copies its own file to
`images/logo.svg`; images/logos/README.md lists which logo belongs to which repository.
"""

from __future__ import annotations

import math
import re
from collections.abc import Callable
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "images" / "logos"
MINT, DEEP, FAR = "#6af0ad", "#0e271c", "#3aa77a"

# The ant from above, head up, origin mid-body; all six legs sit on the thorax, as on the insect.
HEAD = (
    "M0,-136 C21,-136 33,-124 33,-106 C33,-89 21,-78 0,-78 "
    "C-21,-78 -33,-89 -33,-106 C-33,-124 -21,-136 0,-136 Z"
)
MESO = (
    "M0,-74 C15,-74 23,-65 23,-54 C23,-43 16,-38 12,-32 C11,-22 13,-10 11,-1 "
    "C9,6 5,8 0,8 C-5,8 -9,6 -11,-1 C-13,-10 -11,-22 -12,-32 "
    "C-16,-38 -23,-43 -23,-54 C-23,-65 -15,-74 0,-74 Z"
)
GASTER = (
    "M0,32 C29,32 45,56 45,84 C45,116 27,146 0,150 C-27,146 -45,116 -45,84 C-45,56 -29,32 0,32 Z"
)
LEGS = (
    ((-16, -56), (-60, -84), (-80, -128), (-86, -152)),
    ((-13, -34), (-82, -50), (-128, -6), (-148, 16)),
    ((-12, -14), (-80, 8), (-116, 98), (-126, 150)),
)
LEG_W = (12, 9, 6)
ANTENNA = "M-14,-130 L-48,-156 Q-58,-164 -62,-198"
MANDIBLE = "M-10,-134 Q-15,-147 -4,-151"
EYES = (
    '<ellipse cx="-22" cy="-110" rx="6" ry="9" transform="rotate(12 -22 -110)"/>'
    '<ellipse cx="22" cy="-110" rx="6" ry="9" transform="rotate(-12 22 -110)"/>'
)

# The ant from the side, facing right, feet on y=55.
STAND = (
    ((58, 4), (76, 26), (90, 55)),
    ((40, 8), (34, 32), (18, 55)),
    ((22, 8), (0, 30), (-30, 55)),
)
SPRINT = (
    ((58, 4), (88, 16), (118, 30)),
    ((40, 8), (46, 32), (30, 54)),
    ((22, 8), (-10, 24), (-58, 34)),
)

# "ant 0.99" in Roboto Bold (Apache-2.0) as outlines, so the SVG renders without the font.
LABEL = (
    "M10.81 0 Q10.52 -0.57 10.39 -1.42 Q8.85 0.29 6.39 0.29 Q4.06 0.29 2.53 -1.05 Q1 -2.4 "
    "1 -4.45 Q1 -6.97 2.86 -8.32 Q4.73 -9.67 8.26 -9.68 H10.21 V-10.59 Q10.21 -11.69 9.65 "
    "-12.35 Q9.08 -13.01 7.87 -13.01 Q6.8 -13.01 6.19 -12.5 Q5.58 -11.98 5.58 -11.09 "
    "H1.35 Q1.35 -12.47 2.2 -13.64 Q3.05 -14.81 4.6 -15.48 Q6.15 -16.14 8.09 -16.14 "
    "Q11.02 -16.14 12.74 -14.67 Q14.46 -13.2 14.46 -10.53 V-3.66 Q14.47 -1.41 15.09 -0.25 "
    "V0 Z M7.31 -2.94 Q8.25 -2.94 9.04 -3.36 Q9.83 -3.78 10.21 -4.48 V-7.21 H8.63 Q5.45 "
    "-7.21 5.24 -5.01 L5.23 -4.76 Q5.23 -3.97 5.79 -3.46 Q6.34 -2.94 7.31 -2.94 Z M21.61 "
    "-15.85 21.74 -14.02 Q23.44 -16.14 26.29 -16.14 Q28.81 -16.14 30.04 -14.66 Q31.27 "
    "-13.18 31.3 -10.24 V0 H27.07 V-10.14 Q27.07 -11.48 26.48 -12.09 Q25.9 -12.7 24.54 "
    "-12.7 Q22.75 -12.7 21.86 -11.18 V0 H17.62 V-15.85 Z M39.58 -19.75 V-15.85 H42.29 "
    "V-12.74 H39.58 V-4.83 Q39.58 -3.96 39.92 -3.57 Q40.25 -3.19 41.21 -3.19 Q41.91 -3.19 "
    "42.45 -3.3 V-0.09 Q41.21 0.29 39.89 0.29 Q35.43 0.29 35.35 -4.2 V-12.74 H33.03 "
    "V-15.85 H35.35 V-19.75 Z M66.3 -8.82 Q66.3 -4.39 64.47 -2.05 Q62.64 0.29 59.11 0.29 "
    "Q55.62 0.29 53.77 -2.01 Q51.93 -4.31 51.88 -8.6 V-12.52 Q51.88 -16.99 53.74 -19.31 "
    "Q55.59 -21.62 59.08 -21.62 Q62.56 -21.62 64.41 -19.33 Q66.25 -17.04 66.3 -12.74 Z "
    "M62.07 -13.12 Q62.07 -15.78 61.34 -16.98 Q60.62 -18.19 59.08 -18.19 Q57.58 -18.19 "
    "56.87 -17.04 Q56.16 -15.89 56.12 -13.45 V-8.26 Q56.12 -5.65 56.83 -4.39 Q57.54 -3.12 "
    "59.11 -3.12 Q60.66 -3.12 61.35 -4.34 Q62.04 -5.55 62.07 -8.06 Z M69.55 -2.08 Q69.55 "
    "-3.09 70.23 -3.72 Q70.91 -4.35 71.94 -4.35 Q72.98 -4.35 73.66 -3.72 Q74.34 -3.09 "
    "74.34 -2.08 Q74.34 -1.08 73.67 -0.46 Q72.99 0.16 71.94 0.16 Q70.9 0.16 70.22 -0.46 "
    "Q69.55 -1.08 69.55 -2.08 Z M87.77 -8.53 Q86.12 -6.9 83.91 -6.9 Q81.08 -6.9 79.38 "
    "-8.84 Q77.68 -10.78 77.68 -14.08 Q77.68 -16.17 78.6 -17.92 Q79.51 -19.67 81.15 "
    "-20.65 Q82.79 -21.62 84.84 -21.62 Q86.95 -21.62 88.59 -20.57 Q90.23 -19.51 91.14 "
    "-17.53 Q92.05 -15.56 92.07 -13.01 V-11.44 Q92.07 -6.11 89.41 -3.06 Q86.76 -0.01 81.9 "
    "0.19 L80.86 0.21 V-3.33 L81.8 -3.34 Q87.32 -3.59 87.77 -8.53 Z M84.95 -10.14 Q85.97 "
    "-10.14 86.71 -10.66 Q87.45 -11.19 87.83 -11.94 V-13.68 Q87.83 -15.83 87.01 -17.02 "
    "Q86.19 -18.21 84.81 -18.21 Q83.54 -18.21 82.72 -17.04 Q81.9 -15.88 81.9 -14.12 Q81.9 "
    "-12.38 82.7 -11.26 Q83.5 -10.14 84.95 -10.14 Z M104.99 -8.53 Q103.33 -6.9 101.12 "
    "-6.9 Q98.29 -6.9 96.59 -8.84 Q94.89 -10.78 94.89 -14.08 Q94.89 -16.17 95.81 -17.92 "
    "Q96.72 -19.67 98.36 -20.65 Q100 -21.62 102.06 -21.62 Q104.17 -21.62 105.81 -20.57 "
    "Q107.45 -19.51 108.35 -17.53 Q109.26 -15.56 109.28 -13.01 V-11.44 Q109.28 -6.11 "
    "106.63 -3.06 Q103.97 -0.01 99.11 0.19 L98.07 0.21 V-3.33 L99.01 -3.34 Q104.53 -3.59 "
    "104.99 -8.53 Z M102.16 -10.14 Q103.18 -10.14 103.92 -10.66 Q104.66 -11.19 105.04 "
    "-11.94 V-13.68 Q105.04 -15.83 104.22 -17.02 Q103.4 -18.21 102.03 -18.21 Q100.75 "
    "-18.21 99.93 -17.04 Q99.11 -15.88 99.11 -14.12 Q99.11 -12.38 99.91 -11.26 Q100.71 "
    "-10.14 102.16 -10.14 Z"
)
LABEL_WIDTH = 110.8

Pts = tuple[tuple[float, float], ...]


def fmt(v: float) -> str:
    return f"{v:.1f}".rstrip("0").rstrip(".")


def mirror(d: str) -> str:
    """The same absolute path, reflected across x=0."""
    return re.sub(r"(-?[\d.]+),", lambda m: f"{fmt(-float(m.group(1)))},", d)


def poly(pts: Pts) -> str:
    return "M" + " L".join(f"{fmt(x)},{fmt(y)}" for x, y in pts)


def svg(body: str, defs: str, label: str) -> str:
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" '
        f'width="512" height="512" role="img" aria-label="{label}">\n'
        f"<title>{label}</title>\n"
        + (f"<defs>{defs}</defs>\n" if defs else "")
        + body
        + "\n</svg>\n"
    )


def rim(color: str = "#ffffff14") -> str:
    return (
        '<rect x="25.5" y="25.5" width="461" height="461" rx="110.5" fill="none" '
        f'stroke="{color}" stroke-width="3"/>'
    )


def tile(base: str, light: str) -> tuple[str, str]:
    defs = (
        '<linearGradient id="tile" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0" stop-color="{light}"/><stop offset="1" stop-color="{base}"/>'
        "</linearGradient>"
    )
    body = (
        '<rect x="24" y="24" width="464" height="464" rx="112" fill="url(#tile)"/>\n' + rim() + "\n"
    )
    return defs, body


def outline(fragment: str, color: str, pad: float) -> str:
    """The same shapes in one colour, `pad` wider on every side, to cut them free of a prop."""
    f = re.sub(r'(stroke|fill)="#[0-9a-fA-F]{3,8}"', lambda m: f'{m.group(1)}="{color}"', fragment)
    f = re.sub(
        r'stroke-width="([\d.]+)"',
        lambda m: f'stroke-width="{fmt(float(m.group(1)) + 2 * pad)}"',
        f,
    )
    f = re.sub(
        r'<g fill="' + re.escape(color) + '">',
        f'<g fill="{color}" stroke="{color}" stroke-width="{2 * pad}" stroke-linejoin="round">',
        f,
    )
    return re.sub(
        r'<(ellipse|circle|path)([^>]*?)fill="' + re.escape(color) + r'"(?![^>]*stroke=)',
        lambda m: (
            f'<{m.group(1)}{m.group(2)}fill="{color}" stroke="{color}" stroke-width="{2 * pad}"'
        ),
        f,
    )


def placed(fragment: str, transform: str, cut_from: str | None = None, pad: float = 7) -> str:
    s = ""
    if cut_from:
        s += f'<g transform="{transform}">{outline(fragment, cut_from, pad)}</g>\n'
    return s + f'<g transform="{transform}">{fragment}</g>\n'


def ant(fill: str, cut: str | None = None, k: float = 1.0, mandibles: bool = True) -> str:
    """The ant from above; `cut` is the colour its eyes are cut in, `k` scales the legs."""
    s = [f'<g fill="none" stroke="{fill}" stroke-linecap="round" stroke-linejoin="round">']
    for side in (1, -1):
        for leg in LEGS:
            for i in range(3):
                (x0, y0), (x1, y1) = leg[i], leg[i + 1]
                s.append(
                    f'<path d="M{fmt(side * x0)},{y0} L{fmt(side * x1)},{y1}" '
                    f'stroke-width="{fmt(LEG_W[i] * k)}"/>'
                )
        s.append(
            f'<path d="{ANTENNA if side == 1 else mirror(ANTENNA)}" stroke-width="{fmt(7 * k)}"/>'
        )
        if mandibles:
            m = MANDIBLE if side == 1 else mirror(MANDIBLE)
            s.append(f'<path d="{m}" stroke-width="{fmt(6 * k)}"/>')
    s.append("</g>")
    s.append(f'<g fill="{fill}">')
    s.append(f'<path d="{HEAD}"/><path d="{MESO}"/><path d="{GASTER}"/>')
    s.append('<ellipse cx="0" cy="20" rx="8" ry="7"/>')
    s.append("</g>")
    if cut:
        s.append(f'<g fill="{cut}">{EYES}</g>')
    return "\n".join(s)


def body_only(fill: str, cut: str) -> str:
    """Head, thorax, waist and gaster without legs, to draw over a prop that covers the legs."""
    return (
        f'<g fill="{fill}"><path d="{HEAD}"/><path d="{MESO}"/><path d="{GASTER}"/>'
        f'<ellipse cx="0" cy="20" rx="8" ry="7"/></g><g fill="{cut}">{EYES}</g>'
    )


def profile(
    fill: str, cut: str, w: float = 1.0, legs: tuple = STAND, far: str | None = None
) -> str:
    """The ant from the side; `far` draws the three legs of the other side behind it."""
    s = []
    if far:
        s.append(f'<g fill="none" stroke="{far}" stroke-linecap="round" stroke-linejoin="round">')
        for leg in legs:
            behind = poly(tuple((x - 8, y - 2) for x, y in leg))
            s.append(f'<path d="{behind}" stroke-width="{fmt(7 * w)}"/>')
        s.append("</g>")
    s.append(f'<g fill="none" stroke="{fill}" stroke-linecap="round" stroke-linejoin="round">')
    for leg in legs:
        s.append(f'<path d="{poly(leg[:2])}" stroke-width="{fmt(10 * w)}"/>')
        s.append(f'<path d="{poly(leg[1:])}" stroke-width="{fmt(7 * w)}"/>')
    s.append(f'<path d="M92,-28 L104,-62 Q122,-64 140,-48" stroke-width="{fmt(7 * w)}"/>')
    s.append(f'<path d="M104,-6 Q116,-2 113,8" stroke-width="{fmt(6 * w)}"/>')
    s.append("</g>")
    s.append(
        f'<g fill="{fill}">'
        '<ellipse cx="-58" cy="-8" rx="44" ry="30" transform="rotate(-18 -58 -8)"/>'
        '<ellipse cx="-6" cy="2" rx="8" ry="12"/>'
        '<path d="M4,6 C2,-8 10,-20 26,-22 C40,-24 52,-20 58,-14 C66,-8 68,0 64,6 '
        'C56,12 14,14 4,6 Z"/>'
        '<ellipse cx="86" cy="-14" rx="23" ry="18" transform="rotate(12 86 -14)"/>'
        "</g>"
    )
    s.append(f'<ellipse cx="91" cy="-19" rx="5.5" ry="6.5" fill="{cut}"/>')
    return "\n".join(s)


def kataglyphis() -> str:
    defs = (
        '<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">'
        '<stop offset="0" stop-color="#14503a"/><stop offset="1" stop-color="#0a2519"/>'
        "</linearGradient>"
    )
    body = (
        '<rect x="24" y="24" width="464" height="464" rx="112" fill="url(#bg)"/>\n'
        + rim()
        + "\n"
        + f'<g transform="translate(256 276) scale(1.02)">\n{ant(MINT, "#0f3a29", k=1.3)}\n</g>'
    )
    return svg(body, defs, "Kataglyphis: a desert ant on a green badge")


def antfrastructure() -> str:
    base = "#0b3540"
    defs, t = tile(base, "#12505c")
    amber, rib, rail = "#f2a93b", "#d88b1f", "#b8700f"
    ribs = "".join(f'<path d="M{x},176 L{x},300"/>' for x in range(150, 330, 20))
    box = (
        '<g transform="rotate(-5 256 238)">'
        f'<rect x="122" y="160" width="270" height="156" rx="8" fill="{amber}"/>'
        f'<g stroke="{rib}" stroke-width="7" stroke-linecap="round">{ribs}</g>'
        f'<rect x="122" y="160" width="270" height="16" rx="6" fill="{rail}"/>'
        f'<rect x="122" y="300" width="270" height="16" rx="6" fill="{rail}"/>'
        f'<rect x="340" y="176" width="52" height="124" fill="{rib}"/>'
        f'<g stroke="{rail}" stroke-width="6" stroke-linecap="round">'
        '<path d="M354,182 L354,294"/><path d="M378,182 L378,294"/></g>'
        f'<g fill="{rail}"><rect x="346" y="226" width="16" height="8" rx="2"/>'
        '<rect x="370" y="236" width="16" height="8" rx="2"/></g>'
        f'<circle cx="168" cy="238" r="26" fill="{MINT}"/>'
        f'<path d="M156,238 L165,248 L182,228" fill="none" stroke="{base}" stroke-width="8" '
        'stroke-linecap="round" stroke-linejoin="round"/>'
        "</g>"
    )
    a = profile(MINT, base, w=1.25, far=FAR)
    body = t + box + "\n" + placed(a, "translate(236 362) scale(1.18)", base, 8)
    return svg(body, defs, "ANTfrastructure: an ant hauling a shipping container")


def note(x: int, y: int, col: str, flag: bool = True, stem: int = 58) -> str:
    s = (
        f'<ellipse cx="{x}" cy="{y}" rx="15" ry="11" transform="rotate(-22 {x} {y})" fill="{col}"/>'
        f'<path d="M{x + 13},{y - 4} L{x + 13},{y - stem}" stroke="{col}" stroke-width="6" '
        'stroke-linecap="round"/>'
    )
    if flag:
        s += (
            f'<path d="M{x + 13},{y - stem} C{x + 22},{y - stem + 14} {x + 40},{y - stem + 18} '
            f'{x + 34},{y - stem + 40}" fill="none" stroke="{col}" stroke-width="6" '
            'stroke-linecap="round"/>'
        )
    return s


def orchestrant() -> str:
    base = "#221a46"
    defs, t = tile(base, "#33296a")
    gold = "#f5c451"
    legs = (
        f'<g fill="none" stroke="{FAR}" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M258,276 L236,334 L224,402" stroke-width="9"/>'
        '<path d="M270,262 L300,318 L318,402" stroke-width="9"/>'
        '<path d="M272,244 L302,222 L320,190" stroke-width="9"/>'
        "</g>"
        f'<g fill="none" stroke="{MINT}" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M250,280 L224,338" stroke-width="12"/>'
        '<path d="M224,338 L206,404" stroke-width="9"/>'
        '<path d="M262,268 L288,328" stroke-width="12"/>'
        '<path d="M288,328 L298,404" stroke-width="9"/>'
        '<path d="M276,250 L320,252" stroke-width="12"/>'
        '<path d="M320,252 L348,218" stroke-width="9"/>'
        '<path d="M306,196 L314,156 Q332,140 352,146" stroke-width="8"/>'
        '<path d="M318,224 Q330,230 328,240" stroke-width="7"/>'
        "</g>"
    )
    parts = (
        f'<g fill="{MINT}">'
        '<ellipse cx="198" cy="340" rx="52" ry="34" transform="rotate(-47 198 340)"/>'
        '<ellipse cx="238" cy="298" rx="9" ry="13" transform="rotate(-40 238 298)"/>'
        '<ellipse cx="266" cy="262" rx="36" ry="18" transform="rotate(-58 266 262)"/>'
        '<ellipse cx="300" cy="212" rx="27" ry="21" transform="rotate(-25 300 212)"/>'
        "</g>"
        f'<ellipse cx="308" cy="205" rx="5.5" ry="6.5" fill="{base}"/>'
    )
    fig = legs + parts
    baton = (
        '<path d="M344,222 L424,126" stroke="#fff3d6" stroke-width="7" stroke-linecap="round"/>'
        '<path d="M428,98 L433,116 L451,121 L433,126 L428,144 L423,126 L405,121 L423,116 Z" '
        'fill="#fff3d6"/>'
    )
    trail = (
        '<path d="M412,96 C360,44 250,52 196,92" fill="none" stroke="#fff3d6" '
        'stroke-opacity=".45" stroke-width="5" stroke-linecap="round" stroke-dasharray="0 14"/>'
    )
    notes = (
        note(124, 206, gold, flag=False)
        + note(190, 186, gold, flag=False)
        + f'<path d="M137,148 L203,128" stroke="{gold}" stroke-width="12" stroke-linecap="round"/>'
        + note(112, 316, gold)
    )
    stage = '<ellipse cx="262" cy="410" rx="130" ry="20" fill="#ffffff" opacity=".07"/>'
    body = t + stage + trail + notes + outline(fig, base, 7) + fig + baton
    return svg(body, defs, "OrchestrANT: an ant conducting with a baton")


def modelant() -> str:
    rot, sc, cx, cy = 22, 0.74, 262, 300
    pts = [p for leg in LEGS for p in leg]
    pts += [(-14, -130), (-48, -156), (-62, -198), (-45, 84), (0, 150), (-33, -106), (0, -151)]
    pts += [(-x, y) for x, y in pts]
    th = math.radians(rot)
    xs = [cx + sc * (x * math.cos(th) - y * math.sin(th)) for x, y in pts]
    ys = [cy + sc * (x * math.sin(th) + y * math.cos(th)) for x, y in pts]
    x0, x1, y0, y1 = min(xs) - 16, max(xs) + 16, min(ys) - 16, max(ys) + 16
    amber, bg, tab, arm = "#f5b83d", "#0c1712", 42, 34
    grid = "".join(f'<path d="M{v},24 L{v},488 M24,{v} L488,{v}"/>' for v in range(88, 480, 64))
    corners = (
        f"M{fmt(x0)},{fmt(y0 + arm)} L{fmt(x0)},{fmt(y0)} L{fmt(x0 + arm)},{fmt(y0)} "
        f"M{fmt(x1 - arm)},{fmt(y0)} L{fmt(x1)},{fmt(y0)} L{fmt(x1)},{fmt(y0 + arm)} "
        f"M{fmt(x1)},{fmt(y1 - arm)} L{fmt(x1)},{fmt(y1)} L{fmt(x1 - arm)},{fmt(y1)} "
        f"M{fmt(x0 + arm)},{fmt(y1)} L{fmt(x0)},{fmt(y1)} L{fmt(x0)},{fmt(y1 - arm)}"
    )
    body = (
        f'<rect x="24" y="24" width="464" height="464" rx="112" fill="{bg}"/>\n'
        f'<g stroke="#ffffff" stroke-opacity=".05" stroke-width="2">{grid}</g>\n'
        + rim()
        + "\n"
        + f'<g transform="translate({cx} {cy}) rotate({rot}) scale({sc})">\n'
        + f"{ant(MINT, bg, k=1.35)}\n</g>\n"
        + f'<rect x="{fmt(x0)}" y="{fmt(y0)}" width="{fmt(x1 - x0)}" height="{fmt(y1 - y0)}" '
        + f'fill="{amber}" fill-opacity=".06" stroke="{amber}" stroke-width="5"/>\n'
        + f'<path d="{corners}" fill="none" stroke="{amber}" stroke-width="13" '
        + 'stroke-linecap="square"/>\n'
        + f'<rect x="{fmt(x0 - 6.5)}" y="{fmt(y0 - tab)}" width="{fmt(LABEL_WIDTH + 28)}" '
        + f'height="{tab}" rx="4" fill="{amber}"/>\n'
        + f'<path transform="translate({fmt(x0 + 7.5)} {fmt(y0 - 11)})" d="{LABEL}" fill="{bg}"/>'
    )
    return svg(body, "", "ModelANT: an ant in a detection box labelled ant 0.99")


def omniaccelerant() -> str:
    base = "#3a1410"
    defs, t = tile(base, "#5a2114")
    bolt = (
        '<path d="M296,52 L168,282 L248,282 L206,462 L352,206 L270,206 L326,52 Z" fill="#f5a524"/>'
    )
    streaks = "".join(
        f'<path d="M{x0},{y} L{x1},{y}" stroke="#f5a524" stroke-opacity="{o}" stroke-width="11" '
        'stroke-linecap="round"/>'
        for x0, x1, y, o in ((58, 126, 270, 0.9), (76, 148, 304, 0.7), (54, 110, 338, 0.5))
    )
    a = profile(MINT, base, w=1.2, legs=SPRINT, far=FAR)
    body = t + bolt + streaks + "\n" + placed(a, "translate(250 318) scale(1.12)", base, 9)
    return svg(body, defs, "OmniAccelerANT: a sprinting ant and a lightning bolt")


def accelerantgine() -> str:
    base = "#2a1a10"
    defs, t = tile(base, "#43291a")
    defs += (
        '<radialGradient id="coffee" cx=".42" cy=".38" r=".7">'
        '<stop offset="0" stop-color="#8a4f2a"/><stop offset="1" stop-color="#4e2812"/>'
        "</radialGradient>"
    )
    cup = (
        '<circle cx="236" cy="262" r="204" fill="#e8d9bf"/>'
        '<circle cx="236" cy="262" r="186" fill="#f1e5cf"/>'
        '<rect x="356" y="236" width="104" height="50" rx="25" fill="#f8efde"/>'
        '<circle cx="236" cy="262" r="152" fill="#f8efde"/>'
        '<circle cx="236" cy="262" r="128" fill="url(#coffee)"/>'
        '<circle cx="236" cy="262" r="128" fill="none" stroke="#a8693c" stroke-width="10" '
        'opacity=".6"/>'
    )
    art = ant("#f3dfbf", None, k=1.35, mandibles=False)
    little = ant(MINT, base, k=1.6)
    body = (
        t
        + cup
        + "\n"
        + f'<g transform="translate(236 274) scale(.58)" opacity=".95">{art}</g>\n'
        + placed(little, "translate(400 404) rotate(-40) scale(.22)", "#e8d9bf", 18)
    )
    return svg(body, defs, "AccelerANTgine: latte art in the shape of an ant")


def hello_triangle(top: Pts, left: Pts, right: Pts, n: int = 16) -> str:
    """The RGB triangle every graphics API greets with, flat-shaded in n² steps."""
    cols = ((0xFF, 0x45, 0x45), (0x3C, 0x74, 0xFF), (0x2B, 0xD4, 0x6A))

    def pt(i: int, j: int) -> tuple[float, float]:
        k = n - i - j
        return (
            (i * top[0] + j * left[0] + k * right[0]) / n,
            (i * top[1] + j * left[1] + k * right[1]) / n,
        )

    def col(ws: tuple[float, float, float]) -> str:
        c = [sum(ws[v] * cols[v][ch] for v in range(3)) for ch in range(3)]
        return "#{:02x}{:02x}{:02x}".format(*(round(x) for x in c))

    tris = []
    for i in range(n):
        for j in range(n - i):
            w = ((i + 1 / 3) / n, (j + 1 / 3) / n, (n - i - j - 2 / 3) / n)
            tris.append(((pt(i + 1, j), pt(i, j + 1), pt(i, j)), col(w)))
            if i + j < n - 1:
                w = ((i + 2 / 3) / n, (j + 2 / 3) / n, (n - i - j - 4 / 3) / n)
                tris.append(((pt(i + 1, j), pt(i + 1, j + 1), pt(i, j + 1)), col(w)))
    return "".join(
        f'<polygon points="{" ".join(f"{fmt(x)},{fmt(y)}" for x, y in p)}" fill="{c}" '
        f'stroke="{c}" stroke-width="1.2"/>'
        for p, c in tris
    )


def frill(r: int, rs: int, n: int, col: str) -> str:
    dots = "".join(
        f'<circle cx="{fmt(r * math.sin(math.radians(a)))}" '
        f'cy="{fmt(20 + r * math.cos(math.radians(a)))}" r="{rs}"/>'
        for a in range(0, 360, 360 // n)
    )
    return f'<g fill="{col}">{dots}<circle cx="0" cy="20" r="{r}"/></g>'


def beschleunigerballett() -> str:
    base = "#11132c"
    defs, t = tile(base, "#1d2150")
    tri = hello_triangle((256, 70), (64, 412), (448, 412))
    tutu = (
        frill(70, 19, 24, "#ff6fae") + frill(50, 15, 18, "#ff9fcb") + frill(30, 11, 12, "#ffd0e6")
    )
    full = ant(MINT, base, k=1.4)
    tr = "translate(256 286) rotate(18) scale(.66)"
    spin = (
        '<g fill="none" stroke="#ffffff" stroke-linecap="round" stroke-width="7" opacity=".85">'
        '<path d="M138,196 A132,132 0 0 1 214,142"/>'
        '<path d="M380,372 A132,132 0 0 1 300,424"/></g>'
        '<path d="M400,120 L405,136 L421,141 L405,146 L400,162 L395,146 L379,141 L395,136 Z" '
        'fill="#ffffff"/>'
    )
    body = (
        t
        + tri
        + "\n"
        + spin
        + f'<g transform="{tr}">{outline(full, base, 9)}</g>\n'
        + f'<g transform="{tr}">{full}{tutu}{body_only(MINT, base)}</g>'
    )
    return svg(body, defs, "BeschleunigerBallett: a ballerina ant on the RGB hello triangle")


def assetant() -> str:
    defs = (
        '<clipPath id="tileclip"><rect x="24" y="24" width="464" height="464" rx="112"/></clipPath>'
        '<linearGradient id="lw" x1="0" y1="0" x2="1" y2="0">'
        '<stop offset="0" stop-color="#8f1f1a"/><stop offset="1" stop-color="#c2362b"/>'
        "</linearGradient>"
        '<linearGradient id="rw" x1="1" y1="0" x2="0" y2="0">'
        '<stop offset="0" stop-color="#17703e"/><stop offset="1" stop-color="#2a9d58"/>'
        "</linearGradient>"
        '<radialGradient id="glow" cx=".5" cy="0" r="1">'
        '<stop offset="0" stop-color="#ffffff" stop-opacity=".28"/>'
        '<stop offset="1" stop-color="#ffffff" stop-opacity="0"/></radialGradient>'
    )
    room = (
        '<g clip-path="url(#tileclip)">'
        '<rect x="24" y="24" width="464" height="464" fill="#cfc8bb"/>'
        '<polygon points="24,24 488,24 360,140 152,140" fill="#efeae0"/>'
        '<polygon points="24,488 488,488 360,356 152,356" fill="#b9b1a2"/>'
        '<polygon points="24,24 152,140 152,356 24,488" fill="url(#lw)"/>'
        '<polygon points="488,24 360,140 360,356 488,488" fill="url(#rw)"/>'
        '<rect x="152" y="140" width="208" height="216" fill="#e2dccf"/>'
        '<polygon points="214,58 298,58 284,86 228,86" fill="#fffbe6"/>'
        '<rect x="24" y="24" width="464" height="464" fill="url(#glow)"/>'
        '<ellipse cx="270" cy="440" rx="100" ry="16" fill="#000000" opacity=".12"/>'
        '<polygon points="200,358 316,358 344,336 228,336" fill="#f4f0e8"/>'
        '<polygon points="200,358 316,358 316,446 200,446" fill="#dcd6ca"/>'
        '<polygon points="316,358 344,336 344,420 316,446" fill="#c6bfb1"/>'
        "</g>" + rim("#00000018")
    )
    a = profile(MINT, DEEP, w=1.3, far=FAR)
    body = room + "\n" + placed(a, "translate(258 298) scale(.78)", DEEP, 8)
    return svg(body, defs, "AssetANT: an ant in the Cornell box")


def documantation() -> str:
    base = "#13233f"
    defs, t = tile(base, "#1e3560")
    page, edge, line, deep = "#f6eedc", "#d6c6a3", "#b9ae98", "#145a3c"
    left = "M256,158 C212,134 150,128 84,142 L84,378 C150,364 212,370 256,394 Z"
    right = "M256,158 C300,134 362,128 428,142 L428,378 C362,364 300,370 256,394 Z"
    text = "".join(
        f'<path d="M{x0},{y} L{x1},{y}" />'
        for x0, x1, y in (
            (112, 222, 226),
            (112, 230, 250),
            (112, 208, 274),
            (112, 226, 298),
            (112, 196, 322),
        )
    )
    hashmark = (
        f'<g stroke="{deep}" stroke-width="8" stroke-linecap="round">'
        '<path d="M124,166 L118,200"/><path d="M144,166 L138,200"/>'
        '<path d="M112,176 L152,176"/><path d="M110,190 L150,190"/></g>'
        f'<path d="M166,184 L226,184" stroke="{deep}" stroke-width="10" stroke-linecap="round"/>'
    )
    caption = (
        f'<g stroke="{line}" stroke-width="7" stroke-linecap="round">'
        '<path d="M300,330 L392,330"/><path d="M316,350 L376,350"/></g>'
    )
    ribbon = f'<path d="M262,388 L262,470 L276,452 L290,470 L290,382" fill="{MINT}"/>'
    body = (
        t
        + '<g transform="translate(0 10)">'
        + f'<path d="{left}" fill="{edge}" transform="translate(-6 8)"/>'
        + f'<path d="{right}" fill="{edge}" transform="translate(6 8)"/>'
        + ribbon
        + f'<path d="{left}" fill="{page}"/><path d="{right}" fill="{page}"/>'
        + '<path d="M256,158 L256,394" stroke="#00000022" stroke-width="4"/>'
        + hashmark
        + f'<g stroke="{line}" stroke-width="7" stroke-linecap="round">{text}</g>'
        + f'<g transform="translate(346 238) scale(.36)">{ant(deep, page, k=1.5)}</g>'
        + caption
        + "</g>"
    )
    return svg(body, defs, "DocumANTation: an open book with the ant as its figure")


def anthology() -> str:
    base = "#0d3330"
    defs, t = tile(base, "#14504a")
    surf, line = "#133f3b", "#2b6b62"
    phone = (
        f'<rect x="316" y="96" width="132" height="236" rx="22" fill="#0f3a36" stroke="{FAR}" '
        'stroke-width="6"/>'
        f'<rect x="362" y="110" width="40" height="8" rx="4" fill="{FAR}"/>'
        f'<rect x="336" y="140" width="92" height="56" rx="10" fill="{FAR}" opacity=".35"/>'
        f'<rect x="336" y="210" width="70" height="10" rx="5" fill="{FAR}" opacity=".5"/>'
        f'<rect x="336" y="230" width="84" height="10" rx="5" fill="{FAR}" opacity=".5"/>'
    )
    win = (
        f'<rect x="64" y="148" width="320" height="284" rx="22" fill="{surf}" stroke="{line}" '
        'stroke-width="4"/>'
        '<path d="M64,170 a22,22 0 0 1 22,-22 L362,148 a22,22 0 0 1 22,22 L384,192 L64,192 Z" '
        f'fill="{line}"/>'
        f'<g fill="{base}"><circle cx="94" cy="170" r="8"/><circle cx="120" cy="170" r="8"/>'
        '<circle cx="146" cy="170" r="8"/></g>'
        f'<rect x="96" y="372" width="76" height="36" rx="18" fill="{MINT}"/>'
        f'<circle cx="154" cy="390" r="13" fill="{surf}"/>'
        f'<path d="M204,390 L350,390" stroke="{line}" stroke-width="8" stroke-linecap="round"/>'
        f'<path d="M204,390 L290,390" stroke="{MINT}" stroke-width="8" stroke-linecap="round"/>'
        f'<circle cx="290" cy="390" r="14" fill="{MINT}"/>'
    )
    a = ant(MINT, surf, k=1.5)
    body = t + phone + win + f'<g transform="translate(224 282) scale(.42)">{a}</g>'
    return svg(body, defs, "ANThology: an ant inside an app window, with a phone behind it")


def gear(cx: int, cy: int, ro: int, rr: int, rh: int, n: int = 12) -> str:
    """An n-toothed cog with a round hole; even-odd fill leaves the hole open."""
    step = 360 / n
    pts = []
    for i in range(n):
        for r, a in ((rr, -step * 0.32), (ro, -step * 0.18), (ro, step * 0.18), (rr, step * 0.32)):
            th = math.radians(i * step + a)
            pts.append((cx + r * math.sin(th), cy - r * math.cos(th)))
    d = "M" + " L".join(f"{fmt(x)},{fmt(y)}" for x, y in pts) + " Z"
    return d + f" M{cx + rh},{cy} A{rh},{rh} 0 1 0 {cx - rh},{cy} A{rh},{rh} 0 1 0 {cx + rh},{cy} Z"


def oxidant() -> str:
    base = "#231815"
    defs, t = tile(base, "#3a2620")
    defs += (
        '<linearGradient id="steel" x1="0" y1="0" x2="1" y2="1">'
        '<stop offset="0" stop-color="#7c838c"/><stop offset="1" stop-color="#454b53"/>'
        "</linearGradient>"
    )
    cog = f'<path d="{gear(256, 256, 214, 184, 150)}" fill="url(#steel)" fill-rule="evenodd"/>'
    bolts = "".join(
        f'<circle cx="{fmt(256 + 167 * math.sin(math.radians(a)))}" '
        f'cy="{fmt(256 - 167 * math.cos(math.radians(a)))}" r="7" fill="#353a40"/>'
        for a in range(15, 360, 30)
    )
    spots = (
        '<g fill="#8f3c16" opacity=".85"><circle cx="-14" cy="70" r="11"/>'
        '<circle cx="18" cy="106" r="8"/><circle cx="-6" cy="-40" r="6"/>'
        '<circle cx="10" cy="-112" r="5"/></g>'
        '<g fill="#f0a36a" opacity=".8"><circle cx="14" cy="60" r="6"/>'
        '<circle cx="-20" cy="118" r="5"/><circle cx="-8" cy="-60" r="4"/></g>'
    )
    a = ant("#d0652a", base, k=1.4)
    body = t + cog + bolts + f'<g transform="translate(256 268) scale(.66)">{a}{spots}</g>'
    return svg(body, defs, "OxidANT: a rusted ant inside a gear")


def webdavclient() -> str:
    base = "#0e2648"
    defs, t = tile(base, "#173a6b")
    cloud = (
        '<g fill="#dce9ff"><circle cx="196" cy="140" r="50"/><circle cx="262" cy="112" r="66"/>'
        '<circle cx="330" cy="146" r="46"/><rect x="146" y="140" width="230" height="56" rx="28"/>'
        "</g>"
    )
    trail = (
        '<path d="M262,206 L262,262" stroke="#dce9ff" stroke-width="9" stroke-linecap="round" '
        'stroke-dasharray="0 20" opacity=".8"/>'
    )
    doc = (
        '<g transform="translate(256 410) rotate(0)">'
        '<path d="M-40,-48 L18,-48 L40,-26 L40,48 L-40,48 Z" fill="#f2a93b"/>'
        '<path d="M18,-48 L18,-26 L40,-26 Z" fill="#c98419"/>'
        '<g stroke="#9a5f0c" stroke-width="6" stroke-linecap="round">'
        '<path d="M-24,-14 L24,-14"/><path d="M-24,4 L24,4"/><path d="M-24,22 L10,22"/></g>'
        "</g>"
    )
    a = ant(MINT, base, k=1.45)
    body = (
        t + cloud + trail + placed(a, "translate(256 304) rotate(180) scale(.42)", base, 16) + doc
    )
    return svg(body, defs, "WebDavClient: an ant carrying a file down from a cloud")


def jotrockenmitlocken() -> str:
    base = "#33163a"
    defs, t = tile(base, "#4d2257")
    curls = "#2ad488"
    curl = "".join(
        f'<circle cx="{x}" cy="{y}" r="{r}"/>'
        for x, y, r in (
            (176, 214, 26),
            (204, 186, 28),
            (238, 172, 28),
            (274, 172, 28),
            (308, 186, 28),
            (336, 214, 26),
            (220, 206, 22),
            (256, 196, 24),
            (292, 206, 22),
        )
    )
    curl_lines = "".join(
        f'<path d="M{x - 10},{y + 2} a10,10 0 1 1 14,4" />'
        for x, y in ((204, 186), (238, 172), (274, 172), (308, 186), (256, 196))
    )
    face = (
        f'<g fill="none" stroke="{MINT}" stroke-linecap="round" stroke-linejoin="round" '
        'stroke-width="15">'
        '<path d="M226,196 L176,150 Q158,128 154,74"/>'
        '<path d="M286,196 L336,150 Q354,128 358,74"/></g>'
        f'<circle cx="154" cy="72" r="13" fill="{MINT}"/>'
        f'<circle cx="358" cy="72" r="13" fill="{MINT}"/>'
        f'<g fill="none" stroke="{curls}" stroke-width="19" stroke-linecap="round">'
        '<path d="M222,394 C210,424 216,448 240,452"/>'
        '<path d="M290,394 C302,424 296,448 272,452"/></g>'
        '<path d="M256,192 C334,192 376,230 376,298 C376,360 326,408 256,410 '
        f'C186,408 136,360 136,298 C136,230 178,192 256,192 Z" fill="{MINT}"/>'
        f'<g fill="{base}"><ellipse cx="160" cy="300" rx="36" ry="49" '
        'transform="rotate(-8 160 300)"/>'
        '<ellipse cx="352" cy="300" rx="36" ry="49" transform="rotate(8 352 300)"/></g>'
        '<g fill="#ffffff"><ellipse cx="171" cy="278" rx="9" ry="13" '
        'transform="rotate(-20 171 278)"/>'
        '<ellipse cx="363" cy="278" rx="9" ry="13" transform="rotate(-20 363 278)"/></g>'
        f'<path d="M220,368 Q256,388 292,368" fill="none" stroke="{base}" stroke-width="7" '
        'stroke-linecap="round" opacity=".5"/>'
        f'<g fill="{curls}">{curl}</g>'
        f'<g fill="none" stroke="{MINT}" stroke-width="5" stroke-linecap="round" opacity=".7">'
        f"{curl_lines}</g>"
    )
    bubble = (
        '<path d="M352,64 L452,64 Q468,64 468,80 L468,128 Q468,144 452,144 L400,144 L382,164 '
        'L384,144 L352,144 Q336,144 336,128 L336,80 Q336,64 352,64 Z" fill="#f5c451"/>'
        f'<g fill="{base}"><circle cx="376" cy="104" r="8"/><circle cx="402" cy="104" r="8"/>'
        '<circle cx="428" cy="104" r="8"/></g>'
    )
    body = t + '<g transform="translate(-18 18) scale(.98)">' + face + "</g>" + bubble
    return svg(body, defs, "jotrockenmitlocken: a curly-haired ant with a speech bubble")


LOGOS: dict[str, Callable[[], str]] = {
    "kataglyphis": kataglyphis,
    "antfrastructure": antfrastructure,
    "orchestrant": orchestrant,
    "modelant": modelant,
    "omniaccelerant": omniaccelerant,
    "accelerantgine": accelerantgine,
    "beschleunigerballett": beschleunigerballett,
    "assetant": assetant,
    "documantation": documantation,
    "anthology": anthology,
    "oxidant": oxidant,
    "webdavclient": webdavclient,
    "jotrockenmitlocken": jotrockenmitlocken,
}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, draw in LOGOS.items():
        (OUT / f"{name}.svg").write_text(draw(), encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
