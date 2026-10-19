import pathlib, tomllib
root = pathlib.Path('/app')
data = tomllib.loads((root / 'pyproject.toml').read_text())
scripts = dict(data.get('project', {}).get('scripts', {}))
scripts.update(data.get('tool', {}).get('poetry', {}).get('scripts', {}))
for name, target in scripts.items():
    module, func = str(target).split(':', 1)
    body = '#!/bin/sh\nexec python3 -c \"from %s import %s; raise SystemExit(%s())\" \"$@\"\n' % (module, func, func)
    out = pathlib.Path('/usr/local/bin') / name
    out.write_text(body)
    out.chmod(0o755)
