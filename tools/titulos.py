"""Renders header variants side by side, to choose the headline (tools/versiones/titulos/)."""
import importlib.util, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('build', os.path.join(HERE, 'build.py'))
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)

VARIANTS = [
    ('A', 'Measuring the universe',
     'Interactive pieces about its size, its time, and what we could build in it.'),
    ('B', 'How small, how brief, how far',
     'Interactive pieces about the universe, and our place in it.'),
    ('C', 'Our place in the cosmos',
     'How small we are, how brief, and how far we could go.'),
    ('D', 'From a quark to a civilization',
     'Interactive journeys through the size, the time and the future of everything.'),
    ('E', 'The universe, at every scale',
     'From the foam of spacetime to the minds that might one day reshape it.'),
]

out = os.path.join(HERE, 'versiones', 'titulos')
os.makedirs(out, exist_ok=True)
rows = []
for key, title, sub in VARIANTS:
    for theme in ('dark', 'light'):
        with open(os.path.join(out, f'{key}-{theme}.svg'), 'w', encoding='utf-8') as f:
            f.write(build.header(build.THEMES[theme], (title, sub)))
    rows.append(f'<section><h2>{key}</h2><picture><source media="(prefers-color-scheme: dark)" srcset="{key}-dark.svg">'
                f'<img src="{key}-light.svg" alt="{title}"></picture></section>')
page = ('<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
        '<title>Header variants</title><style>'
        ':root{--bg:#fff;--fg:#59636e;--line:#d1d9e0}'
        '@media (prefers-color-scheme: dark){:root{--bg:#0d1117;--fg:#9198a1;--line:#3d444d}}'
        'body{margin:0;background:var(--bg);color:var(--fg);font:14px/1.4 system-ui,sans-serif}'
        'main{max-width:900px;margin:0 auto;padding:24px 16px}'
        'section{border:1px solid var(--line);border-radius:6px;padding:8px 16px 0;margin-bottom:20px}'
        'h2{margin:4px 0 0;font-size:13px;font-weight:600;letter-spacing:.1em}img{width:100%;display:block}'
        '</style></head><body><main>' + ''.join(rows) + '</main></body></html>')
with open(os.path.join(out, 'index.html'), 'w', encoding='utf-8') as f:
    f.write(page)
print('ok', len(VARIANTS))
