"""Builds the animated SVGs and clips used by the profile README (drayzu/drayzu).

    python tools/build.py           # SVGs only
    python tools/build.py --clips   # also re-encode the project clips

Fonts are subset and embedded, so the SVGs look the same on GitHub as here.
"""
import base64, io, os, random, struct, sys
from fontTools import subset
from fontTools.ttLib import TTFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = os.path.join(ROOT, 'tools', 'fonts')
OUT = os.path.join(ROOT, 'media')

SERIES = 'ESCALAS'

THEMES = {
    'dark': dict(ink='#ece7db', bg='#0d1117', panel='#0d1117',
                 pot='#ff5b2e', astro='#e3c48a', time='#8fb4ff', civ='#6fe3c1'),
    'light': dict(ink='#1f1d1a', bg='#ffffff', panel='#ffffff',
                  pot='#d6461c', astro='#9a7430', time='#3a64c8', civ='#1f8f73'),
}
CARD = dict(THEMES['dark'], card='#0a0d13')   # teasers are dark cards in both themes

# ------------------------------------------------------------------ fonts
UNICODES = list(range(0x20, 0x7f)) + list(range(0xa0, 0x100)) + [0x2014, 0x2019, 0x2212]

def font_b64(name):
    opts = subset.Options()
    opts.flavor = 'woff2'
    opts.layout_features = ['kern', 'liga']
    opts.name_IDs = []
    f = TTFont(os.path.join(FONTS, name))
    s = subset.Subsetter(opts)
    s.populate(unicodes=UNICODES)
    s.subset(f)
    buf = io.BytesIO()
    f.flavor = 'woff2'
    f.save(buf)
    return base64.b64encode(buf.getvalue()).decode()

FONT_CSS = (
    "@font-face{font-family:S;src:url(data:font/woff2;base64,%s) format('woff2')}"
    "@font-face{font-family:I;src:url(data:font/woff2;base64,%s) format('woff2')}"
    "@font-face{font-family:M;src:url(data:font/woff2;base64,%s) format('woff2');font-weight:100 900}"
) % (font_b64('serif.woff2'), font_b64('serif-italic.woff2'), font_b64('mono.woff2'))

def svg(w, h, label, style, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
            f'role="img" aria-label="{label}"><title>{label}</title>'
            f'<style>{FONT_CSS}{style}</style>{body}</svg>')

def write(name, data):
    with open(os.path.join(OUT, name), 'w', encoding='utf-8', newline='\n') as f:
        f.write(data)
    print(f'  {name:<28} {len(data.encode()) / 1024:6.1f} KB')

# ------------------------------------------------------------------ helpers
def pow10(exp, unit, size, raise_=None):
    """10 with a raised exponent, Potencias style."""
    r = raise_ or round(size * .42)
    e = str(exp).replace('-', '\u2212')
    return (f'10<tspan dy="-{r}" font-size="{round(size * .68)}">{e}</tspan>'
            f'<tspan dy="{r}">{unit}</tspan>')

def arrow(x, y, s, color, sw=1.6):
    """A right arrow drawn as a path (the fonts have no arrows)."""
    return (f'<path d="M{x},{y}h{s}M{x + s - s * .38},{y - s * .32}L{x + s},{y}L{x + s - s * .38},{y + s * .32}" '
            f'fill="none" stroke="{color}" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round"/>')

def enter_key(x, y, color, sw=1.6):
    """The return-key glyph, drawn."""
    return (f'<path d="M{x + 10},{y - 6}v6h-10M{x + 3.5},{y - 3.5}L{x},{y}L{x + 3.5},{y + 3.5}" fill="none" '
            f'stroke="{color}" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round"/>')

def stars(rng, n, x0, y0, x1, y1, color, rmax=1.2):
    out = []
    for _ in range(n):
        out.append(f'<circle class="tw" cx="{rng.uniform(x0, x1):.1f}" cy="{rng.uniform(y0, y1):.1f}" '
                   f'r="{rng.uniform(.35, rmax):.2f}" fill="{color}" '
                   f'style="animation-duration:{rng.uniform(3, 8):.1f}s;animation-delay:-{rng.uniform(0, 8):.1f}s"/>')
    return ''.join(out)

TWINKLE = '.tw{animation:tw ease-in-out infinite alternate}@keyframes tw{from{opacity:.12}to{opacity:.85}}'

