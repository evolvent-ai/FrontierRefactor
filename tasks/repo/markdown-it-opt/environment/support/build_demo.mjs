#!/usr/bin/env node

import { cp } from 'node:fs/promises'
import { build } from 'vite'
import { viteSingleFile } from 'vite-plugin-singlefile'

await build({
  root: 'support/demo_template',
  configFile: false,
  plugins: [viteSingleFile({ removeViteModuleLoader: true })],
  build: {
    outDir: '../../demo',
    emptyOutDir: true
  }
})

await cp('support/demo_template/README.md', 'demo/README.md')
