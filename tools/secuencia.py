"""Prototype: the whole series as one animated WebP that plays the four pieces in sequence.

    python tools/secuencia.py        ->  media/serie.avif, serie.webp and link-*.svg (the published README)

Every piece plays footage of its own site, from the frames each one records for its README.
(The WebGL scenes in tools/escenas/escena.html, captured with headless Chrome by scene_media, stood in for the
pieces before they were out; --fresh recaptures them.)
Everything is composed with Pillow at 1840 px and encoded by ffmpeg as AVIF (media/serie.avif), with a
lighter WebP (media/serie.webp) for browsers without AVIF.
"""
import base64, importlib.util, io, json, os, socket, subprocess, tempfile, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('build', os.path.join(HERE, 'build.py'))
B = importlib.util.module_from_spec(spec)
spec.loader.exec_module(B)

from PIL import Image, ImageChops, ImageDraw
import math
import numpy as np
from PIL import ImageFilter
import websocket

OUT = os.path.dirname(HERE)
CHROME = r'C:/Program Files/Google/Chrome/Application/chrome.exe'
T = B.CARD
INK, BG = T['ink'], T['card']
W, H = 1000, 900                           # layout units
MX, MY, MW, MH = 20, 318, 960, 440        # media box
Z = 1.84                                   # px per unit: 1840 px wide, about twice the README column, sharp on HiDPI screens
CW, CH = round(W * Z), round(H * Z)
MXp, MYp, MWp, MHp = (round(v * Z) for v in (MX, MY, MW, MH))
SCENE_FPS = 30
TICK = 60                                  # frames are fed to ffmpeg on a 60 per second clock
XFADE_S = .45                              # seconds of crossfade between pieces
AVIF_CRF, AVIF_PRESET = 35, 5
WEBP_W, WEBP_Q = 920, 55                   # fallback for browsers without AVIF