# ------------------------------------------------------------------ header
AXES = [  # (accent key, left, right, axis name, project, live)
    ('pot', pow10(-35, ' m', 17), pow10(26, ' m', 17), 'SIZE', 'Potencias', True),
    ('astro', 'a habitat', 'a star, rebuilt', 'WHAT WE COULD BUILD', 'AstroIngeniería', True),
    ('time', pow10(-43, ' s', 17), pow10(100, ' yr', 17), 'TIME', 'Tiempo', False),
    ('civ', 'K 0.7', 'K III', 'CIVILIZATION', 'Civilización', False),
]

def header(t):
    W, H = 1200, 460
    ink = t['ink']
    rng = random.Random(11)
    STEP = 4.0
    TOTAL = STEP * len(AXES)
    vis = 100 / len(AXES)
    x0, x1, ry = 330, 870, 360
    style = (TWINKLE +
             f'.k{{font:400 13px M,monospace;letter-spacing:.42em;fill:{ink};fill-opacity:.5}}'
             f'.it{{opacity:0;animation:it {TOTAL}s linear infinite both}}'
             f'@keyframes it{{0%{{opacity:0}}{vis * .08:.2f}%{{opacity:1}}{vis * .9:.2f}%{{opacity:1}}{vis:.2f}%,100%{{opacity:0}}}}'
             f'.fl{{transform-origin:{x0}px {ry}px;animation:fl {TOTAL}s cubic-bezier(.5,0,.2,1) infinite both}}'
             f'@keyframes fl{{0%{{transform:scaleX(0)}}{vis * .85:.2f}%,100%{{transform:scaleX(1)}}}}'
             f'.dt{{animation:dt {TOTAL}s cubic-bezier(.5,0,.2,1) infinite both}}'
             f'@keyframes dt{{0%{{transform:translateX(0)}}{vis * .85:.2f}%,100%{{transform:translateX({x1 - x0}px)}}}}'
             '.rise{animation:rise 1.4s cubic-bezier(.2,.7,.2,1) both}'
             '@keyframes rise{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:none}}')
    body = [stars(rng, 170, 10, 10, W - 10, H - 10, ink, 1.25)]
    if t is THEMES['dark']:
        body.insert(0, '<defs><radialGradient id="g" cx="50%" cy="45%" r="50%"><stop offset="0" stop-color="#0d1117" stop-opacity=".95"/>'
                       '<stop offset="1" stop-color="#0d1117" stop-opacity="0"/></radialGradient></defs>')
    else:
        body.insert(0, '<defs><radialGradient id="g" cx="50%" cy="45%" r="50%"><stop offset="0" stop-color="#ffffff" stop-opacity=".95"/>'
                       '<stop offset="1" stop-color="#ffffff" stop-opacity="0"/></radialGradient></defs>')
    body.append(f'<ellipse cx="600" cy="215" rx="470" ry="150" fill="url(#g)"/>')
    body.append(f'<text class="k rise" x="600" y="112" text-anchor="middle">DRAYZU \u00b7 {SERIES} \u00b7 A SERIES</text>')
    body.append(f'<text class="rise" x="600" y="222" text-anchor="middle" font-family="S,serif" font-size="100" '
                f'fill="{ink}" style="animation-delay:.15s">Measuring the universe</text>')
    body.append(f'<text class="rise" x="600" y="276" text-anchor="middle" font-family="I,serif" font-style="italic" '
                f'font-size="28" fill="{ink}" fill-opacity=".75" style="animation-delay:.3s">'
                'Interactive pieces about its size, its time, and what we could build in it.</text>')
    # the ruler
    body.append(f'<line x1="{x0}" x2="{x1}" y1="{ry}" y2="{ry}" stroke="{ink}" stroke-opacity=".2"/>')
    for i in range(21):
        x = x0 + (x1 - x0) * i / 20
        hgt = 6 if i % 5 == 0 else 3
        body.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{ry - hgt}" y2="{ry}" stroke="{ink}" stroke-opacity=".3"/>')
    for i, (key, left, right, axis, name, live) in enumerate(AXES):
        c = t[key]
        d = f'animation-delay:{i * STEP:.1f}s'
        status = '' if live else f'<tspan fill="{ink}" fill-opacity=".45"> \u00b7 in progress</tspan>'
        body.append(
            f'<g class="it" style="{d}">'
            f'<line class="fl" style="{d}" x1="{x0}" x2="{x1}" y1="{ry}" y2="{ry}" stroke="{c}" stroke-width="2"/>'
            f'<g class="dt" style="{d}"><circle cx="{x0}" cy="{ry}" r="9" fill="{c}" fill-opacity=".2"/>'
            f'<circle cx="{x0}" cy="{ry}" r="4.5" fill="{c}"/></g>'
            f'<text x="{x0}" y="{ry - 18}" font-family="M,monospace" font-size="17" fill="{ink}" fill-opacity=".6">{left}</text>'
            f'<text x="{x1}" y="{ry - 18}" text-anchor="end" font-family="M,monospace" font-size="17" fill="{ink}" fill-opacity=".6">{right}</text>'
            f'<text x="600" y="{ry + 46}" text-anchor="middle" font-family="M,monospace" font-size="15" letter-spacing="2.5">'
            f'<tspan fill="{c}">{axis}</tspan><tspan fill="{ink}" fill-opacity=".35"> \u00b7 </tspan>'
            f'<tspan fill="{ink}" fill-opacity=".8" font-family="I,serif" font-style="italic" font-size="22" letter-spacing="0">{name}</tspan>{status}</text>'
            '</g>')
    return svg(W, H, f'drayzu — {SERIES}: measuring the universe. Interactive pieces about its size, its time, and what we could build in it.',
               style, ''.join(body))

