#!/usr/bin/env node

import crypto from 'node:crypto'
import { readFileSync, writeFileSync } from 'node:fs'

const refUrl = 'https://raw.githubusercontent.com/commonmark/cmark/master/test/pathological_tests.py'
const hashFile = new URL('./track-ref-pathological.json', import.meta.url)

const update = process.argv.includes('--update')

if (process.argv.some(arg => arg !== '--update' && arg !== process.argv[0] && arg !== process.argv[1])) {
  console.error('Usage: node support/track-ref-pathological.mjs [--update]')
  process.exit(1)
}

const response = await fetch(refUrl)

if (!response.ok) {
  throw new Error(`Unable to fetch cmark pathological tests: ${response.status} ${response.statusText}`)
}

const sourceHash = crypto.createHash('md5').update(await response.text()).digest('hex')
const trackedHash = JSON.parse(readFileSync(hashFile, 'utf8')).md5

if (update) {
  if (sourceHash === trackedHash) {
    console.log(`Pathological reference hash is already up to date: ${sourceHash}`)
    process.exit(0)
  }

  writeFileSync(hashFile, `{ "md5": "${sourceHash}" }\n`)
  console.log(`Updated pathological reference hash: ${sourceHash}`)
  process.exit(0)
}

if (sourceHash !== trackedHash) {
  throw new Error(
    'Hash of cmark pathological tests changed.\n' +
    `Expected: ${trackedHash}\n` +
    `Actual:   ${sourceHash}\n` +
    'Verify upstream changes and run `npm run pathological:update-hash`.'
  )
}

console.log(`Pathological reference hash is unchanged: ${sourceHash}`)
