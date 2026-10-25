"""Prototype: the whole series as one animated WebP that plays the four pieces in sequence.

    python tools/secuencia.py        ->  media/serie.webp and media/link-*.svg (the published README)

Potencias plays its own hero clip; AstroIngeniería, Tiempo and Civilización are WebGL scenes
(tools/escenas/escena.html, after the engine of drayzu.github.io/prototypes/vuelo.html)
rendered frame by frame with headless Chrome. Everything is composed with Pillow.
"""
import base64, importlib.util, io, json, os, socket, subprocess, tempfile, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('build', os.path.join(HERE, 'build.py'))
B = importlib.util.module_from_spec(spec)
spec.loader.exec_module(B)

from PIL import Image, ImageDraw
import websocket

OUT = os.path.dirname(HERE)
CHROME = r'C:/Program Files/Google/Chrome/Application/chrome.exe'
T = B.CARD
INK, BG = T['ink'], T['card']
W, H = 1000, 900
MX, MY, MW, MH = 20, 318, 960, 440        # media box
FPS_MS = 66
XFADE = 7                                  # frames of crossfade between pieces

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

# ------------------------------------------------------------------ layout
mono = B.pil_font('mono.woff2', 13)
mono_s = B.pil_font('mono.woff2', 11)
mono_p = B.pil_font('mono.woff2', 14)
serif_t = B.pil_font('serif.woff2', 66)
serif_n = B.pil_font('serif.woff2', 23)
serif_h = B.pil_font('serif.woff2', 58)
italic_s = B.pil_font('serif-italic.woff2', 23)
italic_h = B.pil_font('serif-italic.woff2', 23)

def spaced(d, xy, text, font, fill, sp=0.0, anchor='l'):
    x, y = xy
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
    dict(i=2, title='Tiempo', tagline='From before the Big Bang to the last light.', live=False),
    dict(i=3, title='Civilización', tagline='Watch a civilization outgrow its planet.', live=False),
]

