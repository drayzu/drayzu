"""Renders tools/escenas/escena.html frame by frame with headless Chrome (WebGL), for the sequence."""
import base64, functools, http.server, io, os, threading

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SERVE_ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))   # E:/Proyectos/ChatGPT: the page imports three from potencias
PAGE = '/drayzu-perfil/tools/escenas/escena.html'

def serve():
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass
    handler = functools.partial(Quiet, directory=SERVE_ROOT)
    srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv

def scene_frames(chrome, piece, times, size=(960, 440), dsf=2, out_dir=None):
    """chrome: secuencia.Chrome. Returns RGB frames at `size`, rendered at dsf x and downsampled.
    With out_dir, writes them there as 0000.png, 0001.png... instead (big sizes do not fit in memory)."""
    srv = serve()
    try:
        w, h = size
        chrome.call('Emulation.setDeviceMetricsOverride', width=w, height=h, deviceScaleFactor=dsf, mobile=False)
        chrome.call('Page.navigate', url=f'http://127.0.0.1:{srv.server_address[1]}{PAGE}?pieza={piece}')
        import time
        for _ in range(900):
            if chrome.js('window.sceneReady === true'):
                break
            time.sleep(.1)
        else:
            raise RuntimeError('scene did not load: ' + str(chrome.js('document.title')))
        out = []
        for t in times:
            chrome.js(f'window.renderAt({t}); new Promise(r => requestAnimationFrame(() => r(true)))')
            shot = chrome.call('Page.captureScreenshot', format='png')
            im = Image.open(io.BytesIO(base64.b64decode(shot['data']))).convert('RGB')
            im = im.resize(size, Image.LANCZOS) if im.size != size else im
            if out_dir:
                im.save(os.path.join(out_dir, f'{len(out):04d}.png'), compress_level=1)
                out.append(None)
            else:
                out.append(im)
        return out
    finally:
        srv.shutdown()
