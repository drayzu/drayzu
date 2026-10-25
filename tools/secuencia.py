"""Prototype: the whole series as one animated WebP that plays the four pieces in sequence.

    python tools/secuencia.py        ->  media/serie.avif, serie.webp and link-*.svg (the published README)

Potencias, AstroIngeniería and Tiempo play footage of their own sites; Civilización is a WebGL scene
(tools/escenas/escena.html, after the engine of drayzu.github.io/prototypes/vuelo.html)
rendered frame by frame with headless Chrome at 30 fps (cached in tools/src/escenas; --fresh recaptures them all, --fresh tiempo just that one).
Everything is composed with Pillow at 1840 px and encoded by ffmpeg as AVIF (media/serie.avif), with a
lighter WebP (media/serie.webp) for browsers without AVIF.
"""
import base64, importlib.util, io, json, os, socket, subprocess, tempfile, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('build', os.path.join(HERE, 'build.py'))
B = importlib.util.module_from_spec(spec)
spec.loader.exec_module(B)

from PIL import Image, ImageChops, ImageDraw
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
AVIF_CRF, AVIF_PRESET = 34, 5
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

mono = font('mono.woff2', 13)
mono_s = font('mono.woff2', 11)
mono_p = font('mono.woff2', 14)
serif_t = font('serif.woff2', 66)
serif_n = font('serif.woff2', 23)
serif_h = font('serif.woff2', 58)
italic_s = font('serif-italic.woff2', 23)
italic_h = font('serif-italic.woff2', 23)

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

PIECES = [  # station index, title, tagline, live
    dict(i=0, title='Potencias', tagline='Everything is made of something smaller.', live=True, url='drayzu.github.io/Potencias'),
    dict(i=1, title='AstroIngeniería', tagline='From orbital habitats to rebuilt stars.', live=True, url='drayzu.github.io/AstroIngenieria'),
    dict(i=2, title='Tiempo', tagline='From before the Big Bang to the last light.', live=True, url='drayzu.github.io/Tiempo'),
    dict(i=3, title='Civilización', tagline='Watch a civilization outgrow its planet.', live=False),
]

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
    while x < XS[3]:
        d.line(r(x, LY, min(x + 3, XS[3]), LY), fill=B.rgba(INK, .28), width=lw)
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
    spaced(d, (W / 2, 62), f'DRAYZU · {B.SERIES} · A SERIES', mono, B.rgba(INK, .45), 5.5, 'm')
    title, sub = B.HEADLINE
    d.text(z(W / 2, 140), title, font=serif_t, fill=B.rgba(INK), anchor='ms')
    d.text(z(W / 2, 180), sub, font=italic_s, fill=B.rgba(INK, .72), anchor='ms')
    for k, (key, name, axis, live) in enumerate(B.STATIONS):
        on = k == active
        d.text(z(XS[k], LY + 42), name, font=serif_n, fill=B.rgba(INK, .95 if on else .4), anchor='ms')
        spaced(d, (XS[k], LY + 62), axis.upper() + ('' if live else ' · SOON'), mono_s,
               B.rgba(T[key], 1 if on else .45), 1.5, 'm')
    # caption under the media
    p = PIECES[active]
    c = T[B.STATIONS[active][0]]
    w1, w2 = max(1, round(Z)), max(2, round(2 * Z))
    d.text(z(32, H - 66), p['title'], font=serif_h, fill=B.rgba(INK), anchor='ls')
    d.text(z(36, H - 30), p['tagline'], font=italic_h, fill=B.rgba(INK, .72), anchor='ls')
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
        pw = round(mono.getlength(label) / Z + 3 * len(label) + 64)
        px0 = px1 - pw
        d.rounded_rectangle(z(px0, py0, px1, py1), radius=round(28 * Z), fill=B.rgba(BG), outline=B.rgba(INK, .22), width=w1)
        ay = (py0 + py1) / 2
        d.ellipse(z(px0 + 24, ay - 4, px0 + 32, ay + 4), fill=B.rgba(c))
        spaced(d, (px0 + 44, ay + 5), label, mono, B.rgba(INK, .6), 3)
    return im.convert('RGB')

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

