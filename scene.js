import * as THREE from './vendor/three.module.js';
import { GLTFLoader } from './vendor/GLTFLoader.js';
import { MeshoptDecoder } from './vendor/meshopt_decoder.mjs';

// The goods are actual GLB objects resting on one continuous, two-tier rack.
// DOM hit areas and shelf-edge labels are projected from the same camera.
export async function createMarketScene(container, products, onLayout) {
  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 1.7));
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.05;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  container.append(renderer.domElement);
  const scene = new THREE.Scene(); scene.background = new THREE.Color(0xe4e9e9);
  const rackCamera = new THREE.OrthographicCamera(-5, 5, 3, -3, .01, 100);
  const aisleCamera = new THREE.PerspectiveCamera(64, 1, .1, 100);
  let camera = aisleCamera;
  scene.add(new THREE.HemisphereLight(0xffffff, 0x89948c, 1.6));
  const key = new THREE.DirectionalLight(0xfffaf0, 2.5);
  key.position.set(-3, 8, 6); key.castShadow = true;
  key.shadow.mapSize.set(2048, 2048);
  Object.assign(key.shadow.camera, { left: -8, right: 8, top: 8, bottom: -8, near: .1, far: 30 });
  key.shadow.bias = -.0004; key.shadow.normalBias = .015; scene.add(key);
  const fill = new THREE.DirectionalLight(0xe3f1ff, .9); fill.position.set(5, 5, -3); scene.add(fill);
  const steel = new THREE.MeshStandardMaterial({ color: 0xc4ced1, roughness: .49, metalness: .48 });
  const edge = new THREE.MeshStandardMaterial({ color: 0x667782, roughness: .48, metalness: .35 });
  const cream = new THREE.MeshStandardMaterial({ color: 0xf1f3ef, roughness: .72 });
  const rail = new THREE.MeshStandardMaterial({ color: 0xf5cc55, roughness: .45 });
  const floorMat = new THREE.MeshStandardMaterial({ color: 0xd1d5cd, roughness: .68 });
  const canvas = document.createElement('canvas'); canvas.width = canvas.height = 256;
  const ctx = canvas.getContext('2d'); ctx.fillStyle = '#e7edeb'; ctx.fillRect(0, 0, 256, 256);
  for (let y = 12; y < 256; y += 20) for (let x = 12; x < 256; x += 20) {
    ctx.fillStyle = '#adb7b8'; ctx.beginPath(); ctx.arc(x, y, 1.6, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = '#fafcfb'; ctx.fillRect(x - 2, y - 3, 3, 1);
  }
  const pegTexture = new THREE.CanvasTexture(canvas); pegTexture.colorSpace = THREE.SRGBColorSpace;
  pegTexture.wrapS = pegTexture.wrapT = THREE.RepeatWrapping; pegTexture.repeat.set(4, 2);
  const backing = new THREE.MeshStandardMaterial({ map: pegTexture, roughness: .88 });
  const rack = new THREE.Group(), aisle = new THREE.Group(); scene.add(rack, aisle);
  const models = new Map(), shown = new Map(), loader = new GLTFLoader().setMeshoptDecoder(MeshoptDecoder);
  let page = '入口', request = 0, frame = 0, animation = 0, disposed = false;
  const shakes = new Map();
  const pops = new Map();

  function box(parent, dimensions, position, material) {
    const mesh = new THREE.Mesh(new THREE.BoxGeometry(...dimensions), material);
    mesh.position.set(...position); mesh.receiveShadow = true; mesh.castShadow = true; parent.add(mesh); return mesh;
  }
  box(rack, [8.1, 4.1, .07], [0, 2.1, -.86], backing);
  for (const x of [-4.05, 4.05]) {
    box(rack, [.10, 4.2, 1.8], [x, 2.1, 0], steel);
    box(rack, [.15, .13, 2.1], [x, .05, .1], edge);
  }
  for (const x of [-1.35, 1.35]) box(rack, [.07, 4.1, .09], [x, 2.1, -.78], steel);
  for (const y of [.60, 2.70]) {
    box(rack, [8.2, .085, 1.8], [0, y - .0425, 0], cream);
    box(rack, [8.24, .15, .085], [0, y - .09, .93], edge);
    box(rack, [8.25, .025, .025], [0, y - .015, .985], steel);
  }
  box(rack, [30, .06, 25], [0, -.06, 0], floorMat);
  const grout = new THREE.MeshStandardMaterial({ color: 0xadb5b3, roughness: .9 });
  for (let i = -10; i <= 10; i += 2) {
    box(rack, [30, .002, .012], [0, -.028, i], grout);
    box(rack, [.012, .002, 25], [i, -.028, 0], grout);
  }

  // Original aisle scenery; no reference screenshot is reused as a texture.
  box(aisle, [20, .08, 30], [0, -.08, -4], floorMat);
  box(aisle, [14, 7, .15], [0, 3.5, -10], cream);
  const packageMats = [0x286e8b, 0xcc5f42, 0x68966b, 0xcead53, 0x9382ac, 0xe5e4d7].map(color => new THREE.MeshStandardMaterial({ color, roughness: .5 }));
  for (const side of [-1, 1]) {
    box(aisle, [.1, 5.4, 14], [side * 3.2, 2.7, -3], backing);
    for (let row = 0; row < 4; row++) {
      const y = .45 + row * 1.3;
      box(aisle, [1.25, .09, 14], [side * 2.65, y, -3], cream);
      box(aisle, [.08, .14, 14], [side * 2.01, y - .05, -3], rail);
      for (let z = -9; z < 3.7; z += .63) {
        const mat = packageMats[(row * 7 + Math.round(z * 2) + 40) % packageMats.length];
        box(aisle, [.38, .82, .43], [side * 2.57, y + .45, z], mat);
        box(aisle, [.006, .20, .30], [side * 2.37, y + .5, z], cream);
      }
    }
    for (let z = -10; z <= 4; z += 3.5) box(aisle, [.10, 5.5, .10], [side * 2.0, 2.75, z], steel);
  }
  for (let row = 0; row < 4; row++) {
    box(aisle, [6.4, .08, 1.0], [0, .5 + row * 1.3, -9.5], cream);
    for (let col = -5; col <= 5; col++) box(aisle, [.45, .85, .42], [col * .55, .96 + row * 1.3, -9.5], packageMats[(col + row + 12) % 6]);
  }

  function redraw() {
    if (disposed) return;
    cancelAnimationFrame(frame);
    frame = requestAnimationFrame(draw);
  }
  function project(point) {
    const value = point.clone().project(camera);
    return { x: (value.x + 1) * container.clientWidth / 2, y: (1 - value.y) * container.clientHeight / 2 };
  }
  function layout() {
    if (!rack.visible) return;
    const result = [];
    for (const [id, entry] of shown) {
      const bounds = new THREE.Box3().setFromObject(entry.object), corners = [];
      for (const x of [bounds.min.x, bounds.max.x]) for (const y of [bounds.min.y, bounds.max.y]) for (const z of [bounds.min.z, bounds.max.z]) corners.push(project(new THREE.Vector3(x, y, z)));
      const left = Math.min(...corners.map(p => p.x)), right = Math.max(...corners.map(p => p.x));
      const top = Math.min(...corners.map(p => p.y)), bottom = Math.max(...corners.map(p => p.y));
      result.push({ id, left, top, width: right - left, height: bottom - top,
        label: project(new THREE.Vector3(entry.x, entry.y - .09 - .15 / 2, .93 + .085 / 2)) });
    }
    onLayout(result);
  }
  function draw(now = performance.now()) {
    if (disposed) return;
    let moving = false;
    for (const [id, start] of pops) {
      const entry = shown.get(id); if (!entry) { pops.delete(id); continue; }
      const elapsed = now - start;
      entry.object.scale.setScalar(elapsed < 800 ? 1 + .16*Math.sin(Math.PI*elapsed/800) : 1);
      if (elapsed >= 800) pops.delete(id); else moving = true;
    }
    for (const [id, start] of shakes) {
      const entry = shown.get(id); if (!entry) { shakes.delete(id); continue; }
      const elapsed = now - start;
      entry.object.position.x = entry.x + (elapsed < 350 ? Math.sin(elapsed / 25) * .042 * (1 - elapsed / 350) : 0);
      if (elapsed >= 350) shakes.delete(id); else moving = true;
    }
    renderer.render(scene, camera);
    if (moving) frame = requestAnimationFrame(draw);
  }
  function resize() {
    const width = Math.max(container.clientWidth, 1), height = Math.max(container.clientHeight, 1), aspect = width / height;
    const isAisle = page !== '百货区' && page !== '食品区';
    const viewHeight = isAisle ? Math.max(5.7, 8 / aspect) : Math.max(5.9, 9.1 / aspect);
    camera = isAisle ? aisleCamera : rackCamera;
    rackCamera.left = -viewHeight * aspect / 2; rackCamera.right = viewHeight * aspect / 2;
    rackCamera.top = viewHeight / 2; rackCamera.bottom = -viewHeight / 2;
    aisleCamera.aspect = aspect;
    if (isAisle) { camera.position.set(0, 2.1, 4.5); camera.lookAt(0, 2.2, -6); }
    else { camera.position.set(0, 7.4, 10.5); camera.lookAt(0, 2.55, 0); }
    camera.updateProjectionMatrix(); camera.updateMatrixWorld();
    renderer.setSize(width, height); layout(); redraw();
  }
  const observer = new ResizeObserver(resize); observer.observe(container);

  async function loadModel(item) {
    if (!models.has(item.id)) models.set(item.id, loader.loadAsync(globalThis.marketAssetUrl(`assets/models/${item.id}.glb`)).then(gltf => gltf.scene));
    return models.get(item.id);
  }
  async function setPage(next) {
    const token = ++request; page = next; shown.clear(); shakes.clear(); pops.clear();
    for (const object of [...rack.children]) if (object.userData.product) rack.remove(object);
    rack.visible = next === '百货区' || next === '食品区'; aisle.visible = !rack.visible;
    resize();
    if (!rack.visible) return true;
    const displayOrder = next === '百货区' ? ['batteries', 'pencils', 'toothpaste', 'mugs', 'brushes', 'rolls'] : ['apples', 'candy', 'chips', 'eggs', 'water', 'yogurt'];
    const items = displayOrder.map(id => products.find(p => p.id === id));
    const loaded = await Promise.all(items.map(loadModel));
    if (token !== request || disposed) return false;
    loaded.forEach((source, index) => {
      const object = new THREE.Group(); object.userData.product = true;
      const model = source.clone(true); object.add(model);
      const b = new THREE.Box3().setFromObject(model), center = b.getCenter(new THREE.Vector3());
      model.position.sub(center);
      if (['batteries', 'brushes', 'candy'].includes(items[index].id)) model.rotation.x = .82;
      if (items[index].id === 'pencils') model.rotation.y = -.65;
      // Supplied roll pack already presents its paper ends toward the camera.
      // Blender's vertical Z axis becomes Y in glTF; stagger rows without tilting.
      const countingYaw = { eggs: 24, yogurt: -24, water: -28 }[items[index].id];
      if (countingYaw !== undefined) model.rotation.y = THREE.MathUtils.degToRad(countingYaw);
      // Rotate flat display packets upward, then put their lower edge on shelf.
      model.updateMatrixWorld(true);
      const rotated = new THREE.Box3().setFromObject(model), size = rotated.getSize(new THREE.Vector3());
      const heightLimit = items[index].id === 'candy' ? 1.65 : items[index].id === 'pencils' ? 1.55 : items[index].id === 'water' ? .85 : index < 3 ? 1.27 : .95;
      const scale = Math.min(2.15 / size.x, heightLimit / size.y, 1.46 / size.z);
      model.scale.setScalar(scale); model.position.multiplyScalar(scale);
      model.updateMatrixWorld(true);
      const after = new THREE.Box3().setFromObject(model); model.position.y -= after.min.y;
      const x = (index % 3 - 1) * 2.65, y = index < 3 ? 2.70 : .60;
      object.position.set(x, y, items[index].id === 'rolls' ? .42 : .12); rack.add(object);
      model.traverse(mesh => { if (mesh.isMesh) { mesh.castShadow = !(mesh.material?.transparent); mesh.receiveShadow = items[index].id !== 'eggs'; } });
      shown.set(items[index].id, { object, x, y });
    });
    rack.updateMatrixWorld(true); layout(); redraw(); return true;
  }
  resize();
  return { setPage, celebrate(id) { if (matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    pops.set(id, performance.now()); redraw(); }, shake(id) { if (matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    shakes.set(id, performance.now()); redraw(); },
    dispose() { disposed = true; request++; cancelAnimationFrame(frame); cancelAnimationFrame(animation); observer.disconnect(); renderer.dispose(); renderer.domElement.remove(); } };
}

