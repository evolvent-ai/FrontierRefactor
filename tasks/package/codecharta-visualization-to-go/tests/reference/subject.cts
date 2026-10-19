// @ts-nocheck -- generated CommonJS glue; see dispatch.source()
const DISPATCH = {"viewIdForLink": ["./visualization/app/codeCharta/routing/routePaths.js", "viewIdForLink"], "getAsApiVersion": ["./visualization/app/codeCharta/stores/fileStore/loaders/ccJson/util/fileValidator.js", "getAsApiVersion"], "loadMaskImage": ["./visualization/app/codeCharta/renderer/wordCloud/util/wordCloudMask.js", "loadMaskImage"], "interpolateColor": ["./visualization/app/codeCharta/renderer/wordCloud/util/color.util.js", "interpolateColor"], "colorForWord": ["./visualization/app/codeCharta/renderer/wordCloud/util/wordCloudWordColor.js", "colorForWord"], "toExportApiVersion": ["./visualization/app/codeCharta/util/apiVersion.js", "toExportApiVersion"], "downloadPng": ["./visualization/app/codeCharta/features/screenshot/services/pngScreenshot.js", "downloadPng"], "shapeMaskFromSvg": ["./visualization/app/codeCharta/features/domainBar/util/shapeMaskSvg.js", "shapeMaskFromSvg"], "settingCountLabel": ["./visualization/app/codeCharta/features/scenarios/components/scenarioSettingsPicker/settingCountLabel.js", "settingCountLabel"], "formatShare": ["./visualization/app/codeCharta/features/domainWordOccurrences/util/formatShare.js", "formatShare"], "getXMLmodel": ["./visualization/app/codeCharta/features/3dPrint/3DExports/generateXML/build3mfModel.js", "getXMLmodel"]};
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
