"""AstroIngeniería's Dyson sphere, recorded from its own site without the interface (the profile's
AstroIngeniería piece).

    python tools/escenas/astro_dyson.py [--test]   ->  tools/src/astro-dyson/NNNN.png

Serves nothing itself: the built site must be running (cd Astroingenieria-readme-v2; npx vite preview
--port 5195). Headless Chrome hides every element but the canvases, lets the opening play out in real
time, then pauses the page's clock and advances it a thirtieth of a second per frame (virtual time),
so the recording is smooth whatever the capture costs.
"""
import base64, importlib.util, json, os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('secuencia', os.path.join(os.path.dirname(HERE), 'secuencia.py'))
S = importlib.util.module_from_spec(spec)
spec.loader.exec_module(S)

URL = 'http://localhost:5195/AstroIngenieria/'
OUT = os.path.join(os.path.dirname(HERE), 'src', 'astro-dyson')
W, H, DPR = 1600, 860, 2
FPS = 30
SECONDS = 9.0
SETTLE = 16.0   # real seconds for the opening to play out before recording
HIDE = '*{visibility:hidden!important;cursor:none!important}canvas{visibility:visible!important}'

def main():
    test = '--test' in sys.argv
    os.makedirs(OUT, exist_ok=True)
    c = S.Chrome()
    try:
        c.call('Emulation.setDeviceMetricsOverride', width=W, height=H, deviceScaleFactor=DPR, mobile=False)
        c.call('Page.enable')
        c.call('Page.navigate', url=URL)
        time.sleep(SETTLE)
        c.js(f"const s=document.createElement('style');s.textContent={json.dumps(HIDE)};document.head.appendChild(s);1")
        time.sleep(.5)
        n = 1 if test else round(SECONDS * FPS)
        c.call('Emulation.setVirtualTimePolicy', policy='pause')
        for i in range(n):
            c.call('Emulation.setVirtualTimePolicy', policy='advance', budget=1000 / FPS)
            # wait for the budget to run out
            while True:
                msg = json.loads(c.ws.recv())
                if msg.get('method') == 'Emulation.virtualTimeBudgetExpired':
                    break
            shot = c.call('Page.captureScreenshot', format='png')
            with open(os.path.join(OUT, f'{i:04d}.png'), 'wb') as f:
                f.write(base64.b64decode(shot['data']))
            if i % 30 == 0:
                print(f'  {i}/{n}', flush=True)
    finally:
        c.close()

if __name__ == '__main__':
    main()
