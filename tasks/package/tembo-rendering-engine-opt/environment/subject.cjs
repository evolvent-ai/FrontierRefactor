const DISPATCH = {"render": ["./src/renderers/Blessed.js", "render"], "getId": ["./src/renderers/Blessed.js", "getId"], "setId": ["./src/renderers/Blessed.js", "setId"], "appendChild": ["./src/renderers/Blessed.js", "appendChild"], "removeChild": ["./src/renderers/Blessed.js", "removeChild"], "replaceChild": ["./src/renderers/Blessed.js", "replaceChild"], "createText": ["./src/renderers/Blessed.js", "createText"], "createElement": ["./src/renderers/Blessed.js", "createElement"], "TreeNode": ["./src/renderers/Test.js", "TreeNode"], "TextNode": ["./src/renderers/Test.js", "TextNode"], "setProp": ["./src/renderers/String.js", "setProp"], "getChildren": ["./src/renderers/String.js", "getChildren"], "getText": ["./src/renderers/String.js", "getText"], "setText": ["./src/renderers/String.js", "setText"], "isText": ["./src/renderers/String.js", "isText"], "setDOM": ["./src/renderers/DOM.js", "setDOM"], "getID": ["./src/renderers/DOM.js", "getID"], "setID": ["./src/renderers/DOM.js", "setID"], "insertChild": ["./src/renderers/DOM.js", "insertChild"], "isElement": ["./src/renderers/DOM.js", "isElement"], "isNative": ["./src/render/util.js", "isNative"], "differentTypes": ["./src/render/util.js", "differentTypes"], "differentPatch": ["./src/render/util.js", "differentPatch"], "clone": ["./src/render/util.js", "clone"], "merge": ["./src/render/util.js", "merge"]};
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
