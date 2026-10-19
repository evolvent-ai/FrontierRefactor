// @ts-nocheck -- generated CommonJS glue; see dispatch.source()
const DISPATCH = {"resolveAvatarRedirectUrl": ["./src/common/avatar.js", "resolveAvatarRedirectUrl"], "mixWithWhite": ["./src/features/beautify/palette.js", "mixWithWhite"], "normalizeAspectRatio": ["./src/features/ocr/model.js", "normalizeAspectRatio"], "hideFailCourse": ["./src/features/homepage/index.js", "hideFailCourse"], "customText": ["./src/features/homepage/index.js", "customText"]};
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
