import { createRequire } from 'node:module'

const commonmark = createRequire(import.meta.url)('../../extra/node_modules/commonmark')

const parser = new commonmark.Parser()
const renderer = new commonmark.HtmlRenderer()

export function run (data) {
  return renderer.render(parser.parse(data))
}