# ------------------------------------------------------------------ caption under a live clip
def caption(t, key, num, axis, title, tagline, left, right, url):
    W, H = 1200, 200
    ink, c = t['ink'], t[key]
    style = ('.k{animation:k 2.4s ease-in-out infinite}'
             '@keyframes k{0%,80%,100%{transform:translateY(0)}88%{transform:translateY(2px)}}'
             '.p{animation:p 2.6s ease-in-out infinite}@keyframes p{0%,100%{opacity:.2}50%{opacity:.55}}')
    b = []
    b.append(f'<text x="40" y="52" font-family="M,monospace" font-size="13" letter-spacing="4">'
             f'<tspan fill="{c}">{num} \u00b7 {axis}</tspan><tspan fill="{ink}" fill-opacity=".4"> \u00b7 LIVE</tspan></text>')
    b.append(f'<text x="36" y="124" font-family="S,serif" font-size="76" fill="{ink}">{title}</text>')
    b.append(f'<text x="40" y="166" font-family="I,serif" font-style="italic" font-size="25" fill="{ink}" fill-opacity=".72">{tagline}</text>')
    # mini ruler
    rx0, rx1, ry = 720, 1160, 62
    b.append(f'<text x="{rx0}" y="{ry - 16}" font-family="M,monospace" font-size="14" fill="{ink}" fill-opacity=".6">{left}</text>')
    b.append(f'<text x="{rx1}" y="{ry - 16}" text-anchor="end" font-family="M,monospace" font-size="14" fill="{ink}" fill-opacity=".6">{right}</text>')
    b.append(f'<line x1="{rx0}" x2="{rx1}" y1="{ry}" y2="{ry}" stroke="{ink}" stroke-opacity=".25"/>')
    for i in range(17):
        x = rx0 + (rx1 - rx0) * i / 16
        b.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{ry - (6 if i % 4 == 0 else 3)}" y2="{ry}" stroke="{ink}" stroke-opacity=".35"/>')
    b.append(f'<circle class="p" cx="{rx1}" cy="{ry}" r="10" fill="{c}"/><circle cx="{rx1}" cy="{ry}" r="5" fill="{c}"/>')
    # enter pill (same as the project READMEs)
    pw = round(56 + len(url) * 9.75 + 152)
    px, py, ph = 1160 - pw, 104, 60
    b.append(f'<rect x="{px}" y="{py}" width="{pw}" height="{ph}" rx="30" fill="{t["panel"]}" stroke="{ink}" stroke-opacity=".3"/>')
    b.append(arrow(px + 28, py + 30, 15, c))
    b.append(f'<text x="{px + 56}" y="{py + 36}" font-family="M,monospace" font-size="16" letter-spacing=".5" fill="{ink}">{url}</text>')
    b.append(f'<g class="k"><rect x="{px + pw - 128}" y="{py + 12}" width="116" height="36" rx="18" fill="{c}"/>'
             f'<text x="{px + pw - 82}" y="{py + 35}" text-anchor="middle" font-family="M,monospace" font-weight="600" '
             f'font-size="13" letter-spacing="1.5" fill="#0d0b0a">ENTER</text>'
             f'{enter_key(px + pw - 46, py + 33, "#0d0b0a", 1.8)}</g>')
    return svg(W, H, f'{title} — {tagline} Open {url}', style, ''.join(b))

