import * as THREE from './vendor/three.module.js';
import { GLTFLoader } from './vendor/GLTFLoader.js';
import { OrbitControls } from './vendor/OrbitControls.js';

export async function openViewer(container, path) {
  const gltf = await new GLTFLoader().loadAsync(path);
  const scene = new THREE.Scene();
  const model = gltf.scene;
  const bounds = new THREE.Box3().setFromObject(model);
  const center = bounds.getCenter(new THREE.Vector3());
  const size = bounds.getSize(new THREE.Vector3());
  model.position.sub(center); scene.add(model);
  const radius = size.length() / 2;
  const camera = new THREE.PerspectiveCamera(36, 1, Math.max(radius / 100, .0001), radius * 100);
  const direction = new THREE.Vector3(.30, .88, .65).normalize();
  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.25;
  container.append(renderer.domElement);
  scene.add(new THREE.HemisphereLight(0xfffaf0, 0x64765b, 2.5));
  const key = new THREE.DirectionalLight(0xffffff, 3); key.position.set(-1, 2, 2); scene.add(key);
  const fill = new THREE.DirectionalLight(0xdaf1ff, 1.5); fill.position.set(2, 1, -1); scene.add(fill);
  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true; controls.enablePan = false;
  controls.minDistance = radius * 1.4; controls.maxDistance = radius * 12;
  let firstSize = true;
  function resize() {
    const width = Math.max(container.clientWidth, 1), height = Math.max(container.clientHeight, 1);
    camera.aspect = width / height;
    if (firstSize) {
      const halfFov = Math.min(THREE.MathUtils.degToRad(18), Math.atan(Math.tan(THREE.MathUtils.degToRad(18)) * camera.aspect));
      camera.position.copy(direction).multiplyScalar(radius / Math.sin(halfFov) * 1.1);
      controls.update(); firstSize = false;
    }
    camera.updateProjectionMatrix(); renderer.setSize(width, height);
  }
  const observer = new ResizeObserver(resize); observer.observe(container); resize();
  let disposed = false, frame;
  function draw() { if (disposed) return; controls.update(); renderer.render(scene, camera); frame = requestAnimationFrame(draw); }
  draw();
  return { dispose() {
    if (disposed) return; disposed = true; cancelAnimationFrame(frame); observer.disconnect(); controls.dispose();
    model.traverse(object => { object.geometry?.dispose();
      const materials = object.material ? (Array.isArray(object.material) ? object.material : [object.material]) : [];
      materials.forEach(material => { for (const value of Object.values(material)) if (value?.isTexture) value.dispose(); material.dispose(); });
    });
    renderer.dispose(); renderer.domElement.remove();
  } };
}
