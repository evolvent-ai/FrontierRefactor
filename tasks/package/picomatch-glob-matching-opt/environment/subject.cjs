const DISPATCH = {"isObject": ["./lib/utils.js", "isObject"], "hasRegexChars": ["./lib/utils.js", "hasRegexChars"], "isRegexChar": ["./lib/utils.js", "isRegexChar"], "escapeRegex": ["./lib/utils.js", "escapeRegex"], "toPosixSlashes": ["./lib/utils.js", "toPosixSlashes"], "isWindows": ["./lib/utils.js", "isWindows"], "removeBackslashes": ["./lib/utils.js", "removeBackslashes"], "escapeLast": ["./lib/utils.js", "escapeLast"], "removePrefix": ["./lib/utils.js", "removePrefix"], "wrapOutput": ["./lib/utils.js", "wrapOutput"], "basename": ["./lib/utils.js", "basename"]};
exports.entry = async function(op, ...args) {
  if (!DISPATCH[op]) throw new Error('unknown operation: ' + op);
  const [mod, symbol] = DISPATCH[op];
  let loaded;
  // require, not dynamic import: require resolves .ts (Node 22 strips types) and .js
  // alike, while ESM dynamic import of a .ts path raises a terminal ERR_MODULE_NOT_FOUND
  // that the catch cannot recover from. ESM-only subjects keep their type: module .mjs
  // or "type": "module" declares it.
  loaded = require(mod);
  const fn = loaded[symbol] || (loaded.default && loaded.default[symbol]) || loaded.default;
  if (typeof fn !== 'function') throw new Error('export is not callable: ' + symbol);
  return fn(...args);
};