# ------------------------------------------------------------------ divider
def divider(t):
    W, H = 1200, 130
    ink = t['ink']
    b = [f'<line x1="250" x2="470" y1="56" y2="56" stroke="{ink}" stroke-opacity=".2"/>',
         f'<line x1="730" x2="950" y1="56" y2="56" stroke="{ink}" stroke-opacity=".2"/>',
         f'<text x="600" y="61" text-anchor="middle" font-family="M,monospace" font-size="14" letter-spacing="5" fill="{ink}" fill-opacity=".6">NEXT IN THE SERIES</text>',
         f'<text x="600" y="104" text-anchor="middle" font-family="I,serif" font-style="italic" font-size="26" fill="{ink}" fill-opacity=".7">Two more pieces are on their way.</text>']
    return svg(W, H, 'Next in the series: two more pieces are on their way.', '', ''.join(b))

# ------------------------------------------------------------------ teaser cards (600 x 560, dark in both themes)
def card_frame(t, key, num, axis):
    ink, c = t['ink'], t[key]
    return (f'<rect x="1" y="1" width="598" height="558" rx="22" fill="{t["card"]}" stroke="{ink}" stroke-opacity=".14"/>'
            f'<text x="32" y="50" font-family="M,monospace" font-size="13" letter-spacing="4" fill="{c}">{num} \u00b7 {axis}</text>'
            f'<circle class="bl" cx="447" cy="45.5" r="3.5" fill="{c}"/>'
            f'<text x="568" y="50" text-anchor="end" font-family="M,monospace" font-size="12" letter-spacing="3" fill="{ink}" fill-opacity=".5">IN PROGRESS</text>')

def card_text(t, title, sub, meta):
    ink = t['ink']
    return (f'<line x1="32" x2="568" y1="372" y2="372" stroke="{ink}" stroke-opacity=".1"/>'
            f'<text x="28" y="442" font-family="S,serif" font-size="68" fill="{ink}">{title}</text>'
            f'<text x="32" y="482" font-family="I,serif" font-style="italic" font-size="23" fill="{ink}" fill-opacity=".72">{sub}</text>'
            f'<text x="32" y="526" font-family="M,monospace" font-size="13" letter-spacing="1" fill="{ink}" fill-opacity=".45">{meta}</text>')

CARD_CSS = (TWINKLE + '.bl{animation:bl 1.6s steps(1) infinite}@keyframes bl{0%{opacity:1}50%{opacity:.15}}')

