#!/usr/bin/env node
/* eslint no-console:0 */

import fs from 'node:fs'
import util from 'node:util'
import { Bench } from 'tinybench'

const IMPLS = []

for (const name of fs.readdirSync(new URL('./implementations', import.meta.url)).sort()) {
  const filepath = new URL(`./implementations/${name}/index.mjs`, import.meta.url)
  const code = (await import(filepath))

  IMPLS.push({ name, code })
}

const SAMPLES = []

fs.readdirSync(new URL('./samples', import.meta.url)).sort().forEach(sample => {
  const filepath = new URL(`./samples/${sample}`, import.meta.url)

  const content = {}

  content.string = fs.readFileSync(filepath, 'utf8')

  const title = `(${content.string.length} bytes)`

  const bench = new Bench({ name: title })

  IMPLS.forEach(function (impl) {
    bench.add(impl.name, function () { impl.code.run(content.string) })
  })

  SAMPLES.push({ name: sample.split('.')[0], filename: sample, title, content, bench })
})

function formatNumber (num) {
  return num.toLocaleString('en-US', { maximumFractionDigits: 0 })
}

function formatTask (task) {
  const result = task.result

  if (result.state !== 'completed') {
    return `${task.name}: ${result.state}`
  }

  return [
    task.name,
    `${formatNumber(result.throughput.mean)} ops/sec`,
    `+/-${result.throughput.rme.toFixed(2)}%`,
    `${result.throughput.samplesCount} samples`
  ].join(' ')
}

function select (patterns) {
  const result = []

  if (!(patterns instanceof Array)) {
    patterns = [patterns]
  }

  function checkName (name) {
    return patterns.length === 0 || patterns.some(function (regexp) {
      return regexp.test(name)
    })
  }

  SAMPLES.forEach(function (sample) {
    if (checkName(sample.name)) {
      result.push(sample)
    }
  })

  return result
}

async function run (files) {
  const selected = select(files)

  if (selected.length > 0) {
    console.log('Selected samples: (%d of %d)', selected.length, SAMPLES.length)
    selected.forEach(function (sample) {
      console.log(' > %s', sample.name)
    })
  } else {
    console.log('There isn\'t any sample matches any of these patterns: %s', util.inspect(files))
  }

  for (const sample of selected) {
    console.log('\n\nSample: %s %s', sample.filename, sample.title)

    sample.bench.addEventListener('cycle', function (event) {
      console.log(' > %s', formatTask(event.task))
    })

    await sample.bench.run()
  }
}

await run(process.argv.slice(2).map(source => new RegExp(source, 'i')))
