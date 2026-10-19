const DISPATCH = {"Event": ["./src/event.js", "Event"], "default": ["./src/event.js", "default"], "App": ["./src/app.js", "App"], "Talent": ["./src/talent.js", "Talent"], "Life": ["./src/life.js", "Life"], "Property": ["./src/property.js", "Property"], "Achievement": ["./src/achievement.js", "Achievement"], "checkCondition": ["./src/functions/condition.js", "checkCondition"], "extractMaxTriggers": ["./src/functions/condition.js", "extractMaxTriggers"], "summary": ["./src/functions/summary.js", "summary"], "getRate": ["./src/functions/addition.js", "getRate"], "getGrade": ["./src/functions/addition.js", "getGrade"], "clone": ["./src/functions/util.js", "clone"], "max": ["./src/functions/util.js", "max"], "min": ["./src/functions/util.js", "min"], "sum": ["./src/functions/util.js", "sum"], "average": ["./src/functions/util.js", "average"], "map": ["./src/functions/util.js", "map"]};
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
