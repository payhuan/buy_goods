/* Four-page classroom shopping activity. */
const products = MARKET_PRODUCTS;
const game = createMarketGame(products);
const goods = document.querySelector('#goods');
const cards = new Map();
document.querySelector('#entrance-background').style.backgroundImage = `url("${marketAssetUrl('assets/images/entrance-background.jpg')}")`;
let audio, muted = true, scene, sceneRequest = 0, pageTimer;

function sound(correct) {
  if (muted) return;
  try {
    audio ??= new (window.AudioContext || window.webkitAudioContext)(); audio.resume();
    (correct ? [660, 880, 1100] : [170]).forEach((frequency, index) => {
      const oscillator = audio.createOscillator(), gain = audio.createGain(), start = audio.currentTime + index * .09;
      oscillator.type = 'sine'; oscillator.frequency.value = frequency;
      gain.gain.setValueAtTime(0, start); gain.gain.linearRampToValueAtTime(.055, start + .015);
      gain.gain.exponentialRampToValueAtTime(.001, start + .16);
      oscillator.connect(gain); gain.connect(audio.destination); oscillator.start(start); oscillator.stop(start + .17);
    });
  } catch (_) { /* Sound availability never prevents choosing or turning pages. */ }
}
function refreshScore() {
  document.querySelector('#star-count').textContent = game.stars;
  document.querySelector('#score').setAttribute('aria-label', `已获得${game.stars}颗星星`);
  document.querySelector('#area-progress').textContent = `已找到 ${game.foundIn(game.zone)} / 3`;
}
function award(origin) {
  refreshScore();
  const score = document.querySelector('#score'); score.classList.remove('pop'); void score.offsetWidth; score.classList.add('pop');
  if (matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  const a = origin.getBoundingClientRect(), b = score.getBoundingClientRect();
  const star = document.createElement('span'); star.className = 'flying-star'; star.textContent = '★'; star.setAttribute('aria-hidden', 'true');
  star.style.left = `${a.left + a.width / 2 - 20}px`; star.style.top = `${a.top + a.height / 2 - 20}px`; document.body.append(star);
  const flight = star.animate([{ transform: 'translate(0,0) scale(.5)', opacity: 1 },
    { transform: 'translate(0,0) scale(1.65)', opacity: 1, offset: .25 },
    { transform: `translate(${b.left + b.width / 2 - a.left - a.width / 2}px,${b.top + b.height / 2 - a.top - a.height / 2}px) scale(1.1)`, opacity: 1 }],
    { duration: 1600, easing: 'cubic-bezier(.3,.1,.35,1)' }); flight.onfinish = () => star.remove();
}
function layoutGoods(entries) {
  for (const entry of entries) {
    const card = cards.get(entry.id); if (!card) continue;
    Object.assign(card.choose.style, { left: `${entry.left - 6}px`, top: `${entry.top - 6}px`, width: `${entry.width + 12}px`, height: `${entry.height + 12}px` });
    Object.assign(card.label.style, { left: `${entry.label.x}px`, top: `${entry.label.y}px` });
    Object.assign(card.badge.style, { left: `${entry.left + entry.width + 5}px`, top: `${entry.top + 10}px` });
  }
}
function renderGoods() {
  goods.replaceChildren(); cards.clear();
  const order = game.zone === '百货区' ? ['batteries', 'pencils', 'toothpaste', 'mugs', 'brushes', 'rolls'] : ['apples', 'candy', 'chips', 'eggs', 'water', 'yogurt'];
  for (const [index, id] of order.entries()) {
    const item = products.find(p => p.id === id);
    const choose = document.createElement('button'); choose.className = 'product-hit fallback-product'; choose.dataset.id = id;
    choose.setAttribute('aria-label', `选择${item.name}`); choose.disabled = game.hasStar(id);
    choose.innerHTML = `<img src="${marketAssetUrl(`assets/images/${id}.png`)}" alt="${item.name}" draggable="false">`;
    Object.assign(choose.style, { left: `${17 + index % 3 * 24}%`, top: `${index < 3 ? 23 : 55}%`, width: '20%', height: '29%' });
    const label = document.createElement('div'); label.className = 'product-label'; label.dataset.id = id;
    label.innerHTML = `<div class="label-name">${item.name}</div><div class="label-price">¥${item.price.toFixed(2)}</div>`;
    label.style.left = `${27 + index % 3 * 24}%`; label.style.top = index < 3 ? 'calc(52.72% + 20px)' : '86%';
    const badge = document.createElement('span'); badge.className = 'earned-star'; badge.textContent = '★';
    badge.setAttribute('aria-label', `${item.name}已获得星星`); badge.hidden = !game.hasStar(id);
    badge.style.left = `${35 + index % 3 * 24}%`; badge.style.top = `${index < 3 ? 26 : 58}%`;
    choose.addEventListener('click', () => {
      const result = game.select(id);
      if (result === 'correct') {
        choose.disabled = true; badge.hidden = false; sound(true); award(choose);
        if (scene && document.body.dataset.renderer === '3d') scene.celebrate(id);
        else choose.querySelector('img').animate([{transform:'scale(1)'},{transform:'scale(1.16)'},{transform:'scale(1)'}],{duration:800});
        if (game.foundIn(game.zone) === 3) {
          const completedPage = game.page;
          clearTimeout(pageTimer);
          pageTimer = setTimeout(() => { if (game.page === completedPage) { game.next(); renderPage(); } }, 2300);
        }
      }
      else if (result === 'wrong') {
        if (scene && document.body.dataset.renderer === '3d') scene.shake(id);
        else { const image = choose.querySelector('img'); image.classList.remove('shake'); void image.offsetWidth; image.classList.add('shake'); }
        sound(false);
      }
    });
    goods.append(choose, label, badge); cards.set(id, { choose, label, badge });
  }
}
async function renderPage() {
  const token = ++sceneRequest, page = game.page, inArea = ['百货区', '食品区'].includes(page);
  clearTimeout(pageTimer);
  document.body.dataset.page = page; document.body.dataset.renderer = 'fallback';
  document.querySelector('#entrance').hidden = page !== '入口'; document.querySelector('#ending').hidden = page !== '结束';
  document.querySelector('.hud').hidden = !inArea; document.querySelector('#area-sign').hidden = !inArea;
  document.querySelector('.scene-nav').hidden = !inArea; goods.hidden = !inArea;
  document.querySelector('#fallback-rack').hidden = !inArea; document.querySelector('#fallback-aisle').hidden = inArea;
  const title = document.querySelector('#zone-title');
  const syllables = game.zone === '百货区' ? [['百', 'bǎi'], ['货', 'huò'], ['区', 'qū']] : [['食', 'shí'], ['品', 'pǐn'], ['区', 'qū']];
  title.setAttribute('aria-label', game.zone);
  title.innerHTML = syllables.map(([character, pinyin]) => `<span class="zone-syllable"><span class="zone-pinyin" aria-hidden="true">${pinyin}</span><span>${character}</span></span>`).join('');
  refreshScore();
  if (inArea) renderGoods(); else { goods.replaceChildren(); cards.clear(); }
  if (page === '结束') {
    document.querySelector('#ending-title').textContent = game.stars === 6 ? '通关啦！' : '逛完啦！';
    document.querySelector('#ending-score').textContent = `你收集了 ${game.stars} 颗星星`;
    document.querySelector('.ending-stars').innerHTML = Array.from({ length: 6 }, (_, i) => `<span class="${i < game.stars ? '' : 'empty'}" aria-hidden="true">★</span>`).join('');
    document.querySelector('.ending-stars').setAttribute('aria-label', `获得${game.stars}颗星星`);
  }
  if (!scene) return;
  try {
    const ready = await scene.setPage(page);
    if (token !== sceneRequest || !ready) return;
    document.body.dataset.renderer = '3d';
    document.querySelector('#fallback-rack').hidden = true; document.querySelector('#fallback-aisle').hidden = true;
    for (const { choose } of cards.values()) { choose.classList.remove('fallback-product'); choose.querySelector('img').hidden = true; }
  } catch (_) { /* Continuous shelf fallback remains usable if WebGL or asset loading fails. */ }
}
for (const [selector, action] of [['#enter', () => game.enter()], ['#next-page', () => game.next()], ['#previous-page', () => game.back()]]) {
  document.querySelector(selector).addEventListener('click', () => { action(); renderPage(); });
}
document.querySelector('#fullscreen').addEventListener('click', async () => {
  try { if (document.fullscreenElement) await document.exitFullscreen(); else await document.documentElement.requestFullscreen(); } catch (_) { }
});
renderPage();
(async () => {
  try { const module = await import('./scene.js?v=20261016-aligned-labels'); scene = await module.createMarketScene(document.querySelector('#scene-stage'), products, layoutGoods); renderPage(); }
  catch (_) { /* Local file opening also supports the four pages and shelf images. */ }
})();




