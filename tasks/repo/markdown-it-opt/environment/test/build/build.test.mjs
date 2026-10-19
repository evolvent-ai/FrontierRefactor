import assert from 'node:assert/strict'
import { describe, it } from 'node:test'
import { createRequire } from 'node:module'

const require = createRequire(import.meta.url)
const md = require('../../')()

describe('CJS', () => {
  it('require', () => {
    assert.strictEqual(md.render('abc'), '<p>abc</p>\n')
  })
})
