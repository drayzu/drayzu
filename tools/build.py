"""Shared pieces of the profile README (drayzu/drayzu): fonts, palette, headline, the series stations.

The published README is the sequence made by tools/secuencia.py. Run on its own, this file
renders the earlier card layout into tools/versiones/tarjetas/media, for comparison:

    python tools/build.py           # SVGs only
    python tools/build.py --clips   # also render the live project cards (animated WebP)

Fonts are subset and embedded, so the SVGs look the same on GitHub as here.
"""
import base64, io, os, random, struct, sys
from fontTools import subset
from fontTools.ttLib import TTFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = os.path.join(ROOT, 'tools', 'fonts')
OUT = os.path.join(ROOT, 'tools', 'versiones', 'tarjetas', 'media')

SERIES = 'HORIZONTES'

THEMES = {
    'dark': dict(ink='#ece7db', bg='#0d1117', panel='#0d1117',
                 pot='#ff5b2e', astro='#e3c48a', time='#8fb4ff', civ='#6fe3c1', inf='#c9b4ff'),
    'light': dict(ink='#1f1d1a', bg='#ffffff', panel='#ffffff',
                  pot='#d6461c', astro='#9a7430', time='#3a64c8', civ='#1f8f73', inf='#6e4fc9'),
}
CARD = dict(THEMES['dark'], card='#0d1117')   # cards are dark in both themes

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

def stars(rng, n, x0, y0, x1, y1, color, rmax=1.2):
    out = []
    for _ in range(n):
        out.append(f'<circle class="tw" cx="{rng.uniform(x0, x1):.1f}" cy="{rng.uniform(y0, y1):.1f}" '
                   f'r="{rng.uniform(.35, rmax):.2f}" fill="{color}" '
                   f'style="animation-duration:{rng.uniform(3, 8):.1f}s;animation-delay:-{rng.uniform(0, 8):.1f}s"/>')
    return ''.join(out)

TWINKLE = '.tw{animation:tw ease-in-out infinite alternate}@keyframes tw{from{opacity:.12}to{opacity:.85}}'

# ------------------------------------------------------------------ header: title + the series as a line of stations
STATIONS = [  # (accent key, name, axis, live)
    ('pot', 'Espacio', 'where?', True),
    ('time', 'Tiempo', 'when?', True),
    ('civ', 'Destino', 'how far?', False),
    ('inf', 'Infinito', "what's beyond?", False),
]

HEADLINE = ('Everything, from here.', 'Interactive pieces about the universe, and our place in it.')

def header(t, headline=HEADLINE):
    title, sub = headline
    ssize = min(28, round(28 * 1080 / pil_font('serif-italic.woff2', 28).getlength(sub)))
    tsize = min(100, round(100 * 1040 / pil_font('serif.woff2', 100).getlength(title)))  # long titles shrink to fit
    W, H = 1200, 470
    ink = t['ink']
    rng = random.Random(11)
    glow = '#0d1117' if t is THEMES['dark'] else '#ffffff'
    style = (TWINKLE +
             f'.k{{font:400 13px M,monospace;letter-spacing:.42em;fill:{ink};fill-opacity:.5}}'
             '.rise{animation:rise 1.4s cubic-bezier(.2,.7,.2,1) both}'
             '@keyframes rise{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:none}}'
             '.ring{animation:ring 2.8s ease-out infinite;transform-box:fill-box;transform-origin:center}'
             '@keyframes ring{0%{transform:scale(.6);opacity:.9}100%{transform:scale(2.4);opacity:0}}'
             '.run{animation:run 6s linear infinite}@keyframes run{to{stroke-dashoffset:-90}}')
    b = [f'<defs><radialGradient id="g" cx="50%" cy="45%" r="50%"><stop offset="0" stop-color="{glow}" stop-opacity=".95"/>'
         f'<stop offset="1" stop-color="{glow}" stop-opacity="0"/></radialGradient></defs>',
         stars(rng, 170, 10, 10, W - 10, H - 10, ink, 1.25),
         f'<ellipse cx="600" cy="205" rx="470" ry="140" fill="url(#g)"/>',
         f'<text class="k rise" x="600" y="100" text-anchor="middle">DRAYZU · {SERIES} · A SERIES</text>',
         f'<text class="rise" x="600" y="208" text-anchor="middle" font-family="S,serif" font-size="{tsize}" '
         f'fill="{ink}" style="animation-delay:.15s">{title}</text>',
         f'<text class="rise" x="600" y="262" text-anchor="middle" font-family="I,serif" font-style="italic" '
         f'font-size="{ssize}" fill="{ink}" fill-opacity=".75" style="animation-delay:.3s">{sub}</text>']
    xs = [210, 470, 730, 990]
    ly = 350
    b.append(f'<line x1="{xs[0]}" x2="{xs[1]}" y1="{ly}" y2="{ly}" stroke="{ink}" stroke-opacity=".35"/>')
    b.append(f'<line class="run" x1="{xs[1]}" x2="{xs[3]}" y1="{ly}" y2="{ly}" stroke="{ink}" stroke-opacity=".3" stroke-dasharray="3 6"/>')
    for x, (key, name, axis, live) in zip(xs, STATIONS):
        c = t[key]
        if live:
            b.append(f'<circle cx="{x}" cy="{ly}" r="14" fill="{c}" fill-opacity=".18"/><circle cx="{x}" cy="{ly}" r="6.5" fill="{c}"/>')
        else:
            b.append(f'<circle class="ring" cx="{x}" cy="{ly}" r="7" fill="none" stroke="{c}"/>'
                     f'<circle cx="{x}" cy="{ly}" r="6.5" fill="{t["bg"]}" stroke="{c}" stroke-width="2"/>')
        soon = ''  # an open circle already says it is not out yet
        b.append(f'<text x="{x}" y="{ly + 46}" text-anchor="middle" font-family="S,serif" font-size="28" fill="{ink}" '
                 f'fill-opacity="{1 if live else .65}">{name}</text>'
                 f'<text x="{x}" y="{ly + 72}" text-anchor="middle" font-family="M,monospace" font-size="11.5" letter-spacing="1.5" fill="{c}">'
                 f'{axis.upper()}{soon}</text>')
    return svg(W, H, f'drayzu — {SERIES}: {title}. {sub} A series in four pieces: Potencias and AstroIngeniería are live; '
               'Tiempo and Civilización are coming soon.', style, ''.join(b))

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