def chrome_layer(active, progress):
    """Everything but the media: header, the line of stations (active one lit, with a progress ring) and the caption."""
    S = 2  # supersample the line and rings
    im = Image.new('RGBA', (W * S, H * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((S, S, W * S - 2 * S, H * S - 2 * S), radius=18 * S, fill=B.rgba(BG), outline=B.rgba(INK, .14), width=2 * S)
    # line
    d.line((XS[0] * S, LY * S, XS[1] * S, LY * S), fill=B.rgba(INK, .32), width=S)
    x = XS[1]
    while x < XS[3]:
        d.line((x * S, LY * S, min(x + 3, XS[3]) * S, LY * S), fill=B.rgba(INK, .28), width=S)
        x += 9
    for k, (key, name, axis, live) in enumerate(B.STATIONS):
        c = T[key]
        cx, cy = XS[k] * S, LY * S
        if k == active:
            d.ellipse((cx - 17 * S, cy - 17 * S, cx + 17 * S, cy + 17 * S), outline=B.rgba(INK, .14), width=S)
            d.arc((cx - 17 * S, cy - 17 * S, cx + 17 * S, cy + 17 * S), -90, -90 + 360 * progress, fill=B.rgba(c), width=2 * S)
        if live:
            d.ellipse((cx - 13 * S, cy - 13 * S, cx + 13 * S, cy + 13 * S), fill=B.rgba(c, .18))
            d.ellipse((cx - 6 * S, cy - 6 * S, cx + 6 * S, cy + 6 * S), fill=B.rgba(c))
        else:
            d.ellipse((cx - 6 * S, cy - 6 * S, cx + 6 * S, cy + 6 * S), fill=B.rgba(BG), outline=B.rgba(c), width=2 * S)
    im = im.resize((W, H), Image.LANCZOS)
    d = ImageDraw.Draw(im)
    spaced(d, (W / 2, 62), f'DRAYZU \u00b7 {B.SERIES} \u00b7 A SERIES', mono, B.rgba(INK, .45), 5.5, 'm')
    title, sub = B.HEADLINE
    d.text((W / 2, 140), title, font=serif_t, fill=B.rgba(INK), anchor='ms')
    d.text((W / 2, 180), sub, font=italic_s, fill=B.rgba(INK, .72), anchor='ms')
    for k, (key, name, axis, live) in enumerate(B.STATIONS):
        on = k == active
        d.text((XS[k], LY + 42), name, font=serif_n, fill=B.rgba(INK, .95 if on else .4), anchor='ms')
        spaced(d, (XS[k], LY + 62), axis.upper() + ('' if live else ' \u00b7 SOON'), mono_s,
               B.rgba(T[key], 1 if on else .45), 1.5, 'm')
    # caption under the media
    p = PIECES[active]
    c = T[B.STATIONS[active][0]]
    d.text((32, H - 66), p['title'], font=serif_h, fill=B.rgba(INK), anchor='ls')
    d.text((36, H - 30), p['tagline'], font=italic_h, fill=B.rgba(INK, .72), anchor='ls')
    py0, py1, px1 = H - 104, H - 48, W - 36
    if p['live']:
        pw = round(52 + mono_p.getlength(p['url']) + 150)
        px0 = px1 - pw
        d.rounded_rectangle((px0, py0, px1, py1), radius=28, fill=B.rgba(BG), outline=B.rgba(INK, .3), width=1)
        ay = (py0 + py1) // 2
        d.line((px0 + 24, ay, px0 + 38, ay), fill=B.rgba(c), width=2)
        d.line((px0 + 32, ay - 5, px0 + 38, ay, px0 + 32, ay + 5), fill=B.rgba(c), width=2, joint='curve')
        d.text((px0 + 50, ay + 5), p['url'], font=mono_p, fill=B.rgba(INK), anchor='ls')
        bx0, bx1 = px1 - 124, px1 - 11
        d.rounded_rectangle((bx0, py0 + 11, bx1, py1 - 11), radius=17, fill=B.rgba(c))
        spaced(d, (bx0 + 17, ay + 5), 'ENTER', mono, B.rgba('#0d0b0a'), 1.5)
        kx, ky = bx1 - 32, ay + 3
        d.line((kx + 10, ky - 7, kx + 10, ky, kx, ky), fill=B.rgba('#0d0b0a'), width=2)
        d.line((kx + 4, ky - 4, kx, ky, kx + 4, ky + 4), fill=B.rgba('#0d0b0a'), width=2)
    else:
        label = 'IN PROGRESS'
        pw = round(mono.getlength(label) + 3 * len(label) + 64)
        px0 = px1 - pw
        d.rounded_rectangle((px0, py0, px1, py1), radius=28, fill=B.rgba(BG), outline=B.rgba(INK, .22), width=1)
        ay = (py0 + py1) // 2
        d.ellipse((px0 + 24, ay - 4, px0 + 32, ay + 4), fill=B.rgba(c))
        spaced(d, (px0 + 44, ay + 5), label, mono, B.rgba(INK, .6), 3)
    return im

def feather():
    mask = Image.new('L', (MW, MH), 255)
    md = ImageDraw.Draw(mask)
    for i in range(40):
        md.rectangle((i, i, MW - 1 - i, MH - 1 - i), outline=round(255 * (i / 40) ** 1.5))
    return mask

MASK = feather()

def boxed(fr):
    box = Image.new('RGB', (MW, MH), B.rgba(BG)[:3])
    box.paste(fr, ((MW - fr.width) // 2, (MH - fr.height) // 2))
    return box

# ------------------------------------------------------------------ the media of each piece: [(RGB 960x440, ms)]
def live_media(name, loops=1):
    p = B.LIVE[name]
    src = Image.open(p['src'])
    durs = B.webp_durations(p['src'])
    a, z = p['frames']
    z = z or src.n_frames
    out = []
    for k in range(a, z):
        src.seek(k)
        fr = src.convert('RGB')
        if p['crop']:
            fr = fr.crop((0, p['crop'][0], fr.width, p['crop'][1]))
        out.append((boxed(fr), durs[k]))
    if loops > 1:  # fade between loops so the repeat is not a jump
        one = out
        out = []
        for _ in range(loops):
            seg = list(one)
            for j in range(6):
                img, ms = seg[-6 + j]
                seg[-6 + j] = (Image.blend(img, Image.new('RGB', img.size, B.rgba(BG)[:3]), (j + 1) / 7), ms)
            out += seg
    return out

def scene_media(chrome, piece, seconds):
    """The WebGL scenes in tools/escenas/escena.html (Tiempo, Civilización)."""
    spec = importlib.util.spec_from_file_location('capturar', os.path.join(HERE, 'escenas', 'capturar.py'))
    cap = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cap)
    times = [i * FPS_MS / 1000 for i in range(round(seconds * 1000 / FPS_MS))]
    frames = cap.scene_frames(chrome, piece, times, size=(MW, MH))
    for j in range(8):  # fade out the last frames
        k = len(frames) - 8 + j
        frames[k] = Image.blend(frames[k], Image.new('RGB', (MW, MH), B.rgba(BG)[:3]), (j + 1) / 9)
    return [(f, FPS_MS) for f in frames]

# ------------------------------------------------------------------ the links under the sequence (an image on GitHub is one link)
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
def main():
    os.makedirs(os.path.join(OUT, 'media'), exist_ok=True)
    for th, t in B.THEMES.items():
        for key, slug, name in (('pot', 'potencias', 'Potencias'), ('astro', 'astroingenieria', 'AstroIngeniería')):
            open(os.path.join(OUT, 'media', f'link-{slug}-{th}.svg'), 'w', encoding='utf-8').write(link_pill(t, key, name))
    print('capturing teasers...')
    chrome = Chrome()
    try:
        media = [live_media('potencias'),
                 scene_media(chrome, 'astroingenieria', 9.0),
                 scene_media(chrome, 'tiempo', 8.6),
                 scene_media(chrome, 'civilizacion', 9.0)]
    finally:
        chrome.close()
    print('composing...')
    frames, durs = [], []
    for k, seq in enumerate(media):
        total = sum(ms for _, ms in seq)
        cache, t = {}, 0
        for img, ms in seq:
            step = round(24 * t / total)
            if step not in cache:
                cache[step] = chrome_layer(k, step / 24)
            fr = cache[step].copy()
            fr.paste(img, (MX, MY), MASK)
            frames.append(fr)
            durs.append(ms)
            t += ms
    # crossfade into each piece (and from the last back to the first)
    starts = [0]
    for seq in media[:-1]:
        starts.append(starts[-1] + len(seq))
    for s in starts:
        prev = frames[s - 1].copy()
        for j in range(XFADE):
            frames[s + j] = Image.blend(prev, frames[s + j], (j + 1) / (XFADE + 1))
    # composed at 1000 px, published at about the README's own width; particles are costly, hence the quality
    frames = [f.resize((920, round(H * 920 / W)), Image.LANCZOS) for f in frames]
    dst = os.path.join(OUT, 'media', 'serie.webp')
    frames[0].save(dst, save_all=True, append_images=frames[1:], duration=durs, loop=0, quality=58, method=4)
    print(f'  serie.webp  {os.path.getsize(dst) / 1e6:.2f} MB  ({len(frames)} frames, {sum(durs) / 1000:.1f} s)')

if __name__ == '__main__':
    main()