def potencias_media():
    """Potencias' README hero, from its captured frames (one scroll: a cell to the Earth)."""
    d = r'E:/Proyectos/ChatGPT/potencias/tools/src/frames/hero'
    return footage(lambda i: Image.open(os.path.join(d, f'{i:04d}.jpg')).convert('RGB'), 270)

def astro_media(seconds=5.2):
    """AstroIngeniería's own opening, the part before its interface appears: the flight through a nebula
    to the birth of a star (from the original recording, 1260 x 540 at 60 fps)."""
    src = r'E:/Proyectos/ChatGPT/Astroingenieria-readme-archive/docs-readme-intros/intro-principal.mp4'
    folder = os.path.join(HERE, 'src', 'astro-intro')
    n = round(seconds * SCENE_FPS)
    if not os.path.isdir(folder) or len(os.listdir(folder)) < n:
        os.makedirs(folder, exist_ok=True)
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-t', str(seconds), '-vf', f'fps={SCENE_FPS}', '-q:v', '2',
                        os.path.join(folder, '%04d.jpg')], check=True)
    return footage(lambda i: Image.open(os.path.join(folder, f'{i + 1:04d}.jpg')).convert('RGB'), n)

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
    body = (f'<rect x="20" y="16" width="560" height="60" rx="30" fill="{t["panel"]}" stroke="{ink}" stroke-opacity=".18" stroke-dasharray="3 5"/>'
            f'<circle cx="54" cy="46" r="5.5" fill="none" stroke="{c}" stroke-width="2"/>'
            f'<text x="76" y="56" font-family="S,serif" font-size="28" fill="{ink}" fill-opacity=".55">{name}</text>'
            f'<text x="556" y="51" text-anchor="end" font-family="M,monospace" font-size="13" letter-spacing="2" fill="{c}" fill-opacity=".8">SOON</text>')
    return B.svg(600, 92, f'{name}: coming soon', '', body)

def link_pill(t, key, name):
    W_, H_ = 600, 92
    ink, c = t['ink'], t[key]
    w = 560
    body = (f'<rect x="20" y="16" width="{w}" height="60" rx="30" fill="{t["panel"]}" stroke="{ink}" stroke-opacity=".3"/>'
            f'<circle cx="54" cy="46" r="6" fill="{c}"/>'
            f'<text x="76" y="56" font-family="S,serif" font-size="28" fill="{ink}">{name}</text>'
            f'<text x="536" y="51" text-anchor="end" font-family="M,monospace" font-size="13" letter-spacing="2" fill="{ink}" fill-opacity=".6">ENTER</text>'
            f'<path d="M546,46h16M556,40l6,6l-6,6" fill="none" stroke="{c}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>')
    return B.svg(W_, H_, f'Enter {name}', '', body)

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
        for key, slug, name in (('pot', 'potencias', 'Potencias'), ('astro', 'astroingenieria', 'AstroIngeniería'), ('time', 'tiempo', 'Tiempo')):
            open(os.path.join(OUT, 'media', f'link-{slug}-{th}.svg'), 'w', encoding='utf-8').write(link_pill(t, key, name))
        open(os.path.join(OUT, 'media', f'soon-civilizacion-{th}.svg'), 'w', encoding='utf-8').write(soon_pill(t, 'civ', 'Civilización'))
    print('capturing scenes...')
    chrome = Chrome()
    try:
        media = [potencias_media(),
                 astro_media(),
                 tiempo_media(),
                 scene_media(chrome, 'civilizacion', 9.0, fresh)]
    finally:
        chrome.close()

    def compose(k, img, progress, cache):
        step = round(24 * progress)
        if step not in cache:
            cache.clear()
            cache[step] = chrome_layer(k, step / 24)
        fr = cache[step].copy()
        fr.paste(img, (MXp, MYp), MASK)
        return fr

    print('composing...')
    avif = os.path.join(OUT, 'media', 'serie.avif')
    enc = encode_avif(avif)
    last = compose(len(media) - 1, media[-1][-1][0](), 1, {})  # the loop crossfades from the end back to the start
    webp, webp_durs = [], []
    for k, seq in enumerate(media):
        total = sum(ms for _, ms in seq)
        cache, t, prev, wt = {}, 0, last, 0
        xf = round(XFADE_S * 1000 / seq[0][1])
        for i, (load, ms) in enumerate(seq):
            fr = compose(k, load(), t / total, cache)
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
