/**
 * Serve a JavaScript subject over the wire. Written into the task; not required by the factory.
 *
 * The subject supplies `entry(...) -> value` in subject.js or subject.ts, throwing to refuse.
 * Its parameters are the wire's `args`, spread. It may also return
 * a promise: asynchronous code is ordinary in this language, and a shim that did not await one
 * would freeze every answer as the JSON for a pending promise rather than as the value.
 */
'use strict';

// The subject is resolved without an extension so that the same shim serves both JavaScript and
// TypeScript: Node picks up `subject.js` from the compiler's output.
// Naming the extension here would make this file JavaScript-only, and the table would then need a
// second near-identical template to keep in step for no behaviour of its own.
// The subject's filename arrives as an argument so that this one template serves both JavaScript
// and TypeScript, the latter on Node's own type stripping. Resolving it by extension does not
// work: CommonJS `require('./subject')` will not find a `.ts` file. Hard-coding `subject.js` would
// make this template JavaScript-only and force a second, near-identical one for TypeScript -- a
// copy to keep in step for no behaviour of its own.
const path = require('path');
const { pathToFileURL } = require('url');
const subjectPath = path.resolve(__dirname, process.argv[2] || './subject.js');
const symbol = process.argv[3] || 'entry';
// Dynamic import handles native ES modules (the common GitHub shape) and also exposes CommonJS
// exports as a namespace. Static require would make every `export const` subject die at startup.
const subjectReady = import(pathToFileURL(subjectPath).href);

/** The type and the message, never the stack: a stack carries absolute paths from this machine. */
function describe(failure) {
  if (failure === null || failure === undefined) {
    return 'Error: ' + String(failure);
  }
  // The constructor's name rather than `.name`, because a subclass of Error that does not assign
  // `name` still answers "Error" there, and the type is part of the behaviour being compared.
  const type = (failure.constructor && failure.constructor.name) || typeof failure;
  const message = (failure instanceof Error ? failure.message : String(failure))
    .replaceAll(process.cwd(), '<workspace>');
  if (message.includes('Cannot find module') || message.includes('ERR_MODULE_NOT_FOUND')) {
    return type + ': module resolution failed';
  }
  return type + ': ' + message;
}

function isThenable(value) {
  return value !== null && typeof value === 'object' && typeof value.then === 'function';
}

/**
 * Await only what actually needs awaiting.
 *
 * `await` on a plain value still costs a turn of the microtask queue, and for the small subjects
 * this pipeline produces that turn is a measurable part of what op="time" reports.
 */
async function callEntry(entry, args) {
  // Spread: `args` is the argument LIST, so a subject declared `entry(a, b)` is called with
  // two arguments. See the contract in protocol.py -- packing instead would mean editing
  // real material to serve it, and then grading the edit.
  const value = entry(...args);
  return isThenable(value) ? await value : value;
}

function emit(reply) {
  let line;
  try {
    line = JSON.stringify(reply) + '\n';
  } catch (failure) {
    // A value that cannot be encoded -- a BigInt, a cycle -- is a failed call rather than a reason
    // to stop reading, so it is reported in place of the value.
    line = JSON.stringify({ id: reply.id, ok: false, error: describe(failure) }) + '\n';
  }
  process.stdout.write(line);
}

async function handle(line) {
  let request;
  try {
    request = JSON.parse(line);
  } catch (failure) {
    return;                                      // an unreadable line is not a call
  }
  if (request === null || typeof request !== 'object') {
    return;
  }

  const id = request.id;
  // AN ARGS FIELD OF THE WRONG SHAPE IS A REFUSAL, NOT AN EMPTY CALL. Collapsing both into `[]` is
  // the most expensive kind of wrong: `{"args": "not-a-list"}` was quietly rewritten into a call
  // with no arguments, the subject answered whatever a no-argument call returns, and the reply said
  // ok:true. A false SUCCESS enters grading as though it were a real answer.
  //
  // A MISSING field keeps the empty default: the factory always sends `args`, so its absence is a
  // hand-written line rather than a malformed call.
  if ('args' in request && !Array.isArray(request.args)) {
    emit({ id: id, ok: false, error: 'the arguments must be a JSON array' });
    return;
  }
  const args = Array.isArray(request.args) ? request.args : [];
  const op = request.op === undefined ? 'run' : request.op;
  const subject = await subjectReady;
  const entry = subject[symbol];

  if (op === 'time') {
    // TIMED HERE, on this side of the pipe. Measuring from the factory would charge the subject for
    // process startup and for JSON transport, which for a quick subject is most of the clock.
    const repeats = request.repeats === undefined ? 1 : Math.trunc(Number(request.repeats));
    let failure = null;
    const started = process.hrtime.bigint();
    for (let i = 0; i < repeats; i += 1) {
      try {
      await callEntry(entry, args);
      } catch (thrown) {
        failure = thrown;
        break;
      }
    }
    const elapsed = Number(process.hrtime.bigint() - started) / 1e9;
    emit(failure === null
      ? { id: id, ok: true, seconds: elapsed }
      : { id: id, ok: false, error: describe(failure) });
    return;
  }

  try {
    const value = await callEntry(entry, args);
    // JSON.stringify drops a key whose value is undefined; a subject that returned nothing should
    // still answer with a value, so it is reported as null as every other shim would report it.
    emit({ id: id, ok: true, value: value === undefined ? null : value });
  } catch (failure) {
    // A REFUSAL IS AN ANSWER. How the subject rejects bad input is behaviour a reimplementation has
    // to reproduce, so it is reported and the loop carries on reading.
    emit({ id: id, ok: false, error: describe(failure) });
  }
}

// Replies are serialised through one chain rather than raced, so that an asynchronous entry point
// cannot answer request 4 before request 3.
let queue = Promise.resolve();
let pending = '';

process.stdin.setEncoding('utf8');

process.stdin.on('data', (chunk) => {
  // A chunk is not a line. A large probe arrives split at whatever boundary the pipe chose, and
  // several small calls arrive glued together, so the remainder is carried between chunks.
  pending += chunk;
  let cut = pending.indexOf('\n');
  while (cut >= 0) {
    const line = pending.slice(0, cut).trim();
    pending = pending.slice(cut + 1);
    if (line) {
      queue = queue.then(() => handle(line));
    }
    cut = pending.indexOf('\n');
  }
});

process.stdin.on('end', () => {
  const last = pending.trim();
  pending = '';
  if (last) {
    queue = queue.then(() => handle(last));      // a final line that arrived without its newline
  }
  // Nothing else to do: once the queue settles and stdout has drained, the process ends with 0.
  // Calling process.exit() here would discard whatever of stdout the pipe had not yet accepted.
});

// The factory going away first is not this process failing, and an unhandled EPIPE would report it
// as one.
process.stdout.on('error', () => process.exit(0));
