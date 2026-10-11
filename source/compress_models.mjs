// Geometry compression only: keep nodes, textures and all countable objects.
import { NodeIO } from '@gltf-transform/core';
import { ALL_EXTENSIONS } from '@gltf-transform/extensions';
import { dedup, meshopt, getBounds } from '@gltf-transform/functions';
import { MeshoptEncoder, MeshoptDecoder } from 'meshoptimizer';
import { mkdir, readFile, writeFile, stat } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import assert from 'node:assert/strict';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const input = resolve(root, process.argv[2] || 'assets/models');
const output = resolve(root, process.argv[3] || 'assets-compressed/models');
assert.notEqual(input, output, 'Use a separate output directory.');
await mkdir(output, { recursive: true });
await Promise.all([MeshoptEncoder.ready, MeshoptDecoder.ready]);
const io = new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({
  'meshopt.encoder': MeshoptEncoder, 'meshopt.decoder': MeshoptDecoder,
});
const catalog = JSON.parse(await readFile(resolve(root, 'assets/catalog.json'), 'utf8'));
const checks = [];
function snapshot(doc) {
  return {
    names: doc.getRoot().listNodes().filter(n => n.getMesh()).map(n => n.getName()).sort(),
    bounds: getBounds(doc.getRoot().listScenes()[0]),
    textures: doc.getRoot().listTextures().map(t => Buffer.from(t.getImage()).toString('base64')).sort(),
  };
}
for (const item of catalog) {
  const source = resolve(input, `${item.id}.glb`), target = resolve(output, `${item.id}.glb`);
  const doc = await io.read(source), before = snapshot(doc);
  await doc.transform(dedup(), meshopt({ encoder: MeshoptEncoder, level: 'medium' }));
  await io.write(target, doc);
  const decoded = await io.read(target), after = snapshot(decoded);
  assert.deepEqual(after.names, before.names, `${item.id}: countable nodes changed`);
  assert.deepEqual(after.textures, before.textures, `${item.id}: textures changed`);
  const maxError = Math.max(...['min', 'max'].flatMap(k => before.bounds[k].map((v, i) => Math.abs(v - after.bounds[k][i]))));
  assert.ok(maxError < .0002, `${item.id}: bounding error ${maxError}`);
  for (const accessor of decoded.getRoot().listAccessors()) {
    assert.ok(accessor.getArray().every(Number.isFinite), `${item.id}: invalid coordinates`);
  }
  checks.push({ id: item.id, beforeBytes: (await stat(source)).size, afterBytes: (await stat(target)).size, maxError, nodes: after.names.length });
  console.log(`${item.id}: ${checks.at(-1).beforeBytes} -> ${checks.at(-1).afterBytes} bytes`);
}
await writeFile(resolve(output, 'compression-report.json'), JSON.stringify(checks, null, 2));
console.log('All 12 models decoded; node names, textures and bounds verified.');