def tiempo(t):
    ink, c = t['ink'], t['time']
    rng = random.Random(5)
    D = 10  # seconds per loop
    ax0, ax1, ay = 60, 456, 200

    def half(x):  # half-height of the expanding universe: inflation, then slow, then accelerating
        if x <= 92:
            return 44 * max(x - ax0, 0) / 32
        return 44 + 48 * ((x - 92) / (ax1 - 92)) ** 1.6

    top = ' '.join(f'{x},{ay - half(x):.1f}' for x in range(ax0, ax1 + 1, 4))
    bot = ' '.join(f'{x},{ay + half(x):.1f}' for x in range(ax1, ax0 - 1, -4))
    style = (CARD_CSS +
             f'.bang{{transform-origin:{ax0}px {ay}px;animation:bang {D}s ease-out infinite}}'
             f'@keyframes bang{{0%{{transform:scale(.2);opacity:0}}2%{{opacity:1}}20%{{transform:scale(1.5);opacity:0}}100%{{opacity:0}}}}'
             f'.era{{animation:era {D}s linear infinite}}'
             f'@keyframes era{{0%,24%{{opacity:0}}40%,66%{{opacity:1}}90%,100%{{opacity:.06}}}}')
    b = [card_frame(t, 'time', '03', 'TIME')]
    b.append('<defs><radialGradient id="bg" cx="50%" cy="50%" r="50%"><stop offset="0" stop-color="#ffffff"/>'
             f'<stop offset=".3" stop-color="{c}" stop-opacity=".7"/><stop offset="1" stop-color="{c}" stop-opacity="0"/></radialGradient>'
             '<linearGradient id="tr" x1="0" x2="1"><stop offset="0" stop-color="#ffffff"/>'
             f'<stop offset=".35" stop-color="{c}"/><stop offset=".7" stop-color="#ffb46b"/><stop offset="1" stop-color="#7a2a2a" stop-opacity=".3"/></linearGradient>'
             f'<linearGradient id="cone" gradientUnits="userSpaceOnUse" x1="{ax0}" x2="{ax1}" y1="0" y2="0">'
             f'<stop offset="0" stop-color="#ffffff" stop-opacity=".55"/><stop offset=".12" stop-color="{c}" stop-opacity=".22"/>'
             f'<stop offset=".4" stop-color="{c}" stop-opacity=".07"/><stop offset="1" stop-color="{c}" stop-opacity=".02"/></linearGradient>'
             f'<clipPath id="cc"><polygon points="{top} {bot}"/></clipPath></defs>')
    # the universe, expanding
    b.append(f'<polygon points="{top} {bot}" fill="url(#cone)"/>')
    b.append(f'<polyline points="{top}" fill="none" stroke="{c}" stroke-opacity=".45"/>'
             f'<polyline points="{bot}" fill="none" stroke="{c}" stroke-opacity=".45"/>')
    # the cosmic microwave background, a speckled wall at 380 000 years
    cmb = []
    for _ in range(90):
        y = rng.uniform(ay - half(215), ay + half(215))
        cmb.append(f'<circle cx="{215 + rng.uniform(-3, 3):.1f}" cy="{y:.1f}" r="{rng.uniform(.6, 1.6):.1f}" '
                   f'fill="{rng.choice(["#ffb46b", "#ff7a59", c, "#cfe0ff"])}" opacity="{rng.uniform(.35, .8):.2f}"/>')
    b.append(f'<g clip-path="url(#cc)">{"".join(cmb)}</g>')
    # stars and galaxies are born, then fade at the end of time
    born = []
    for _ in range(110):
        x = rng.uniform(250, ax1 - 4)
        y = ay + rng.uniform(-1, 1) * (half(x) - 5)
        if rng.random() < .14:
            born.append(f'<ellipse cx="{x:.1f}" cy="{y:.1f}" rx="{rng.uniform(3, 6):.1f}" ry="{rng.uniform(1, 2):.1f}" '
                        f'transform="rotate({rng.uniform(-40, 40):.0f} {x:.1f} {y:.1f})" fill="{ink}" opacity=".35"/>')
        else:
            born.append(f'<circle class="tw" cx="{x:.1f}" cy="{y:.1f}" r="{rng.uniform(.4, 1.3):.2f}" fill="{ink}" '
                        f'style="animation-duration:{rng.uniform(3, 7):.1f}s;animation-delay:-{rng.uniform(0, 7):.1f}s"/>')
    b.append(f'<g class="era">{"".join(born)}</g>')
    b.append(f'<circle class="bang" cx="{ax0}" cy="{ay}" r="46" fill="url(#bg)"/>')
    # certainty along the axis: speculative (before), theoretical, observed, theoretical
    seg = lambda x0, x1, dash, op: (f'<line x1="{x0}" x2="{x1}" y1="{ay}" y2="{ay}" stroke="{c}" stroke-opacity="{op}" '
                                    f'stroke-width="2" {dash} stroke-linecap="round"/>')
    b.append(seg(26, ax0 - 6, 'stroke-dasharray="1 6"', .55))
    b.append(seg(ax0, 120, 'stroke-dasharray="6 5"', .75))
    b.append(seg(120, 330, '', .9))
    b.append(seg(330, ax1, 'stroke-dasharray="6 5"', .75))
    ends = [(f'M{ax1},{ay} Q490,{ay} 516,{ay - 54}', 'freeze?', ay - 58),
            (f'M{ax1},{ay} L516,{ay}', 'rip?', ay + 5),
            (f'M{ax1},{ay} Q490,{ay} 516,{ay + 54}', 'crunch?', ay + 68)]
    for d, lab, ly in ends:
        b.append(f'<path d="{d}" fill="none" stroke="{c}" stroke-opacity=".55" stroke-width="2" stroke-dasharray="1 6" stroke-linecap="round"/>'
                 f'<text x="524" y="{ly}" font-family="I,serif" font-style="italic" font-size="17" fill="{ink}" fill-opacity=".6">{lab}</text>')
    # the light that travels through time
    L = ax1 - ax0
    b.append(f'<line x1="{ax0}" x2="{ax1}" y1="{ay}" y2="{ay}" stroke="url(#tr)" stroke-width="2.4" stroke-dasharray="{L} {L}">'
             f'<animate attributeName="stroke-dashoffset" values="{L};0;0;{L}" keyTimes="0;.8;.92;1" dur="{D}s" repeatCount="indefinite"/>'
             f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;.86;.95;1" dur="{D}s" repeatCount="indefinite"/></line>')
    b.append(f'<g><circle r="9" fill="{c}" fill-opacity=".25"/><circle r="3.6" fill="#ffffff"/>'
             f'<animateMotion path="M{ax0},{ay} H{ax1} Q490,{ay} 516,{ay + 54}" keyPoints="0;.8;1;1" keyTimes="0;.8;.9;1" calcMode="linear" dur="{D}s" repeatCount="indefinite"/>'
             f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;.86;.92;1" dur="{D}s" repeatCount="indefinite"/></g>')
    # ticks, below the cone
    ly = ay + half(ax1) + 26
    ticks = [(ax0, pow10(-43, ' s', 12)), (120, '3 min'), (215, '380 kyr'), (330, 'today'), (ax1, pow10(100, ' yr', 12))]
    for x, lab in ticks:
        b.append(f'<line x1="{x}" x2="{x}" y1="{ay + half(x) + 4:.1f}" y2="{ly - 14:.1f}" stroke="{ink}" stroke-opacity=".18" stroke-dasharray="1 3"/>'
                 f'<text x="{x}" y="{ly:.1f}" text-anchor="middle" font-family="M,monospace" font-size="12" fill="{ink}" fill-opacity=".55">{lab}</text>')
    b.append(f'<text x="330" y="{ay - 12}" text-anchor="middle" font-family="M,monospace" font-size="11" letter-spacing="2" fill="{c}">YOU ARE HERE</text>'
             f'<line x1="330" x2="330" y1="{ay - 8}" y2="{ay - 2}" stroke="{c}"/>')
    # legend
    lg = [('', 'observed'), ('stroke-dasharray="6 5"', 'theoretical'), ('stroke-dasharray="1 6"', 'speculative')]
    for i, (dash, lab) in enumerate(lg):
        x = 60 + i * 168
        b.append(f'<line x1="{x}" x2="{x + 28}" y1="{ly + 26:.0f}" y2="{ly + 26:.0f}" stroke="{c}" stroke-width="2" {dash} stroke-linecap="round"/>'
                 f'<text x="{x + 38}" y="{ly + 30:.0f}" font-family="M,monospace" font-size="12" fill="{ink}" fill-opacity=".55">{lab}</text>')
    b.append(card_text(t, 'Tiempo', 'From before the Big Bang to the last light.',
                       f'{pow10(-43, " s", 13)}  —  {pow10(100, " yr", 13)}  ·  coming soon'))
    return svg(600, 560, 'Tiempo — coming soon. From before the Big Bang to the last light: a logarithmic journey through time, '
               'marking what is observed, theoretical and speculative.', style, ''.join(b))

def civilizacion(t):
    ink, c = t['ink'], t['civ']
    rng = random.Random(9)
    D = 14
    cx, cy = 300, 196
    style = CARD_CSS
    b = [card_frame(t, 'civ', '04', 'CIVILIZATION')]
    b.append(stars(rng, 60, 30, 80, 570, 300, ink, 1.1))
    b.append('<defs><radialGradient id="sg" cx="50%" cy="50%" r="50%"><stop offset="0" stop-color="#ffd48a" stop-opacity=".55"/>'
             '<stop offset=".4" stop-color="#ff8a3a" stop-opacity=".18"/><stop offset="1" stop-color="#ff8a3a" stop-opacity="0"/></radialGradient>'
             '<radialGradient id="sc" cx="45%" cy="42%" r="55%"><stop offset="0" stop-color="#fff6df"/><stop offset=".45" stop-color="#ffc56b"/>'
             '<stop offset="1" stop-color="#e0642a"/></radialGradient></defs>')
    # the star dims as the swarm captures its light
    b.append(f'<circle cx="{cx}" cy="{cy}" r="120" fill="url(#sg)">'
             f'<animate attributeName="opacity" values="1;.3;.3;1" keyTimes="0;.8;.93;1" dur="{D}s" repeatCount="indefinite"/></circle>')
    b.append(f'<circle cx="{cx}" cy="{cy}" r="30" fill="url(#sc)"/>')
    orbits = [(-16, 128, 34, 11), (24, 112, 30, 14), (72, 100, 26, 17)]
    panels = []
    for oi, (rot, rx, ry, dur) in enumerate(orbits):
        path = f'M{cx - rx},{cy} a{rx},{ry} 0 1,0 {2 * rx},0 a{rx},{ry} 0 1,0 {-2 * rx},0'
        b.append(f'<g transform="rotate({rot} {cx} {cy})"><path d="{path}" fill="none" stroke="{ink}" stroke-opacity=".09"/></g>')
        for k in range(16):
            panels.append((rot, path, dur, -dur * k / 16))
    rng.shuffle(panels)
    n = len(panels)
    for i, (rot, path, dur, begin) in enumerate(panels):
        tk = .04 + .74 * i / n
        b.append(f'<g transform="rotate({rot} {cx} {cy})"><rect x="-4" y="-1.6" width="8" height="3.2" rx=".8" fill="{c}" opacity="0">'
                 f'<animateMotion path="{path}" dur="{dur}s" begin="{begin:.2f}s" rotate="auto" repeatCount="indefinite"/>'
                 f'<animate attributeName="opacity" values="0;0;.95;.95;0" keyTimes="0;{tk:.3f};{tk + .02:.3f};.93;1" dur="{D}s" repeatCount="indefinite"/>'
                 '</rect></g>')
    # Kardashev meter
    kx0, kx1, ky = 120, 480, 318
    marks = [(120, '0.7'), (230, 'I'), (355, 'II'), (480, 'III')]
    b.append(f'<text x="32" y="{ky + 4}" font-family="M,monospace" font-size="11" letter-spacing="2" fill="{ink}" fill-opacity=".5">KARDASHEV</text>')
    b.append(f'<line x1="{kx0}" x2="{kx1}" y1="{ky}" y2="{ky}" stroke="{ink}" stroke-opacity=".2"/>')
    for x, lab in marks:
        b.append(f'<line x1="{x}" x2="{x}" y1="{ky - 5}" y2="{ky + 5}" stroke="{ink}" stroke-opacity=".4"/>'
                 f'<text x="{x}" y="{ky + 24}" text-anchor="middle" font-family="M,monospace" font-size="12" fill="{ink}" fill-opacity=".55">{lab}</text>')
    b.append(f'<line x1="{kx0}" x2="{kx0}" y1="{ky}" y2="{ky}" stroke="{c}" stroke-width="2.4" stroke-linecap="round">'
             f'<animate attributeName="x2" values="{kx0};372;372;{kx0}" keyTimes="0;.8;.93;1" dur="{D}s" repeatCount="indefinite"/></line>')
    b.append(f'<circle cx="{kx0}" cy="{ky}" r="4.5" fill="{c}">'
             f'<animate attributeName="cx" values="{kx0};372;372;{kx0}" keyTimes="0;.8;.93;1" dur="{D}s" repeatCount="indefinite"/></circle>')
    b.append(card_text(t, 'Civilización', 'Watch a civilization outgrow its planet.',
                       'AstroIngeniería, made visible  \u00b7  coming soon'))
    return svg(600, 560, 'Civilización — coming soon. AstroIngeniería made visible: a civilization climbs the Kardashev scale '
               'while a Dyson swarm gathers around its star.', style, ''.join(b))

# ------------------------------------------------------------------ footer: the series as a line of stations
def footer(t):
    W, H = 1200, 240
    ink = t['ink']
    style = ('.ring{animation:ring 2.8s ease-out infinite;transform-box:fill-box;transform-origin:center}'
             '@keyframes ring{0%{transform:scale(.6);opacity:.9}100%{transform:scale(2.2);opacity:0}}')
    xs = [150, 450, 750, 1050]
    ly = 106
    b = [f'<text x="600" y="46" text-anchor="middle" font-family="M,monospace" font-size="13" letter-spacing="5" fill="{ink}" fill-opacity=".55">'
         f'{SERIES} \u00b7 2 OF 4 LIVE</text>',
         f'<line x1="{xs[0]}" x2="{xs[1]}" y1="{ly}" y2="{ly}" stroke="{ink}" stroke-opacity=".35"/>',
         f'<line x1="{xs[1]}" x2="{xs[3]}" y1="{ly}" y2="{ly}" stroke="{ink}" stroke-opacity=".25" stroke-dasharray="3 6"/>']
    names = [('pot', 'Potencias', 'size', True), ('astro', 'AstroIngeniería', 'what we could build', True),
             ('time', 'Tiempo', 'time', False), ('civ', 'Civilización', 'civilization', False)]
    for x, (key, name, axis, live) in zip(xs, names):
        c = t[key]
        if live:
            b.append(f'<circle cx="{x}" cy="{ly}" r="15" fill="{c}" fill-opacity=".18"/><circle cx="{x}" cy="{ly}" r="7" fill="{c}"/>')
        else:
            b.append(f'<circle class="ring" cx="{x}" cy="{ly}" r="8" fill="none" stroke="{c}"/>'
                     f'<circle cx="{x}" cy="{ly}" r="7" fill="{t["bg"]}" stroke="{c}" stroke-width="2"/>')
        soon = '' if live else ' \u00b7 SOON'
        b.append(f'<text x="{x}" y="{ly + 50}" text-anchor="middle" font-family="S,serif" font-size="30" fill="{ink}" fill-opacity="{1 if live else .7}">{name}</text>'
                 f'<text x="{x}" y="{ly + 76}" text-anchor="middle" font-family="M,monospace" font-size="12" letter-spacing="1.5" fill="{c}">'
                 f'{axis.upper()}{soon}</text>')
    b.append(f'<text x="600" y="{H - 10}" text-anchor="middle" font-family="I,serif" font-style="italic" font-size="20" fill="{ink}" fill-opacity=".5">'
             'The full collection is coming to drayzu.github.io</text>')
    return svg(W, H, f'{SERIES}, a series in four pieces: Potencias and AstroIngeniería are live; Tiempo and Civilización are coming soon.',
               style, ''.join(b))

# ------------------------------------------------------------------ clips
def webp_durations(path):
    b = open(path, 'rb').read()
    i, out = 12, []
    while i < len(b):
        tag, n = b[i:i + 4], struct.unpack('<I', b[i + 4:i + 8])[0]
        if tag == b'ANMF':
            out.append(int.from_bytes(b[i + 8 + 12:i + 8 + 15], 'little'))
        i += 8 + n + (n & 1)
    return out

def clip(src, dst, keep_every=2, quality=72):
    from PIL import Image
    im = Image.open(src)
    durs = webp_durations(src)
    frames, out_d = [], []
    for k in range(0, im.n_frames, keep_every):
        im.seek(k)
        frames.append(im.convert('RGBA').copy())
        out_d.append(sum(durs[k:k + keep_every]))
    frames[0].save(os.path.join(OUT, dst), save_all=True, append_images=frames[1:], duration=out_d,
                   loop=0, quality=quality, method=6)
    print(f'  {dst:<28} {os.path.getsize(os.path.join(OUT, dst)) / 1e6:6.2f} MB  ({len(frames)} frames)')

CLIPS = {
    'potencias-{t}.webp': r'E:/Proyectos/ChatGPT/potencias/docs/media/hero-{t}-v3.webp',
    'astroingenieria-{t}.webp': os.path.join(ROOT, 'tools', 'src', 'astro-hero-{t}.webp'),
}

if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    for name, t in THEMES.items():
        write(f'header-{name}.svg', header(t))
        write(f'potencias-{name}.svg', caption(t, 'pot', '01', 'SIZE', 'Potencias', 'Everything is made of something smaller.',
                                               pow10(-35, ' m', 14), pow10(26, ' m', 14), 'drayzu.github.io/Potencias'))
        write(f'astroingenieria-{name}.svg', caption(t, 'astro', '02', 'WHAT WE COULD BUILD', 'AstroIngeniería',
                                                     'From orbital habitats to rebuilt stars.', 'a habitat', 'a star, rebuilt',
                                                     'drayzu.github.io/AstroIngenieria'))
        write(f'next-{name}.svg', divider(t))
        write(f'series-{name}.svg', footer(t))
    write('tiempo.svg', tiempo(CARD))
    write('civilizacion.svg', civilizacion(CARD))
    if '--clips' in sys.argv:
        for dst, src in CLIPS.items():
            for th in ('dark', 'light'):
                clip(src.format(t=th), dst.format(t=th))
