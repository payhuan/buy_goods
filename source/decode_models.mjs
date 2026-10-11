// Produce temporary uncompressed files for Blender's independent import checks.
import { NodeIO } from '@gltf-transform/core';
import { ALL_EXTENSIONS } from '@gltf-transform/extensions';
import { dequantize } from '@gltf-transform/functions';
import { MeshoptDecoder } from 'meshoptimizer';
import { mkdir, readFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const output = resolve(root, 'verification/decoded-models');
await mkdir(output, { recursive: true });
await MeshoptDecoder.ready;
const io = new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({ 'meshopt.decoder': MeshoptDecoder });
const catalog = JSON.parse(await readFile(resolve(root, 'assets/catalog.json'), 'utf8'));
for (const item of catalog) {
  const doc = await io.read(resolve(root, 'assets', item.model));
  doc.getRoot().listExtensionsUsed().filter(e => e.extensionName === 'EXT_meshopt_compression').forEach(e => e.dispose());
  await doc.transform(dequantize());
  await io.write(resolve(output, `${item.id}.glb`), doc);
}
console.log('Decoded 12 temporary GLBs for Blender verification.');