def card_text(t, title, sub):
    ink = t['ink']
    return (f'<line x1="32" x2="568" y1="372" y2="372" stroke="{ink}" stroke-opacity=".1"/>'
            f'<text x="28" y="458" font-family="S,serif" font-size="68" fill="{ink}">{title}</text>'
            f'<text x="32" y="500" font-family="I,serif" font-style="italic" font-size="23" fill="{ink}" fill-opacity=".72">{sub}</text>')

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
    b.append(card_text(t, 'Tiempo', 'From before the Big Bang to the last light.'))
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
    b.append(card_text(t, 'Civilización', 'Watch a civilization outgrow its planet.'))
    return svg(600, 560, 'Civilización — coming soon. AstroIngeniería made visible: a civilization climbs the Kardashev scale '
               'while a Dyson swarm gathers around its star.', style, ''.join(b))

# ------------------------------------------------------------------ live cards: the project clip inside the same card as the teasers
# Rendered as animated WebP (an SVG on GitHub cannot hold a moving clip), dark in both themes like the teasers.
def webp_durations(path):
    b = open(path, 'rb').read()
    i, out = 12, []
    while i < len(b):
        tag, n = b[i:i + 4], struct.unpack('<I', b[i + 4:i + 8])[0]
        if tag == b'ANMF':
            out.append(int.from_bytes(b[i + 8 + 12:i + 8 + 15], 'little'))
        i += 8 + n + (n & 1)
    return out

def pil_font(name, size):
    from PIL import ImageFont
    f = TTFont(os.path.join(FONTS, name))
    f.flavor = None
    buf = io.BytesIO()
    f.save(buf)
    buf.seek(0)
    return ImageFont.truetype(buf, size)

def rgba(hex_, a=1.0, over=None):
    """An opaque colour: hex_ at opacity a over the card (ImageDraw replaces pixels instead of blending)."""
    rgb = lambda h: tuple(int(h.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4))
    fg, bg = rgb(hex_), rgb(over or CARD['card'])
    return tuple(round(f * a + b * (1 - a)) for f, b in zip(fg, bg)) + (255,)

LIVE = {
    'potencias': dict(key='pot', num='01', axis='SIZE', title='Potencias',
                      tagline='Everything is made of something smaller.',
                      url='drayzu.github.io/Potencias',
                      src=r'E:/Proyectos/ChatGPT/potencias/docs/media/hero-dark-v3.webp', frames=(6, None), crop=(50, 490), quality=72),
    'astroingenieria': dict(key='astro', num='02', axis='WHAT WE COULD BUILD', title='AstroIngeniería',
                            tagline='From orbital habitats to rebuilt stars.',
                            url='drayzu.github.io/AstroIngenieria',
                            src=os.path.join(ROOT, 'tools', 'src', 'astro-hero-v5-dark.webp'), frames=(0, 69), crop=None, quality=80),
}

