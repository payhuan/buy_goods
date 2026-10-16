const test = require('node:test');
const assert = require('node:assert/strict');
const products = require('../data.js');
const createGame = require('../game.js');
const fs = require('node:fs');
const path = require('node:path');

test('sound stays silent until enabled and becomes silent again when disabled', () => {
  const vm = require('node:vm');
  const app = fs.readFileSync(path.join(__dirname, '../app.js'), 'utf8');
  const button = { textContent: '', attributes: {}, setAttribute(k, v) { this.attributes[k] = v; }, addEventListener(_, handler) { this.click = handler; } };
  let starts = 0;
  class AudioContext {
    currentTime = 0;
    resume() {}
    createOscillator() { return { frequency: {}, connect() {}, start() { starts++; }, stop() {} }; }
    createGain() { return { gain: { setValueAtTime() {}, linearRampToValueAtTime() {}, exponentialRampToValueAtTime() {} }, connect() {} }; }
  }
  const context = vm.createContext({ marketAssetUrl: value => value, MARKET_PRODUCTS: [], createMarketGame: () => ({}), document: { querySelector: () => ({ style: {} }) }, window: { AudioContext } });
  vm.runInContext(app.slice(0, app.indexOf('function refreshScore()')), context);
  vm.runInContext('sound(false); sound(true);', context);
  assert.equal(starts, 0);
  context.document.querySelector = () => button;
  vm.runInContext(app.slice(app.indexOf("document.querySelector('#sound').addEventListener"), app.indexOf("document.querySelector('#fullscreen').addEventListener")), context);
  button.click({ currentTarget: button });
  assert.equal(button.attributes['aria-pressed'], 'true');
  assert.equal(button.textContent, '♫ 音效开');
  vm.runInContext('sound(false);', context);
  assert.equal(starts, 1);
  button.click({ currentTarget: button });
  assert.equal(button.attributes['aria-pressed'], 'false');
  assert.equal(button.textContent, '♫ 音效关');
  vm.runInContext('sound(false); sound(true);', context);
  assert.equal(starts, 1);
});

test('four pages omit introductions and allow incomplete progress and replay', () => {
  const game = createGame(products);
  assert.equal(game.page, '入口');
  game.enter(); assert.equal(game.page, '百货区');
  game.select('pencils'); assert.equal(game.foundIn('百货区'), 1);
  game.next(); assert.equal(game.page, '食品区');
  game.next(); assert.equal(game.page, '结束');
  game.back(); assert.equal(game.page, '食品区');
  game.back(); assert.equal(game.page, '百货区');
  game.back(); assert.equal(game.page, '入口');
  assert.equal(game.stars, 1);
  game.restart(); assert.equal(game.page, '入口');
  assert.equal(game.stars, 0); assert.equal(game.hasStar('pencils'), false);
});

test('generated visible package printing contains no English', () => {
  const labels = JSON.parse(fs.readFileSync(path.join(__dirname, '../assets/printed-labels.json'), 'utf8'));
  assert.ok(labels.length > 30);
  for (const label of labels) assert.doesNotMatch(label.text, /[a-z]/i);
  for (const item of products) assert.doesNotMatch(item.note, /[a-z]/i);
});

test('standalone publish file embeds every declared model and image without external entry files', () => {
  const crypto = require('node:crypto');
  const publish = path.join(__dirname, '../publish');
  const report = JSON.parse(fs.readFileSync(path.join(publish,'资源依赖清单.json'),'utf8'));
  const html = fs.readFileSync(path.join(publish,'逛超市_超喵单文件版.html'),'utf8');
  const embedded = JSON.parse(html.match(/MARKET_EMBEDDED_ASSETS=(\{[^\n]+\});/)[1]);
  assert.equal(report.external_runtime_files, 0);
  assert.equal(Object.keys(embedded).length, 25);
  assert.equal(report.images, 13);
  assert.match(embedded['assets/images/entrance-background.jpg'], /^data:image\/jpeg;base64,/);
  assert.equal(report.assets.filter(a => a.path.endsWith('.glb')).length, 12);
  for (const asset of report.assets) {
    const content = Buffer.from(embedded[asset.path].split(',')[1],'base64');
    assert.equal(content.length, asset.bytes);
    assert.equal(crypto.createHash('sha256').update(content).digest('hex'), asset.sha256);
  }
  assert.doesNotMatch(html, /<script\s+src=|<link\s+rel="stylesheet"/);
});

test('game inventory matches the generated model catalogue', () => {
  const catalogue = JSON.parse(fs.readFileSync(path.join(__dirname, '../assets/catalog.json'), 'utf8'));
  assert.equal(catalogue.length, products.length);
  for (const item of products) {
    const model = catalogue.find(asset => asset.id === item.id);
    for (const key of ['name','zone','perPackage','stock','unit','price']) assert.equal(model[key], item[key]);
    assert.equal(fs.existsSync(path.join(__dirname, '../assets', model.model)), true);
    assert.equal(fs.existsSync(path.join(__dirname, '../assets', model.image)), true);
  }
});

test('exact package quantity, rather than shelf total, determines correctness', () => {
  const game = createGame(products);
  assert.equal(game.select('brushes'), 'wrong'); // Two boards of six is not ten per board.
  assert.equal(game.select('mugs'), 'wrong');
  assert.equal(game.select('toothpaste'), 'wrong');
  for (const id of ['rolls', 'batteries', 'pencils']) assert.equal(game.select(id), 'correct');
  game.setZone('食品区');
  for (const id of ['water', 'chips', 'apples']) assert.equal(game.select(id), 'wrong');
  for (const id of ['candy', 'yogurt', 'eggs']) assert.equal(game.select(id), 'correct');
  assert.equal(game.stars, 6);
});
test('switching before any answer is unrestricted and earned stars persist', () => {
  const game = createGame(products);
  game.setZone('食品区'); assert.equal(game.stars, 0);
  game.select('eggs'); game.setZone('百货区');
  assert.equal(game.stars, 1); game.setZone('食品区');
  assert.equal(game.hasStar('eggs'), true);
  assert.equal(game.select('eggs'), 'ignored'); assert.equal(game.stars, 1);
});
test('wrong, unknown and out of area choices never award stars', () => {
  const game = createGame(products);
  for (let i = 0; i < 4; i++) assert.equal(game.select('brushes'), 'wrong');
  assert.equal(game.select('eggs'), 'ignored'); assert.equal(game.select('unknown'), 'ignored');
  assert.equal(game.stars, 0); assert.throws(() => game.setZone('missing'));
});