# ------------------------------------------------------------------ headless chrome
class Chrome:
    def __init__(self):
        self.tmp = tempfile.mkdtemp(prefix='chrome-')
        with socket.socket() as s_:
            s_.bind(('127.0.0.1', 0))
            port = s_.getsockname()[1]
        self.proc = subprocess.Popen([CHROME, '--headless=new', f'--remote-debugging-port={port}', f'--user-data-dir={self.tmp}',
                                      '--hide-scrollbars', '--force-color-profile=srgb', 'about:blank'],
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(100):
            try:
                tabs = json.load(urllib.request.urlopen(f'http://127.0.0.1:{port}/json'))
                page = next(t for t in tabs if t['type'] == 'page')
                break
            except Exception:
                time.sleep(.1)
        self.ws = websocket.create_connection(page['webSocketDebuggerUrl'], suppress_origin=True)
        self.n = 0

    def call(self, method, **params):
        self.n += 1
        self.ws.send(json.dumps({'id': self.n, 'method': method, 'params': params}))
        while True:
            msg = json.loads(self.ws.recv())
            if msg.get('id') == self.n:
                if 'error' in msg:
                    raise RuntimeError(msg['error'])
                return msg.get('result', {})

    def js(self, expr):
        return self.call('Runtime.evaluate', expression=expr, awaitPromise=True, returnByValue=True)['result'].get('value')

    def close(self):
        self.ws.close()
        self.proc.kill()

# ------------------------------------------------------------------ layout (in 1000 x 900 units, drawn at Z px per unit)
def font(name, size):
    return B.pil_font(name, round(size * Z))

mono = font('mono.woff2', 14)
mono_s = font('mono.woff2', 15)
mono_k = font('mono.woff2', 15)
mono_p = font('mono.woff2', 15)
serif_t = font('serif.woff2', 66)
serif_n = font('serif.woff2', 25)
serif_h = font('serif.woff2', 58)
italic_s = font('serif-italic.woff2', 23)
italic_h = font('serif-italic.woff2', 25)

def spaced(d, xy, text, font, fill, sp=0.0, anchor='l'):
    """Letter-spaced text; xy and sp in layout units."""
    x, y = xy[0] * Z, xy[1] * Z
    sp *= Z
    width = sum(font.getlength(c) + sp for c in text) - sp
    if anchor == 'r':
        x -= width
    elif anchor == 'm':
        x -= width / 2
    for c in text:
        d.text((x, y), c, font=font, fill=fill, anchor='ls')
        x += font.getlength(c) + sp
    return x

XS = [170, 390, 610, 830]
LY = 236

PIECES = [  # station index, title, tagline, live (the Atlas, the series' library, is a link under the sequence)
    dict(i=0, title='Espacio', tagline='From a quark to the edge of everything.', live=True, url='drayzu.github.io/Espacio'),
    dict(i=1, title='Tiempo', tagline='From before the Big Bang to the last light.', live=True, url='drayzu.github.io/Tiempo'),
    dict(i=2, title='Destino', tagline='From one thought to all we could ever build.', live=True, url='drayzu.github.io/Destino'),
    dict(i=3, title='Infinito', tagline='Beyond the last thing we could know.', live=True, url='drayzu.github.io/Infinito'),
]

class Header:
    """The kicker, HORIZONTES cut by a line of light (the lower half of the letters dim, as if below the horizon)
    and the line under it, drawn per frame over the top of the card: at the start of each loop the line lights up
    and the letters rise one by one from behind it, then the line; afterwards a slow glint runs along it now and then."""
    SIZE, SP, BASE = 80, 20, 142           # title, in layout units
    LINE_X = (30, 970)
    TAG = ('Everything, from here.', 24, .72, 184)  # text, size, opacity, baseline
    GLINT_EVERY, GLINT_S, GLINT_W = 9.0, 2.6, 60

    def __init__(self):
        self.f = font('serif.woff2', self.SIZE)
        self.cap = -self.f.getbbox('H', anchor='ls')[1] / Z
        self.hy = self.BASE - self.cap * .30
        self.HH = round(205 * Z)
        Y, depth = round(self.hy * Z), round(self.cap * .45 * Z)
        rows = np.zeros(self.HH, np.float32)
        rows[:Y] = 1
        k = np.arange(depth)
        rows[Y:Y + depth] = .32 * (1 - k / depth) ** 1.4
        self.rows = rows[:, None]
        xs = []
        x = W / 2 - (sum(self.f.getlength(c) / Z + self.SP for c in B.SERIES) - self.SP) / 2
        for c in B.SERIES:
            xs.append(x)
            x += self.f.getlength(c) / Z + self.SP
        self.xs = xs
        # the line and its glow, as alpha maps
        line = Image.new('L', (CW, self.HH), 0)
        d = ImageDraw.Draw(line)
        X0, X1 = round(self.LINE_X[0] * Z), round(self.LINE_X[1] * Z)
        for px in range(X0, X1):
            v = math.sin(math.pi * (px - X0) / (X1 - X0)) ** 1.6
            d.line((px, Y, px, Y + max(1, round(Z * .9)) - 1), fill=round(255 * v))
        glow = line.filter(ImageFilter.GaussianBlur(9 * Z)).point(lambda p: min(255, p * 3))
        self.line = np.asarray(line, np.float32) / 255
        self.glow = np.asarray(glow, np.float32) / 255 * .55
        self.xu = np.arange(CW, dtype=np.float32) / Z
        self.ink = np.array(B.rgba(INK)[:3], np.float32)
        self.static = None

    @staticmethod
    def ease(u):
        u = min(1.0, max(0.0, u))
        return 1 - (1 - u) ** 3

    def letters(self, t):
        rise = [self.ease((t - .4 - i * .09) / 1.1) for i in range(len(B.SERIES))]
        if min(rise) >= 1 and self.static is not None:
            return self.static
        im = Image.new('L', (CW, self.HH), 0)
        d = ImageDraw.Draw(im)
        for x, c, r in zip(self.xs, B.SERIES, rise):
            d.text((round(x * Z), round((self.BASE + (1 - r) * (self.cap + 6)) * Z)), c, font=self.f, fill=255, anchor='ls')
        a = np.asarray(im, np.float32) / 255 * self.rows
        if min(rise) >= 1:
            self.static = a
        return a

    def draw(self, fr, t, tg):
        """fr: the frame (RGB, modified in place); t: seconds since the loop began; tg: the same, for the glint."""
        top = np.asarray(fr.crop((0, 0, CW, self.HH)), np.float32)
        def over(a):
            nonlocal top
            top = top * (1 - a[..., None]) + self.ink * a[..., None]
        g = np.full(CW, .9 * self.ease(t / .6), np.float32)
        u = (tg % self.GLINT_EVERY) / self.GLINT_S
        if 0 < u < 1 and tg > self.GLINT_EVERY / 2:
            gx = self.LINE_X[0] + (self.LINE_X[1] - self.LINE_X[0]) * u
            g = g + 1.1 * np.sin(math.pi * u) * np.exp(-((self.xu - gx) / self.GLINT_W) ** 2)
        over(np.clip(self.glow * g, 0, 1))
        over(np.clip(self.line * g, 0, 1))
        over(self.letters(t))
        fr.paste(Image.fromarray(top.round().astype(np.uint8)), (0, 0))
        d = ImageDraw.Draw(fr)
        spaced(d, (W / 2, 46), 'DRAYZU · A SERIES', mono_k, B.rgba(INK, .6), 4.5, 'm')
        text, size, alpha, y = self.TAG
        a = self.ease((t - 2.3) / .9)
        if a > 0:
            d.text((round(W / 2 * Z), round(y * Z)), text, font=font('serif-italic.woff2', size), fill=B.rgba(INK, alpha * a), anchor='ms')
        return fr

def chrome_layer(active, progress):
    """Everything but the media: header, the line of stations (active one lit, with a progress ring) and the caption."""
    S = 2 * Z  # shapes are supersampled
    def r(*v):
        return tuple(round(x * S) for x in v)
    im = Image.new('RGBA', (round(W * S), round(H * S)), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    lw = max(1, round(S))
    d.rounded_rectangle(r(1, 1, W - 2, H - 2), radius=round(18 * S), fill=B.rgba(BG), outline=B.rgba(INK, .14), width=2 * lw)
    # line
    last_live = max(k for k, s in enumerate(B.STATIONS) if s[3])
    d.line(r(XS[0], LY, XS[last_live], LY), fill=B.rgba(INK, .32), width=lw)
    x = XS[last_live]
    while x < XS[-1]:
        d.line(r(x, LY, min(x + 3, XS[-1]), LY), fill=B.rgba(INK, .28), width=lw)
        x += 9
    for k, (key, name, axis, live) in enumerate(B.STATIONS):
        c = T[key]
        cx, cy = XS[k], LY
        if k == active:
            d.ellipse(r(cx - 17, cy - 17, cx + 17, cy + 17), outline=B.rgba(INK, .14), width=lw)
            d.arc(r(cx - 17, cy - 17, cx + 17, cy + 17), -90, -90 + 360 * progress, fill=B.rgba(c), width=2 * lw)
        if live:
            d.ellipse(r(cx - 13, cy - 13, cx + 13, cy + 13), fill=B.rgba(c, .18))
            d.ellipse(r(cx - 6, cy - 6, cx + 6, cy + 6), fill=B.rgba(c))
        else:
            d.ellipse(r(cx - 6, cy - 6, cx + 6, cy + 6), fill=B.rgba(BG), outline=B.rgba(c), width=2 * lw)
    im = im.resize((CW, CH), Image.LANCZOS)
    d = ImageDraw.Draw(im)
    def z(*v):
        return tuple(round(x * Z) for x in v)
    for k, (key, name, axis, live) in enumerate(B.STATIONS):
        on = k == active
        d.text(z(XS[k], LY + 44), name, font=serif_n, fill=B.rgba(INK, .95 if on else .6), anchor='ms')
        if on:  # only the piece on screen asks its question
            spaced(d, (XS[k], LY + 68), axis.upper(), mono_s, B.rgba(T[key]), 1.5, 'm')
    # caption under the media
    p = PIECES[active]
    c = T[B.STATIONS[active][0]]
    w1, w2 = max(1, round(Z)), max(2, round(2 * Z))
    d.text(z(32, H - 66), p['title'], font=serif_h, fill=B.rgba(INK), anchor='ls')
    d.text(z(36, H - 30), p['tagline'], font=italic_h, fill=B.rgba(INK, .8), anchor='ls')
    py0, py1, px1 = H - 104, H - 48, W - 36
    if p['live']:
        # Only the address, quietly: an image on GitHub is a single link, so no button here pretends
        # to be one (the real links are the pills under the sequence).
        ay = (py0 + py1) / 2
        tw = mono_p.getlength(p['url']) / Z
        x0 = px1 - tw - 22
        d.line(z(x0, ay, x0 + 13, ay), fill=B.rgba(c, .8), width=w2)
        d.line(z(x0 + 8, ay - 5, x0 + 13, ay, x0 + 8, ay + 5), fill=B.rgba(c, .8), width=w2, joint='curve')
        d.text(z(x0 + 22, ay + 5), p['url'], font=mono_p, fill=B.rgba(INK, .55), anchor='ls')
    else:
        label = 'IN PROGRESS'
        pw = round(mono.getlength(label) / Z + 2 * len(label) + 64)
        px0 = px1 - pw
        d.rounded_rectangle(z(px0, py0, px1, py1), radius=round(28 * Z), fill=B.rgba(BG), outline=B.rgba(INK, .22), width=w1)
        ay = (py0 + py1) / 2
        d.ellipse(z(px0 + 24, ay - 4, px0 + 32, ay + 4), fill=B.rgba(c))
        spaced(d, (px0 + 44, ay + 5), label, mono, B.rgba(INK, .7), 2)
    return Image.alpha_composite(Image.new('RGBA', im.size, B.rgba(BG)), im).convert('RGB')  # the corners outside the card are the page

def feather():
    mask = Image.new('L', (MWp, MHp), 255)
    md = ImageDraw.Draw(mask)
    n = round(40 * Z)
    for i in range(n):
        md.rectangle((i, i, MWp - 1 - i, MHp - 1 - i), outline=round(255 * (i / n) ** 1.5))
    return mask

MASK = feather()
DARK = Image.new('RGB', (MWp, MHp), B.rgba(BG)[:3])

# ------------------------------------------------------------------ the media of each piece: [(loader -> RGB MWp x MHp, ms)]
def live_media(name):
    """A live piece's hero clip (its own frame rate), cropped to the media box and scaled up to it."""
    p = B.LIVE[name]
    src = Image.open(p['src'])
    durs = B.webp_durations(p['src'])
    a, z = p['frames']
    z = z or src.n_frames
    def load(k):
        src.seek(k)
        fr = src.convert('RGB')
        if p['crop']:
            fr = fr.crop((0, p['crop'][0], fr.width, p['crop'][1]))
        fr = fr.resize((round(fr.width * Z), round(fr.height * Z)), Image.LANCZOS)
        box = DARK.copy()
        box.paste(fr, ((MWp - fr.width) // 2, (MHp - fr.height) // 2))
        return box
    return [((lambda k=k: load(k)), durs[k]) for k in range(a, z)]

# Tiempo's README hero, captured from the site (tiempo/tools/src/frames/hero, 1280 x 720 JPG at 30 fps):
# one scroll from the Milky Way assembling to the Sun being born, the Earth and now.
TIEMPO_FRAMES = r'E:/Proyectos/ChatGPT/tiempo/tools/src/frames/hero'

def tiempo_media(first=24, last=312):
    fade = round(SCENE_FPS * .27)
    def load(i):
        fr = Image.open(os.path.join(TIEMPO_FRAMES, f'{i:04d}.jpg')).convert('RGB')
        h = round(fr.width * MH / MW)
        y0 = (fr.height - h) // 2
        fr = fr.crop((0, y0, fr.width, y0 + h)).resize((MWp, MHp), Image.LANCZOS)
        # screen over the card: its black becomes the card, so the box has no edge
        fr = ImageChops.screen(fr, DARK)
        if i > last - fade:
            fr = Image.blend(fr, DARK, (i - (last - fade)) / (fade + 1))
        return fr
    return [((lambda i=i: load(i)), 1000 / SCENE_FPS) for i in range(first, last + 1)]

def footage(load_rgb, count, fade_in=0):
    """Real footage (RGB frames at 30 fps), cropped to the media box and screened over the card."""
    fade = round(SCENE_FPS * .27)
    def load(i):
        fr = load_rgb(i)
        h = round(fr.width * MH / MW)
        if h <= fr.height:
            y0 = (fr.height - h) // 2
            fr = fr.crop((0, y0, fr.width, y0 + h))
        else:
            w = round(fr.height * MW / MH)
            x0 = (fr.width - w) // 2
            fr = fr.crop((x0, 0, x0 + w, fr.height))
        fr = ImageChops.screen(fr.resize((MWp, MHp), Image.LANCZOS), DARK)
        if i >= count - fade:
            fr = Image.blend(fr, DARK, (i - (count - fade) + 1) / (fade + 1))
        return fr
    return [((lambda i=i: load(i)), 1000 / SCENE_FPS) for i in range(count)]

def espacio_media():
    """Espacio's README hero, from its captured frames (one scroll: a cell to the Earth)."""
    d = r'E:/Proyectos/ChatGPT/potencias/tools/src/frames/hero'
    return footage(lambda i: Image.open(os.path.join(d, f'{i:04d}.jpg')).convert('RGB'), 270)

DESTINO_FRAMES = r'E:/Proyectos/ChatGPT/civilizacion/tools/readme'

def destino_media(clips=('hero1', 'hero4', 'hero5'), join=10):
    """Destino's README hero (its own captured flights, 1840 x 1035 JPG at 30 fps): the swarm around the Sun,
    a star being taken apart and the black hole, each fading into the next over `join` frames."""
    ns = [len([f for f in os.listdir(os.path.join(DESTINO_FRAMES, c)) if f.endswith('.jpg')]) for c in clips]
    seq = []
    for k, (c, n) in enumerate(zip(clips, ns)):
        start = join if k else 0
        last = k == len(clips) - 1
        for i in range(start, n if last else n - join):
            seq.append(((c, i), None, 0))
        if not last:
            for i in range(join):
                seq.append(((c, n - join + i), (clips[k + 1], i), (i + 1) / (join + 1)))
    img = lambda ci: Image.open(os.path.join(DESTINO_FRAMES, ci[0], f'{ci[1]:04d}.jpg')).convert('RGB')
    def rgb(i):
        a, b, w = seq[i]
        return Image.blend(img(a), img(b), w) if b else img(a)
    return footage(rgb, len(seq))

def infinito_media():
    """Infinito's README hero (tools/readme/hero, 1840 x 1035 JPG at 30 fps): a point of light becomes the thread
    of your life, splits at every choice and grows into the tree of all your lives."""
    d = r'E:/Proyectos/ChatGPT/infinito/tools/readme/hero'
    n = len([f for f in os.listdir(d) if f.endswith('.jpg')])
    return footage(lambda i: Image.open(os.path.join(d, f'{i:04d}.jpg')).convert('RGB'), n)

def astro_media():
    """AstroIngeniería's Dyson sphere being built, recorded from its own site with the interface hidden
    (tools/escenas/astro_dyson.py: 3200 x 1720 PNG at 30 fps). The site keeps the sphere high, so the
    frame is anchored at the top."""
    folder = os.path.join(HERE, 'src', 'astro-dyson')
    n = len([f for f in os.listdir(folder) if f.endswith('.png')])
    def rgb(i):
        fr = Image.open(os.path.join(folder, f'{i:04d}.png')).convert('RGB')
        return fr.crop((0, 0, fr.width, round(fr.width * MH / MW)))
    return footage(rgb, n)

def scene_media(chrome, piece, seconds, fresh=False):
    """The WebGL scenes in tools/escenas/escena.html, captured once into tools/src/escenas/ (a PNG per frame)."""
    n = round(seconds * SCENE_FPS)
    folder = os.path.join(HERE, 'src', 'escenas', f'{piece}-{MWp}x{MHp}-{SCENE_FPS}')
    have = len([f for f in os.listdir(folder) if f.endswith('.png')]) if os.path.isdir(folder) else 0
    if fresh is True or piece in (fresh or ()) or have != n:
        spec = importlib.util.spec_from_file_location('capturar', os.path.join(HERE, 'escenas', 'capturar.py'))
        cap = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cap)
        os.makedirs(folder, exist_ok=True)
        t0 = time.time()
        cap.scene_frames(chrome, piece, [i / SCENE_FPS for i in range(n)], size=(MWp, MHp), out_dir=folder)
        print(f'  {piece}: {n} frames in {time.time() - t0:.0f} s')
    fade = round(SCENE_FPS * .27)  # fade out the last frames
    def load(i):
        fr = Image.open(os.path.join(folder, f'{i:04d}.png')).convert('RGB')
        if i >= n - fade:
            fr = Image.blend(fr, DARK, (i - (n - fade) + 1) / (fade + 1))
        return fr
    return [((lambda i=i: load(i)), 1000 / SCENE_FPS) for i in range(n)]

# ------------------------------------------------------------------ the links under the sequence (an image on GitHub is one link)
def soon_pill(t, key, name):
    """A piece still in the works: the same pill, quieter, with no way in yet."""
    ink, c = t['ink'], t[key]
    body = (f'<rect x="20" y="16" width="560" height="60" rx="30" fill="{t["panel"]}" stroke="{ink}" stroke-opacity=".22" stroke-dasharray="3 5"/>'
            f'<circle cx="54" cy="46" r="6" fill="none" stroke="{c}" stroke-width="2"/>'
            f'<text x="76" y="56" font-family="S,serif" font-size="30" fill="{ink}" fill-opacity=".7">{name}</text>'
            f'<text x="556" y="52" text-anchor="end" font-family="M,monospace" font-size="16" letter-spacing="1.5" fill="{c}" fill-opacity=".9">SOON</text>')
    return B.svg(600, 92, f'{name}: coming soon', '', body)

def link_pill(t, key, name):
    ink, c = t['ink'], t[key]
    body = (f'<rect x="20" y="16" width="560" height="60" rx="30" fill="{t["panel"]}" stroke="{ink}" stroke-opacity=".3"/>'
            f'<circle cx="54" cy="46" r="6.5" fill="{c}"/>'
            f'<text x="76" y="56" font-family="S,serif" font-size="30" fill="{ink}">{name}</text>'
            f'<text x="532" y="52" text-anchor="end" font-family="M,monospace" font-size="16" letter-spacing="1.5" fill="{ink}" fill-opacity=".8">ENTER</text>'
            f'<path d="M542,46h18M553,39l7,7l-7,7" fill="none" stroke="{c}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>')
    return B.svg(600, 92, f'Enter {name}', '', body)

def atlas_note(t):
    """The Atlas, quietly: a small caption under the pieces, not a piece itself (it is the series' library)."""
    ink, c = t['ink'], t['astro']
    text = 'And to read further, the Atlas →'
    w = B.pil_font('serif-italic.woff2', 26).getlength(text)
    x0 = 600 - (w + 18) / 2
    body = (f'<circle cx="{x0 + 4:.1f}" cy="29" r="4" fill="{c}"/>'
            f'<text x="{x0 + 18:.1f}" y="38" font-family="I,serif" font-style="italic" font-size="26" fill="{ink}" fill-opacity=".8">{text}</text>')
    return B.svg(1200, 58, 'And to read further, the Atlas, the library of the series', '', body)

# ------------------------------------------------------------------ compose
def encode_avif(dst):
    """ffmpeg reads raw frames on a 60 per second clock (each frame repeated for its duration); the repeats are
    dropped again (mpdecimate) so the AVIF keeps each frame's own duration."""
    return subprocess.Popen(
        ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{CW}x{CH}', '-r', str(TICK), '-i', '-',
         '-vf', 'mpdecimate=hi=1:lo=1:frac=0:max=0,scale=out_color_matrix=bt709:out_range=tv,format=yuv420p', '-fps_mode', 'vfr',
         '-color_primaries', 'bt709', '-color_trc', 'iec61966-2-1', '-colorspace', 'bt709', '-color_range', 'tv',
         '-c:v', 'libsvtav1', '-preset', str(AVIF_PRESET), '-crf', str(AVIF_CRF), '-g', '600', '-loop', '0', dst],
        stdin=subprocess.PIPE)

def main():
    import sys
    args = sys.argv[1:]  # --fresh recaptures every scene; --fresh tiempo civilizacion only those
    names = [a for a in args if not a.startswith('-')]
    fresh = (names or True) if '--fresh' in args else False
    os.makedirs(os.path.join(OUT, 'media'), exist_ok=True)
    for th, t in B.THEMES.items():
        open(os.path.join(OUT, 'media', f'atlas-note-{th}.svg'), 'w', encoding='utf-8').write(atlas_note(t))
        for key, slug, name in (('pot', 'espacio', 'Espacio'), ('time', 'tiempo', 'Tiempo'),
                                ('civ', 'destino', 'Destino'), ('inf', 'infinito', 'Infinito')):
            open(os.path.join(OUT, 'media', f'link-{slug}-{th}.svg'), 'w', encoding='utf-8').write(link_pill(t, key, name))
    media = [espacio_media(), tiempo_media(), destino_media(), infinito_media()]

    head = Header()
    def compose(k, img, progress, cache, t=99.0, tg=0.0):
        step = round(24 * progress)
        if step not in cache:
            cache.clear()
            cache[step] = chrome_layer(k, step / 24)
        fr = cache[step].copy()
        fr.paste(img, (MXp, MYp), MASK)
        return head.draw(fr, t, tg)

    print('composing...')
    avif = os.path.join(OUT, 'media', 'serie.avif')
    enc = encode_avif(avif)
    last = compose(len(media) - 1, media[-1][-1][0](), 1, {})  # the loop crossfades from the end back to the start
    webp, webp_durs = [], []
    t0 = 0  # ms since the loop began
    for k, seq in enumerate(media):
        total = sum(ms for _, ms in seq)
        cache, t, prev, wt = {}, 0, last, 0
        xf = round(XFADE_S * 1000 / seq[0][1])
        for i, (load, ms) in enumerate(seq):
            fr = compose(k, load(), t / total, cache, (t0 + t) / 1000, (t0 + t) / 1000)
            if i < xf:
                fr = Image.blend(prev, fr, (i + 1) / (xf + 1))
            ticks = round((t + ms) * TICK / 1000) - round(t * TICK / 1000)
            raw = fr.tobytes()
            for _ in range(ticks):
                enc.stdin.write(raw)
            if t >= wt:  # the WebP fallback, at about 15 frames per second
                webp.append(fr.resize((WEBP_W, round(CH * WEBP_W / CW)), Image.LANCZOS))
                webp_durs.append(0)
                wt += 66
            webp_durs[-1] += ms
            t += ms
            last = fr
        t0 += total
        print(f'  {PIECES[k]["title"]}: {len(seq)} frames')
    enc.stdin.close()
    enc.wait()
    print(f'  serie.avif  {os.path.getsize(avif) / 1e6:.2f} MB  ({CW}x{CH})')
    dst = os.path.join(OUT, 'media', 'serie.webp')
    webp_durs = [round(d) for d in webp_durs]
    webp[0].save(dst, save_all=True, append_images=webp[1:], duration=webp_durs, loop=0, quality=WEBP_Q, method=4)
    print(f'  serie.webp  {os.path.getsize(dst) / 1e6:.2f} MB  ({len(webp)} frames, {sum(webp_durs) / 1000:.1f} s)')

if __name__ == '__main__':
    main()
