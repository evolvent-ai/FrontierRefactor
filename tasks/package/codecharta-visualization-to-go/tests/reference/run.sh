#!/usr/bin/env bash
# Serve the subject over the wire the verifier speaks. Replace the implementation,
# not this file: the verifier starts it exactly as written.
set -euo pipefail
cd "$(dirname "$0")"
sh -c 'tsc --target ES2022 --module commonjs --skipLibCheck --allowJs $(find . -name '"'"'*.ts'"'"' -not -path '"'"'./node_modules/*'"'"' -not -name '"'"'*.d.ts'"'"' 2>/dev/null) ./subject.cts || tsc --target ES2022 --module commonjs --skipLibCheck ./subject.cts' >/dev/null
exec node --experimental-specifier-resolution=node ./serve.cjs subject.cjs entry
