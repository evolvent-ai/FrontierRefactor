import { marked } from '../../extra/node_modules/marked/lib/marked.esm.js'

export function run (data) {
  return marked(data)
}