def live_card(name):
    from PIL import Image, ImageDraw
    p = LIVE[name]
    t = CARD
    ink, c, bg = t['ink'], t[p['key']], t['card']
    W, H = 1000, 684
    cx, cy, cw, ch = 20, 66, 960, 440
    mono, mono_s = pil_font('mono.woff2', 13), pil_font('mono.woff2', 15)
    serif, italic = pil_font('serif.woff2', 66), pil_font('serif-italic.woff2', 25)

    def spaced(d, xy, text, font, fill, sp=0.0, anchor_end=False):
        x, y = xy
        width = sum(font.getlength(ch_) + sp for ch_ in text) - sp
        if anchor_end:
            x -= width
        for ch_ in text:
            d.text((x, y), ch_, font=font, fill=fill, anchor='ls')
            x += font.getlength(ch_) + sp
        return x

    def base(dot_on):
        im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        d.rounded_rectangle((1, 1, W - 2, H - 2), radius=18, fill=rgba(bg), outline=rgba(ink, .14), width=2)
        spaced(d, (36, 46), f'{p["num"]} \u00b7 {p["axis"]}', mono, rgba(c), 4)
        x = spaced(d, (964, 46), 'LIVE', mono, rgba(ink, .55), 3.2, anchor_end=True)
        lw = sum(mono.getlength(ch_) + 3.2 for ch_ in 'LIVE') - 3.2
        dx = 964 - lw - 14
        if dot_on:
            d.ellipse((dx - 4, 37.5, dx + 4, 45.5), fill=rgba(c))
        d.line((36, 532, 964, 532), fill=rgba(ink, .1), width=1)
        d.text((32, 604), p['title'], font=serif, fill=rgba(ink), anchor='ls')
        d.text((36, 646), p['tagline'], font=italic, fill=rgba(ink, .72), anchor='ls')
        # enter pill, as in the project READMEs
        pw = round(56 + mono_s.getlength(p['url']) + 156)
        px1, py0 = 964, 570
        px0, py1 = px1 - pw, py0 + 60
        d.rounded_rectangle((px0, py0, px1, py1), radius=30, fill=rgba(bg), outline=rgba(ink, .3), width=1)
        ay = py0 + 30
        d.line((px0 + 26, ay, px0 + 41, ay), fill=rgba(c), width=2)
        d.line((px0 + 35, ay - 5, px0 + 41, ay, px0 + 35, ay + 5), fill=rgba(c), width=2, joint='curve')
        d.text((px0 + 54, ay + 6), p['url'], font=mono_s, fill=rgba(ink), anchor='ls')
        bx0, bx1 = px1 - 128, px1 - 12
        d.rounded_rectangle((bx0, py0 + 12, bx1, py1 - 12), radius=18, fill=rgba(c))
        spaced(d, (bx0 + 18, ay + 5), 'ENTER', pil_font('mono.woff2', 13), rgba('#0d0b0a'), 1.5)
        kx, ky = bx1 - 34, ay + 3
        d.line((kx + 10, ky - 7, kx + 10, ky, kx, ky), fill=rgba('#0d0b0a'), width=2)
        d.line((kx + 4, ky - 4, kx, ky, kx + 4, ky + 4), fill=rgba('#0d0b0a'), width=2)
        im.alpha_composite(lay)
        return im

    bases = (base(True), base(False))
    src = Image.open(p['src'])
    durs = webp_durations(p['src'])
    a, z = p['frames']
    z = z or src.n_frames
    # feathered edges so the clip melts into the card
    mask = Image.new('L', (cw, ch), 255)
    md = ImageDraw.Draw(mask)
    for i in range(40):
        v = round(255 * (i / 40) ** 1.5)
        md.rectangle((i, i, cw - 1 - i, ch - 1 - i), outline=v)
    FADE = 9
    frames, out_d, elapsed = [], [], 0
    for k in range(a, z):
        src.seek(k)
        fr = src.convert('RGB')
        if p['crop']:
            fr = fr.crop((0, p['crop'][0], fr.width, p['crop'][1]))
        clipbox = Image.new('RGB', (cw, ch), rgba(bg)[:3])
        clipbox.paste(fr, (0, (ch - fr.height) // 2))
        left = z - 1 - k
        if left < FADE:  # fade out, so the loop restarts from the dark
            clipbox = Image.blend(Image.new('RGB', (cw, ch), rgba(bg)[:3]), clipbox, left / FADE)
        img = bases[0 if (elapsed // 800) % 2 == 0 else 1].copy()
        img.paste(clipbox, (cx, cy), mask)
        frames.append(img)
        out_d.append(durs[k])
        elapsed += durs[k]
    dst = os.path.join(OUT, f'{name}.webp')
    frames[0].save(dst, save_all=True, append_images=frames[1:], duration=out_d, loop=0,
                   quality=p['quality'], method=4)
    print(f'  {name + ".webp":<28} {os.path.getsize(dst) / 1e6:6.2f} MB  ({len(frames)} frames, {sum(out_d) / 1000:.1f} s)')

if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    for name, t in THEMES.items():
        write(f'header-{name}.svg', header(t))
        write(f'next-{name}.svg', divider(t))
    write('tiempo.svg', tiempo(CARD))
    write('civilizacion.svg', civilizacion(CARD))
    if '--clips' in sys.argv:
        for name in LIVE:
            live_card(name)
